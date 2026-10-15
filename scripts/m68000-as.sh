#!/bin/sh
# Both Mega Drive and Sega CD CPUs use the original 68000 instruction set.
set -eu
for argument in "$@"; do
    case "$argument" in
        -m68000|-mcpu=68000|-march=68000) ;;
        -m[0-9]*|-mcpu=*|-march=*|-mcf*|-mcoldfire*|-mcpu32)
            echo 'Megadev assembler: target must be a 68000 without an FPU or MMU' >&2
            exit 1
            ;;
    esac
done
exec /opt/m68k/bin/m68k-elf-as.real -m68000 -mno-68881 -mno-68851 "$@"
