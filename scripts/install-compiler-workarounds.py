#!/usr/bin/env python3
"""Disable GCC 16.2's incorrect M68000 shared-pointer auto-increment fold."""
from pathlib import Path
import subprocess


def install():
    compiler = "/opt/m68k/bin/m68k-elf-gcc"
    specs = subprocess.check_output([compiler, "-dumpspecs"], text=True)
    marker = "*self_spec:\n\n\n"
    if specs.count(marker) != 1:
        raise RuntimeError("GCC self specs changed; review the M68000 workaround")
    # A driver default covers ordinary compilation and LTO, including projects
    # that replace EXTRA_FLAGS. Explicit -fauto-inc-dec remains available for
    # reproducing the compiler defect in the regression test.
    library = Path(subprocess.check_output([compiler, "-print-libgcc-file-name"], text=True).strip())
    target = library.parent / "specs"
    if target.exists():
        raise RuntimeError("Compiler already has custom specs; review before replacing them")
    policy = (
        "%{mcpu=*:%{!mcpu=68000:%eThis toolchain targets the Mega Drive / Sega CD 68000 CPU}} "
        "%{march=*:%{!march=68000:%eThis toolchain targets the Mega Drive / Sega CD 68000 architecture}} "
        "%{m68020-40|m68020-60|m68881|m68851:%eThe Mega Drive / Sega CD has a 68000 without an FPU or MMU} "
        "%{!mcpu=*:-mcpu=68000} %{!std=*:-std=gnu17} %{!fauto-inc-dec:-fno-auto-inc-dec}"
    )
    target.write_text(specs.replace(marker, "*self_spec:\n" + policy + "\n\n"))
    # GCC and command-line assembly use two installed paths to GAS. Route both
    # through the same 68000 default and CPU-option check.
    assembler = Path("/opt/m68k/bin/m68k-elf-as")
    assembler.rename(assembler.with_name("m68k-elf-as.real"))
    assembler.write_bytes(Path(__file__).with_name("m68000-as.sh").read_bytes())
    assembler.chmod(0o755)
    backend = Path("/opt/m68k/m68k-elf/bin/as")
    backend.unlink()
    backend.symlink_to("../../bin/m68k-elf-as")


if __name__ == "__main__":
    install()
