#!/usr/bin/env python3
"""Start an upstream project or describe a data ISO for an emulator."""
import argparse
import os
from pathlib import Path
import shutil


def initialize(destination, upstream):
    if any(destination.iterdir()):
        raise ValueError("init needs an empty folder; existing files were not changed")
    shutil.copytree(upstream / "new_project", destination, dirs_exist_ok=True)
    for name in ("build", "disc"):
        (destination / name).mkdir(exist_ok=True)


def write_cue(image):
    if any(character in image.name for character in ('"', '\n', '\r')):
        raise ValueError("ISO filename cannot contain quotes or line breaks")
    with image.open("rb") as stream:
        header = stream.read(16)
    if header[:16] != b"SEGADISCSYSTEM  " or image.stat().st_size % 2048:
        raise ValueError("expected a sector-aligned Megadev data ISO")
    target = image.with_suffix(".cue")
    # Do not overwrite a manually authored mixed-mode disc layout.
    with target.open("x") as stream:
        stream.write(f'FILE "{image.name}" BINARY\n  TRACK 01 MODE1/2048\n    INDEX 01 00:00:00\n')
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="copy upstream new_project into this empty folder")
    cue = commands.add_parser("cue", help="create a data-only CUE beside an ISO")
    cue.add_argument("image", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize(Path.cwd(), Path(os.environ.get("MEGADEV_PATH", "/opt/megadev")))
            print("Created Megadev's upstream new_project. Run build next.")
        else:
            print(write_cue(args.image))
    except (OSError, ValueError) as error:
        parser.exit(1, f"megadev: {error}\n")


if __name__ == "__main__":
    main()
