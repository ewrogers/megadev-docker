# Testing and publishing

## Toolchain inputs

| Component | Source |
|---|---|
| Megadev | `7a7246c14b845ad2f1bd3c7d73afb04cf67d83ef` |
| GCC | 16.2.0, bare-metal `m68k-elf`, C only |
| GNU binutils | 2.47 |
| GDB | 18.1 |
| Container | Debian trixie, locked multi-platform base digest |

The source URLs and SHA-256 checksums are in `sources.lock.json` and
`debugger.lock.json`. The downloader verifies every archive before installing
it. Debian packages come from the base distribution's repositories; their
versions can change between builds. This is not a promise of bit-identical
container images or complete discs.

The image contains no SGDK, Java runtime, external BIOS or commercial games.
Megadev's upstream sources and examples are retained, including their notices.
Its bundled regional security blocks are upstream material, distinct from an
external BIOS. See [source and licensing notes](toolchain-notes.md).

## Compiler safeguards

Both the Mega Drive main CPU and Sega CD sub CPU use base-68000 instructions.
GCC and libgcc are built with `--with-cpu=m68000 --disable-multilib`. Compiler
specs and both assembler entry points enforce that target and reject later-CPU,
FPU and MMU options. Far branches must expand to valid 68000 instructions.

GNU C17 is the default; an explicit `-std=` still works. This preserves
Megadev's existing flags rather than replacing `CC_FLAGS`. The container does
not supply a general C library. Megadev links with `ld -nostdlib`; if your
code needs compiler arithmetic helpers, explicitly add the compiler's libgcc
archive to the relevant link rule (`m68k-elf-gcc -print-libgcc-file-name`).

The compiler defaults to `-fno-auto-inc-dec`, carrying the GCC 16.2 byte-copy
workaround used in SGDK Docker. The regression executes the emitted machine
code, then explicitly enables `-fauto-inc-dec` as a negative control that must
reproduce the defect. Do not enable that optimization for game builds.

`-fno-strict-aliasing` is also a driver default for ordinary compilation and LTO,
matching SGDK Docker's compatibility policy for low-level mixed-width buffers.
An explicit `-fstrict-aliasing` remains available for audited code and diagnosis.
This is not a fix for a GCC optimizer bug: incompatible typed-pointer aliasing
violates the normal C rules. Prefer character access, explicit packing or another
valid representation in new code. The flag does not fix alignment, bounds, data
races, MMIO volatility or other undefined behavior.

These are correctness guards, not a security sandbox or proof of arbitrary
code. Handwritten `.word` instructions, imported binaries, CPU directives and
deliberately replaced compiler specs still require review. Hardware registers,
CPU synchronization and timing must also be tested in an emulator or hardware.

## Run the tests

```sh
python3 -m unittest discover -s tests -v
python3 -m venv build/test-venv
build/test-venv/bin/pip install -r tests/requirements.txt
docker buildx build --platform linux/arm64 --load -t megadev-test:arm64 .
build/test-venv/bin/python scripts/test-image.py megadev-test:arm64 \
  --platform linux/arm64 --output build/test-arm64
```

Repeat the build and image test with `amd64`, using a separate output folder.
Then compare reports:

```sh
python3 scripts/compare-reports.py build/test-arm64/report.json build/test-amd64/report.json
```

Each output folder must be new. Logs, generated discs and reports stay in
ignored `build/`. Unicorn is a test-only dependency; it is not in the image.

The suite builds fresh copies of all seven upstream projects, including the
cartridge example, and repeats the C template for US/NTSC, JP/NTSC and EU/PAL.
It checks regional boot signatures, ISO9660 files against the compiled modules,
command failures,
non-destructive project creation, source access, GDB symbols and a project
folder containing spaces. The host UID/GID is used for generated files.

Compiler regressions reject invalid CPU/FPU instructions and options, execute
far branches and libgcc arithmetic as a 68000, and check the byte-copy defect
with LTO. Aliasing regressions execute O2 and O3/LTO output: the compatibility
default preserves mixed-width writes, explicit strict aliasing reproduces the
intentional negative control, and a valid character-access version passes even
with strict aliasing. Publication fails if any architecture lacks these checks.
The architecture comparison requires the boot areas, modules and
disc file contents to match. Whole ISO hashes are excluded because filesystem
metadata contains build dates.
The regional signatures follow [ares' disc detection](https://github.com/ares-emulator/ares/blob/master/mia/medium/mega-cd.cpp).

The GCC 16 container's US template was boot-tested in ares v148: the user
confirmed all three upstream modules animated and cycled correctly. The local
ARM64 image suite also passed all seven examples and three regional builds.
Build tests do not prove CD audio, PCM playback, scaling effects or real-console
behavior; those need separate runtime checks.

## CI and Docker Hub

The workflow uses native Ubuntu ARM64 and AMD64 runners. PRs build and test
without publishing. A push to `main` builds and tests both images, pushes
commit-specific platform tags, compares target payloads, then publishes a
single manifest as:

- `ewrogers/megadev:latest`
- `ewrogers/megadev:7a7246c-gcc16.2.0-binutils2.47`

Neither public tag is updated if an architecture fails or payloads disagree.
Manual runs only publish from `main` with the publish checkbox selected.
The `DOCKERHUB_TOKEN` repository secret needs push access to `ewrogers/megadev`.
Workflow permissions are read-only; fork PRs never receive the publishing token.
Actions are pinned to verified release commits and tracked by Dependabot.

GNU source archives and recipes ship with the image so the bundled compiler
and debugger sources remain available. Source upgrades require renewed
regression and runtime validation, especially before removing a workaround.
