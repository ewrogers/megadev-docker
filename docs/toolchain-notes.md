# Toolchain decisions and sources

These notes explain the container's compatibility choices. Megadev is a separate
Sega CD development kit, not an SGDK extension.

## Megadev build requirements

The reviewed upstream revision is
`7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef`, also upstream HEAD when checked on
October 15, 2026. Its build rules use GNU Make, an M68000 C compiler and assembler,
GNU binutils, and `mkisofs`. Upstream's Debian setup supplies the latter through
`genisoimage`; it also installs `xxd`. Megadev compiles separate main-CPU and
sub-CPU modules and combines its boot block with an ISO9660 filesystem.
See [upstream build rules](https://github.com/drojaazu/megadev/blob/7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef/megadev.make)
and [Debian dependencies](https://github.com/drojaazu/megadev/blob/7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef/.devcontainer/Dockerfile).

Use GNU C17 explicitly. This retains the GNU extensions used by the kit without
depending on GCC's changing default language version. Megadev already adds
`-m68000`, `-fno-builtin`, and assembler options; do not replace its entire
`CC_FLAGS` variable just to select the dialect. Its modules link directly with
`ld -nostdlib`, and upstream does not provide a general C standard library.
See [the C development guide](https://github.com/drojaazu/megadev/blob/7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef/docs/dev_in_c.md)
and [GCC language standards](https://gcc.gnu.org/onlinedocs/gcc/Standards.html).

## Original 68000 safeguards

Both console CPUs require original-68000 machine code. GCC documents
`-m68000` as equivalent to `-march=68000`; later M680x0 and ColdFire targets
are not substitutes. Configure GCC and its runtime helpers for the 68000,
reject incompatible compiler options, and also guard direct assembler calls.
Tests should reject a 68020-only instruction and an FPU instruction, and execute
a far-branch fixture to check that assembler relaxation remains 68000-safe.
See [GCC target options](https://gcc.gnu.org/onlinedocs/gcc/M680x0-Options.html).

Checking project C files is insufficient: any linked runtime library must also
target the 68000. A compiler configured with `--with-cpu=m68000` and
`--disable-multilib` builds one suitable `libgcc`. Megadev's direct `ld` commands
do not automatically add it. If generated code needs helpers such as long
multiplication or division, select this compiler's `-print-libgcc-file-name`
result explicitly and test the linked arithmetic on an M68000 emulator.
Do not substitute a distribution's unverified default `libgcc`.

Retain the GCC 16.2 byte-copy workaround from our SGDK container:
`-fno-auto-inc-dec`. Our executed regression reproduced corrupted volatile
byte copies when the optimization was enabled and correct copies when disabled.
This is a locally reproduced defect, not a claim that every auto-increment
instruction is unsafe. GCC describes the pass as folding pointer increments
into memory accesses and enables it from `-O1` on supported targets.
See [the regression and negative control](https://github.com/ewrogers/sgdk-docker/blob/584b9a6/scripts/m68k_regression.py),
[installed compiler policy](https://github.com/ewrogers/sgdk-docker/blob/584b9a6/scripts/install-compiler-workarounds.py),
and [GCC optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html).

## Source provenance and validation limits

Megadev carries an [MIT license](https://github.com/drojaazu/megadev/blob/7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef/LICENSE).
Preserve it with the installed source. Its
[security block source](https://github.com/drojaazu/megadev/blob/7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef/lib/security.c)
contains upstream region-specific boot bytes; preserve their provenance instead
of presenting them as newly authored code. This block is distinct from an
emulator BIOS. Builds need no external BIOS; emulator users supply their own.
Do not package BIOS files or commercial games in the image or repository.

GCC 16.2.0 and binutils 2.47 are the maintained releases selected for this
toolchain, checked against the [GCC release list](https://gcc.gnu.org/releases.html)
and [binutils release page](https://www.gnu.org/software/binutils/).
Keep exact revisions and archive checksums in the source lock file. Include
GNU tool source archives, license notices, and build recipes with the image.

Fresh upstream example builds, cross-architecture payload comparisons and
executed compiler regressions establish specific compatibility evidence. They
do not prove all Megadev APIs or real hardware behavior. Disc-image metadata can
contain timestamps, so compare boot and file payloads separately unless the
entire ISO build has deliberately been made reproducible.
