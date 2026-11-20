"""Extract legacy firmware source packages into a private staging directory."""

import bz2
import gzip
import logging
import os
import re
import shutil
import stat
import struct
import tempfile
import unicodedata
import zipfile
import zlib
from pathlib import Path

logger = logging.getLogger(__name__)
MAX_PACKAGE_BYTES = 128 * 1024 * 1024
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_EXTRACTED_BYTES = 256 * 1024 * 1024
MAX_MEMBERS = 4096
CPIO_MAGIC = (b"070701", b"070702")
WINDOWS_DEVICES = re.compile(
    r"(?:con|conin\$|conout\$|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])", re.I
)


class FirmwareArchiveError(ValueError):
    """An archive failed the format or extraction policy."""


def member_parts(name):
    while name.startswith("./"):
        name = name[2:]
    parts = name.split("/")
    if (
        not 1 <= len(name) <= 400
        or not 1 <= len(parts) <= 24
        or any(char in name for char in '\\:<>"|?*')
        or any(
            not part
            or part in {".", ".."}
            or not part.isprintable()
            or part != part.strip()
            or part.endswith(".")
            or len(part.encode("utf-8")) > 200
            or WINDOWS_DEVICES.fullmatch(part.split(".", 1)[0])
            for part in parts
        )
    ):
        raise FirmwareArchiveError("Archive contains an unsafe member path.")
    return parts


class StagedArchive:
    def __init__(
        self, root, *, max_members=None, max_member_bytes=None, max_expanded_bytes=None
    ):
        self.root = root
        self.max_members = MAX_MEMBERS if max_members is None else max_members
        self.max_member_bytes = (
            MAX_MEMBER_BYTES if max_member_bytes is None else max_member_bytes
        )
        self.max_expanded_bytes = (
            MAX_EXTRACTED_BYTES if max_expanded_bytes is None else max_expanded_bytes
        )
        self.members = {}
        self.total = 0
        self.count = 0

    def add(self, name, size, directory):
        self.count += 1
        if self.count > self.max_members or not 0 <= size <= self.max_member_bytes:
            raise FirmwareArchiveError("Archive member limits exceeded.")
        self.total += size
        if self.total > self.max_expanded_bytes:
            raise FirmwareArchiveError("Archive exceeds its expanded byte limit.")
        if directory and size:
            raise FirmwareArchiveError("Archive directories must be empty entries.")
        if directory and name in {".", "./"}:
            return self.root
        parts = member_parts(name[:-1] if directory and name.endswith("/") else name)
        for index in range(1, len(parts) + 1):
            spelling = "/".join(parts[:index])
            key = unicodedata.normalize("NFC", spelling).casefold()
            is_directory = directory or index < len(parts)
            prior = self.members.get(key)
            if prior and (prior != (spelling, is_directory) or not is_directory):
                raise FirmwareArchiveError("Archive contains conflicting member paths.")
            self.members[key] = (spelling, is_directory)
        path = self.root.joinpath(*parts)
        if directory:
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
        return path


def read_exact(source, size):
    result = source.read(size)
    if len(result) != size:
        raise FirmwareArchiveError("Archive is truncated.")
    return result


def copy_member(source, destination, size, *, checksum=None):
    actual = 0
    with destination.open("xb") as output:
        remaining = size
        while remaining:
            chunk = read_exact(source, min(remaining, 65536))
            output.write(chunk)
            remaining -= len(chunk)
            if checksum is not None:
                actual = (actual + sum(chunk)) & 0xFFFFFFFF
    if checksum is not None and actual != checksum:
        raise FirmwareArchiveError("CPIO member checksum failed.")


def read_zip(source, stage, *, compression=None):
    with zipfile.ZipFile(source) as package:
        infos = package.infolist()
        if len(infos) > stage.max_members:
            raise FirmwareArchiveError("ZIP has too many members.")
        for info in infos:
            if compression is not None and info.compress_type not in compression:
                raise FirmwareArchiveError(
                    "ZIP uses an unsupported compression method."
                )
            directory = info.is_dir()
            unix_type = stat.S_IFMT(info.external_attr >> 16)
            if (
                info.flag_bits & 1
                or info.filename != info.orig_filename
                or unix_type not in {0, stat.S_IFDIR if directory else stat.S_IFREG}
            ):
                raise FirmwareArchiveError(
                    "ZIP contains an encrypted, linked or special member."
                )
            destination = stage.add(info.filename, info.file_size, directory)
            if not directory:
                with package.open(info) as member:
                    copy_member(member, destination, info.file_size)
                    if member.read(1):
                        raise FirmwareArchiveError(
                            "ZIP member exceeds its declared size."
                        )


