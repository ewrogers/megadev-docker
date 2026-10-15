#!/bin/sh
set -eu
printf 'Host: '; uname -m
printf 'Megadev: '; python3 -c 'import json; print(json.load(open("/usr/local/share/megadev/sources.lock.json"))["megadev"]["commit"])'
printf 'Target: '; m68k-elf-gcc -dumpmachine
printf 'GCC: '; m68k-elf-gcc -dumpfullversion
m68k-elf-ld --version | head -1
m68k-elf-gdb --version | head -1
mkisofs --version
printf 'Defaults: GNU C17, base 68000, no FPU/MMU, -fno-auto-inc-dec\n'
for tool in make git python3 xxd m68k-elf-as m68k-elf-ar m68k-elf-objcopy m68k-elf-gdb; do
    command -v "$tool"
done
