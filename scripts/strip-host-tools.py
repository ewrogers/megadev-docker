#!/usr/bin/env python3
"""Remove host debug symbols while preserving every m68k target object."""
from pathlib import Path
import struct
import subprocess


seen = set()
for path in Path("/opt/m68k").rglob("*"):
    if not path.is_file() or path.resolve() in seen:
        continue
    seen.add(path.resolve())
    with path.open("rb") as stream:
        header = stream.read(20)
    if len(header) < 20 or header[:4] != b"\x7fELF":
        continue
    byte_order = "<" if header[5] == 1 else ">"
    kind, machine = struct.unpack(byte_order + "HH", header[16:20])
    # ELF executable/shared object, hosted on AMD64 or AArch64. Target m68k
    # code has machine=4 and is deliberately left untouched.
    if kind in (2, 3) and machine in (62, 183):
        subprocess.run(["strip", "--strip-debug", str(path)], check=True)