def read_cpio(source, stage):
    for _ in range(MAX_MEMBERS + 1):
        header = read_exact(source, 110)
        if header[:6] not in CPIO_MAGIC or not re.fullmatch(
            rb"[A-Fa-f0-9]{104}", header[6:]
        ):
            raise FirmwareArchiveError("Expected a newc or CRC CPIO header.")
        fields = [int(header[i : i + 8], 16) for i in range(6, 110, 8)]
        mode, links, size, name_length, crc = (fields[i] for i in (1, 4, 6, 11, 12))
        if not 2 <= name_length <= 4096:
            raise FirmwareArchiveError("Invalid CPIO member name length.")
        raw_name = read_exact(source, name_length)
        if not raw_name.endswith(b"\0") or b"\0" in raw_name.rstrip(b"\0"):
            raise FirmwareArchiveError("Invalid CPIO filename terminator.")
        name = raw_name.rstrip(b"\0").decode("utf-8")
        read_exact(source, -(110 + name_length) % 4)
        if name == "TRAILER!!!" and size == 0:
            padding = source.read(4097)
            if len(padding) > 4096 or any(padding):
                raise FirmwareArchiveError("Unexpected data after the CPIO trailer.")
            return
        directory = stat.S_ISDIR(mode)
        if not directory and (not stat.S_ISREG(mode) or links != 1):
            raise FirmwareArchiveError("CPIO links and special files are unsupported.")
        destination = stage.add(name, size, directory)
        if not directory:
            copy_member(
                source,
                destination,
                size,
                checksum=crc if header[:6] == b"070702" else None,
            )
        read_exact(source, -size % 4)
    raise FirmwareArchiveError("CPIO has too many members or no trailer.")


def skip_rpm_header(source):
    header = read_exact(source, 16)
    if header[:8] != b"\x8e\xad\xe8\x01\0\0\0\0":
        raise FirmwareArchiveError("Unsupported RPM header.")
    count, size = struct.unpack(">II", header[8:])
    if count > 16384 or size > 8 * 1024 * 1024:
        raise FirmwareArchiveError("RPM metadata exceeds its size limit.")
    source.seek(count * 16 + size, os.SEEK_CUR)


def read_rpm(source, stage):
    if read_exact(source, 96)[:4] != b"\xed\xab\xee\xdb":
        raise FirmwareArchiveError("Expected a version 4 RPM package.")
    skip_rpm_header(source)
    source.seek(-source.tell() % 8, os.SEEK_CUR)
    skip_rpm_header(source)
    offset = source.tell()
    magic = read_exact(source, 6)
    source.seek(offset)
    if magic in CPIO_MAGIC:
        read_cpio(source, stage)
    elif magic.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=source) as payload:
            read_cpio(payload, stage)
    elif magic.startswith(b"BZh"):
        with bz2.BZ2File(source) as payload:
            read_cpio(payload, stage)
    else:
        raise FirmwareArchiveError(
            "Use RPM with a gzip, bzip2 or uncompressed CPIO payload."
        )
    nested = list(stage.root.glob("*.cpio"))
    if len(nested) > 1:
        raise FirmwareArchiveError(
            "Multiple embedded CPIO archives require manual review."
        )
    if nested:
        with nested[0].open("rb") as payload:
            read_cpio(payload, stage)


def extract(path, extract_dir, reader):
    destination = Path(extract_dir)
    try:
        if os.path.lexists(destination):
            metadata = destination.lstat()
            reparse = (
                getattr(metadata, "st_file_attributes", 0)
                & stat.FILE_ATTRIBUTE_REPARSE_POINT
            )
            if (
                reparse
                or not stat.S_ISDIR(metadata.st_mode)
                or any(destination.iterdir())
            ):
                raise FirmwareArchiveError(
                    "Use an empty, local destination for extraction."
                )
        with Path(path).open("rb") as source:
            metadata = os.fstat(source.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or not 1 <= metadata.st_size <= MAX_PACKAGE_BYTES
            ):
                raise FirmwareArchiveError("Use a regular archive file up to 128 MiB.")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(
                prefix="firmware-stage-", dir=destination.parent
            ) as scratch:
                contents = Path(scratch) / "contents"
                contents.mkdir()
                reader(source, StagedArchive(contents))
                if destination.exists():
                    # rmdir also refuses to clobber concurrent output.
                    destination.rmdir()
                contents.rename(destination)
        return os.fspath(extract_dir)
    except (
        OSError,
        ValueError,
        EOFError,
        RuntimeError,
        NotImplementedError,
        zipfile.BadZipFile,
        zlib.error,
    ) as exc:
        logger.error(
            "Firmware archive rejected (%s): %s", type(exc).__name__, str(exc)[:200]
        )
        return None


def extract_rpm(rpm_path, extract_dir):
    return extract(rpm_path, extract_dir, read_rpm)


def extract_cpio(cpio_path, extract_dir):
    return extract(cpio_path, extract_dir, read_cpio)


def extract_img(img_path, extract_dir):
    # This legacy convention refers to ZIP-wrapped sources only.
    return extract(img_path, extract_dir, read_zip)


def extract_zipped_firmware(zip_path, extract_dir):
    return extract(zip_path, extract_dir, read_zip)


def find_source_files(directory, extensions=(".cs", ".cpp", ".h", ".py")):
    return sorted(
        str(path)
        for path in Path(directory).rglob("*")
        if path.suffix.lower() in extensions
        and path.is_file()
        and not path.is_symlink()
    )


def process_firmware_package(firmware_path):
    readers = {".rpm": read_rpm, ".cpio": read_cpio, ".img": read_zip, ".zip": read_zip}
    reader = readers.get(Path(firmware_path).suffix.lower())
    if reader is None:
        logger.error("Choose a supported firmware source archive.")
        return None
    folder = Path(tempfile.mkdtemp(prefix="firmware-source-"))
    extracted = extract(firmware_path, folder / "contents", reader)
    sources = find_source_files(extracted) if extracted else []
    if not sources:
        shutil.rmtree(folder)
        return None
    return sources
