import gzip
import stat
import struct
import zipfile

import pytest

from Hardware_Tester_App.utils import firmware_utils as firmware


@pytest.mark.parametrize(
    "unsafe", ["../escape.txt", "/absolute.cpp", "C:/root.h", "a\\b.cpp", "NUL.txt"]
)
def test_zip_rejects_unsafe_paths_without_publishing(tmp_path, unsafe):
    source = tmp_path / "source.zip"
    destination = tmp_path / "extract"
    destination.mkdir()
    with zipfile.ZipFile(source, "w") as package:
        package.writestr("directory/controller.cpp", "int main() {}")
        package.writestr(unsafe.replace("\\", "/"), "invalid")
    if "\\" in unsafe:
        # A Windows ZipInfo writer normalizes separators before serialization.
        source.write_bytes(source.read_bytes().replace(b"a/b.cpp", b"a\\b.cpp"))
    assert firmware.extract_zipped_firmware(source, destination) is None
    assert list(destination.iterdir()) == []
    assert not (tmp_path / "escape.txt").exists()


def test_zip_rejects_link_and_case_collision(tmp_path):
    source = tmp_path / "source.zip"
    destination = tmp_path / "extract"
    with zipfile.ZipFile(source, "w") as package:
        link = zipfile.ZipInfo("link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        package.writestr(link, "../outside")
    assert firmware.extract_zipped_firmware(source, destination) is None
    with zipfile.ZipFile(source, "w") as package:
        package.writestr("A/first.cpp", "a")
        package.writestr("a/second.cpp", "b")
    assert firmware.extract_zipped_firmware(source, destination) is None
    assert not destination.exists()


def test_legacy_zip_wrapped_img_keeps_nested_source_and_refuses_nonempty_destination(
    tmp_path,
):
    source = tmp_path / "legacy.img"
    destination = tmp_path / "extract"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("app/Controller.cpp", "int main() {}")
    assert firmware.extract_img(source, destination) == str(destination)
    assert (destination / "app/Controller.cpp").read_text() == "int main() {}"
    assert firmware.extract_img(source, destination) is None
    assert firmware.find_source_files(destination) == [
        str(destination / "app/Controller.cpp")
    ]


def cpio_member(name, data=b"", mode=stat.S_IFREG | 0o644, links=1):
    filename = name.encode() + b"\0"
    fields = [0, mode, 0, 0, links, 0, len(data), 0, 0, 0, 0, len(filename), sum(data)]
    metadata = (
        b"070702" + "".join(f"{value:08x}" for value in fields).encode() + filename
    )
    return metadata + b"\0" * (-len(metadata) % 4) + data + b"\0" * (-len(data) % 4)


def test_rpm_gzip_cpio_support_and_size_gate(tmp_path, monkeypatch):
    # The fixture supplies the RPM framing and a CRC CPIO source member.
    source = tmp_path / "controller.rpm"
    lead = b"\xed\xab\xee\xdb" + bytes(92)
    header = b"\x8e\xad\xe8\x01" + bytes(4) + struct.pack(">II", 0, 0)
    source.write_bytes(
        lead
        + header
        + header
        + gzip.compress(
            cpio_member("./src/valve.cpp", b"int valve;") + cpio_member("TRAILER!!!")
        )
    )
    destination = tmp_path / "extract"
    assert firmware.extract_rpm(source, destination) == str(destination)
    assert (destination / "src/valve.cpp").read_bytes() == b"int valve;"
    monkeypatch.setattr(firmware, "MAX_MEMBER_BYTES", 4)
    assert firmware.extract_rpm(source, tmp_path / "over-limit") is None
    assert not (tmp_path / "over-limit").exists()


def test_cpio_rejects_hardlinks_and_raw_disk_is_not_an_archive(tmp_path):
    source = tmp_path / "linked.cpio"
    source.write_bytes(cpio_member("linked.cpp", links=2) + cpio_member("TRAILER!!!"))
    assert firmware.extract_cpio(source, tmp_path / "extract") is None
    disk = tmp_path / "sd.img"
    disk.write_bytes(bytes(512))
    assert firmware.extract_img(disk, tmp_path / "raw") is None
