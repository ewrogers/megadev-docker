# Megadev Docker

Build Sega CD and Mega CD games with
[Megadev](https://github.com/drojaazu/megadev), a development kit for C and
68000 assembly. Docker keeps the compiler and disc tools together, so you
don't need to set up a cross-compiler on your computer. Your project and
finished disc images stay in your own folder.

The image includes GCC, binutils, GDB, Megadev's libraries and examples,
and `mkisofs` from genisoimage. It supports **ARM64 and AMD64**. Docker selects
the right image for your machine.

## Start a project

Install Docker and make sure it is running, then pull the image from
[Docker Hub](https://hub.docker.com/r/ewrogers/megadev):

```sh
docker pull ewrogers/megadev:latest
mkdir my-game
cd my-game
docker run --rm -v "$PWD:/workspace" ewrogers/megadev:latest init
docker run --rm -v "$PWD:/workspace" ewrogers/megadev:latest
docker run --rm -v "$PWD:/workspace" ewrogers/megadev:latest cue new_project.iso
```

`init` copies Megadev's own `new_project` example into an empty folder. It runs
code on both CPUs and loads three example modules from disc. Edit the project
Makefile and source files to make it your own. Existing files are never replaced
by `init`.

Open `new_project.cue` in your emulator. In ares, select **Mega CD** and configure
your own US BIOS and controller mappings. Press Start to launch the disc, then
again to cycle the modules. A BIOS is needed to play, not to build; none is
included or downloaded by this image.

## Build an existing project

Run these from a Megadev project folder:

```sh
docker run --rm -v "$PWD:/workspace" ewrogers/megadev:latest
docker run --rm -v "$PWD:/workspace" ewrogers/megadev:latest build clean
docker run --rm -v "$PWD:/workspace" ewrogers/megadev:latest build REGION=EU VIDEO=PAL
```

Clean before changing region or video settings. The example defaults to US/NTSC;
its region must match your emulator's BIOS. `cue` creates a **data-only** disc
layout and refuses to replace an existing CUE. Music tracks need a mixed-mode
layout; see Megadev's [disc mastering notes](https://github.com/drojaazu/megadev/blob/master/docs/disc.md).

## Use the tools

```sh
docker run --rm ewrogers/megadev:latest doctor
docker run --rm -it -v "$PWD:/workspace" ewrogers/megadev:latest bash
docker run --rm -v "$PWD:/workspace" ewrogers/megadev:latest m68k-elf-objdump -d build/ip.bin.elf
```

Megadev is at `/opt/megadev` (`$MEGADEV_PATH` inside the container).
`M68K_PREFIX=m68k-elf-` is already set. Ordinary `make` works too. Both console
CPUs target the original 68000, with GNU C17 as the default. This is a separate
toolchain from [SGDK Docker](https://github.com/ewrogers/sgdk-docker).

## Build the container locally

```sh
git clone https://github.com/ewrogers/megadev-docker.git
cd megadev-docker
docker buildx build --load -t megadev-local .
docker run --rm megadev-local doctor
```

The first build compiles the tools and takes a while. Use `megadev-local`
instead of `ewrogers/megadev:latest` in the project commands above.

## On your computer

- **macOS:** use Docker Desktop.
- **Linux:** use Docker Engine or Desktop. Add `--user "$(id -u):$(id -g)"`
  to keep generated files owned by your account.
- **Windows:** use Docker Desktop in Linux-container mode, preferably with
  [WSL2](https://docs.docker.com/desktop/features/wsl/). The commands above work
  in WSL. In PowerShell, replace `-v "$PWD:/workspace"` with
  `--mount "type=bind,source=$($PWD.Path),target=/workspace"`.

For the hardware and library, start with the
[Megadev manual](https://github.com/drojaazu/megadev/blob/master/docs/manual.md),
[C programming notes](https://github.com/drojaazu/megadev/blob/master/docs/dev_in_c.md)
and [Plutiedev](https://plutiedev.com/).
See [testing and publishing](docs/development.md) for versions, compiler
safeguards and maintainer instructions.

The packaging is MIT licensed. Bundled tools retain their own licenses.
GNU source archives and build recipes are included under
`/usr/local/share/megadev`; Megadev's license is at `/opt/megadev/LICENSE`.

## Disclaimer

Megadev Docker is an independent community project. It is not affiliated with,
endorsed by or sponsored by SEGA CORPORATION or SEGA SAMMY HOLDINGS INC.
SEGA and related names, logos and trademarks belong to their respective owners.
They are used here to identify the hardware and tools this project supports.

This repository's original work is available under the [MIT License](LICENSE).
Third-party software and materials retain their own licenses and notices.
