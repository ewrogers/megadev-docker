# Working on Megadev Docker

- Keep this a Sega CD toolchain, not a game framework. Preserve upstream
  Megadev examples and distinguish upstream code from our packaging.
- Use `ewrogers/megadev:latest` in public usage commands. Lock and checksum
  source inputs for builds; review updates and run both architecture suites.
- Target the base 68000 on both CPUs. Keep compiler and assembler guards,
  the byte-copy workaround, and executed regressions in sync with SGDK Docker.
- Keep GNU C17 as the default without replacing Megadev's project flags.
- No BIOS, commercial disc images, private paths or credentials in this
  repository or container. Source downloads and test outputs belong in build/.
- Test real compiled machine code, fresh upstream examples, disc contents,
  useful failures, and ARM64/AMD64 payload agreement. Do not confuse compilation
  with emulator, audio or hardware validation.
- Keep helper scripts small, portable and standard-library Python where possible.
  Preserve argument boundaries, exit codes and host file ownership.
- Retain third-party license notices and GNU source archives/build recipes.
- Keep README usage concise and natural. Put maintainer details in docs/.
- Changes require PR review. Never merge a PR on the user's behalf.
