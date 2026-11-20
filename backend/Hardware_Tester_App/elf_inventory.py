"""Bounded static ELF inspection of load headers and dynamic strings."""

import re
import struct
from typing import NamedTuple

MACHINES = {
    3: "x86",
    8: "mips",
    20: "ppc",
    21: "ppc64",
    40: "arm",
    62: "x86_64",
    183: "aarch64",
    243: "riscv",
}
PT_LOAD, PT_DYNAMIC, PT_INTERP = 1, 2, 3
DT_NULL, DT_NEEDED, DT_STRTAB, DT_STRSZ, DT_SONAME = 0, 1, 5, 10, 14


class ElfError(ValueError):
    """ELF structures needed for inventory are missing or unsupported."""


class Segment(NamedTuple):
    kind: int
    offset: int
    address: int
    size: int


def bounded_string(data, start, limit):
    if not 0 <= start < limit <= len(data):
        raise ElfError("Invalid ELF string location.")
    end = data.find(b"\0", start, min(start + 257, limit))
    if end < 0 or not re.fullmatch(rb"[A-Za-z0-9_.$/+\-]+", data[start:end]):
        raise ElfError("Invalid or unsupported ELF name.")
    return data[start:end].decode("ascii")


def dynamic_names(data, segments, dynamic, encoding, wide):
    layout = struct.Struct(encoding + ("qQ" if wide else "iI"))
    if dynamic.size % layout.size or dynamic.size > 4096 * layout.size:
        raise ElfError("ELF dynamic table exceeds supported bounds.")
    tags = {}
    for tag, value in layout.iter_unpack(
        data[dynamic.offset : dynamic.offset + dynamic.size]
    ):
        if tag == DT_NULL:
            break
        if tag in (DT_NEEDED, DT_STRTAB, DT_STRSZ, DT_SONAME):
            tags.setdefault(tag, []).append(value)
    else:
        raise ElfError("ELF dynamic table is unterminated.")

    needed = tags.get(DT_NEEDED, [])
    soname = tags.get(DT_SONAME, [])
    if not needed and not soname:
        return [], None
    if (
        len(needed) > 128
        or len(soname) > 1
        or any(len(tags.get(key, [])) != 1 for key in (DT_STRTAB, DT_STRSZ))
    ):
        raise ElfError("ELF dynamic string metadata is incomplete or ambiguous.")
    address, size = tags[DT_STRTAB][0], tags[DT_STRSZ][0]
    offsets = {
        segment.offset + address - segment.address
        for segment in segments
        if segment.kind == PT_LOAD
        and segment.address <= address
        and address + size <= segment.address + segment.size
    }
    if len(offsets) != 1 or not size:
        raise ElfError("ELF string table is outside a file-backed load segment.")
    offset = offsets.pop()
    libraries = sorted(
        {bounded_string(data, offset + item, offset + size) for item in needed}
    )
    return libraries, (
        bounded_string(data, offset + soname[0], offset + size) if soname else None
    )


def inspect_elf(data):
    if (
        len(data) < 16
        or data[:4] != b"\x7fELF"
        or data[4] not in (1, 2)
        or data[5] not in (1, 2)
        or data[6] != 1
    ):
        raise ElfError("Unsupported or truncated ELF identification.")
    wide = data[4] == 2
    encoding = "<" if data[5] == 1 else ">"
    header = struct.Struct(encoding + ("HHIQQQIHHHHHH" if wide else "HHIIIIIHHHHHH"))
    program = struct.Struct(encoding + ("IIQQQQQQ" if wide else "IIIIIIII"))
    if len(data) < 16 + header.size:
        raise ElfError("Truncated ELF header.")
    kind, machine, version, _, offset, _, flags, header_size, entry_size, count, *_ = (
        header.unpack_from(data, 16)
    )
    if (
        version != 1
        or header_size < 16 + header.size
        or header_size > len(data)
        or count > 256
    ):
        raise ElfError("ELF header or program count exceeds supported bounds.")
    if count and (
        entry_size != program.size
        or offset < header_size
        or offset + count * entry_size > len(data)
    ):
        raise ElfError("ELF program headers are outside the file.")
    segments = []
    for i in range(count):
        row = program.unpack_from(data, offset + i * entry_size)
        file_offset, address, size = (
            (row[2], row[3], row[5]) if wide else (row[1], row[2], row[4])
        )
        if row[0] in (PT_LOAD, PT_INTERP, PT_DYNAMIC):
            if file_offset + size > len(data):
                raise ElfError("ELF segment is outside the file.")
            segments.append(Segment(row[0], file_offset, address, size))

    interpreters = [segment for segment in segments if segment.kind == PT_INTERP]
    dynamics = [segment for segment in segments if segment.kind == PT_DYNAMIC]
    if len(interpreters) > 1 or len(dynamics) > 1:
        raise ElfError("ELF has ambiguous loading metadata.")
    interpreter = None
    if interpreters:
        segment = interpreters[0]
        interpreter = bounded_string(
            data, segment.offset, segment.offset + segment.size
        )
    needed, soname = (
        dynamic_names(data, segments, dynamics[0], encoding, wide)
        if dynamics
        else ([], None)
    )
    loader = (interpreter or "").split("/")[-1]
    libc = None
    if loader.startswith("ld-musl-") or any(
        name.startswith("libc.musl-") for name in needed
    ):
        libc = "musl"
    elif (
        loader.startswith(("ld-linux", "ld64.so."))
        or "libc.so.6" in needed
        or soname == "libc.so.6"
    ):
        libc = "glibc"
    return {
        "architecture": MACHINES.get(machine),
        "machine": machine,
        "type": {1: "relocatable", 2: "executable", 3: "shared-or-PIE", 4: "core"}.get(
            kind, "unknown"
        ),
        "bits": 64 if wide else 32,
        "endianness": "little" if encoding == "<" else "big",
        "osAbi": data[7],
        "abiVersion": data[8],
        "flags": flags,
        "interpreter": interpreter,
        "libc": libc,
        "needed": needed,
        "soname": soname,
    }
