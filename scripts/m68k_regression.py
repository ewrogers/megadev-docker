"""Execute compiled 68000 code, including a known optimizer negative control."""
from pathlib import Path
import subprocess


def execute(binary, symbols, *, rom=False):
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN
    from unicorn.m68k_const import UC_CPU_M68K_M68000, UC_M68K_REG_A7, UC_M68K_REG_D0, UC_M68K_REG_PC, UC_M68K_REG_SR

    names = {}
    for line in symbols.read_text().splitlines():
        fields = line.split()
        if len(fields) == 3:
            names[fields[2]] = int(fields[0], 16)
    machine = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    machine.ctl_set_cpu_model(UC_CPU_M68K_M68000)
    machine.mem_map(0, 0x400000)
    machine.mem_map(0xA00000, 0x20000)
    machine.mem_map(0xE0FF0000, 0x10000)
    machine.mem_write(0 if rom else 0x10000, binary.read_bytes())
    machine.mem_write(0xA00000, b"\xcc" * 8192)
    machine.reg_write(UC_M68K_REG_SR, 0x2700)
    machine.reg_write(UC_M68K_REG_A7, 0xE0FFFFE0)
    end = 0x300000 if rom else names["finished"]
    machine.mem_write(0xE0FFFFE0, end.to_bytes(4, "big"))
    entries = [address for name, address in names.items() if name == "main" or name.startswith("main.")]
    if rom and len(entries) != 1:
        raise AssertionError("Expected one SGDK main entry point")
    machine.emu_start(entries[0] if rom else names["_start"], end, count=2_000_000)
    if machine.reg_read(UC_M68K_REG_PC) != end:
        raise AssertionError("M68000 byte-copy test did not return within its instruction limit")
    return machine.reg_read(UC_M68K_REG_D0)


def run_regression(base, output):
    def run(name, command):
        with (output / f"{name}.log").open("w") as log:
            subprocess.run([*base, *command], stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)

    (output / "cpu-probe.c").write_text("int answer(void) { return 42; }\n")
    for option in ["-m68010", "-m68020", "-mcpu=68040", "-mcpu=cpu32", "-mcpu=5475",
                   "-march=68020", "-m68881", "-m68851"]:
        with (output / f"reject{option}.log").open("w") as log:
            result = subprocess.run([*base, "m68k-elf-gcc", option, "-c", "cpu-probe.c", "-o", "invalid.o"], stdout=log, stderr=subprocess.STDOUT)
        if result.returncode == 0:
            raise AssertionError(f"Compiler accepted incompatible CPU option {option}")
    (output / "invalid-cpu.s").write_text(".text\n extb.l %d0\n")
    for name, command in [
        ("compiler", ["m68k-elf-gcc", "-c", "invalid-cpu.s", "-o", "invalid.o"]),
        ("assembler", ["m68k-elf-as", "invalid-cpu.s", "-o", "invalid.o"]),
        ("assembler-cpu", ["m68k-elf-as", "-m68020", "invalid-cpu.s", "-o", "invalid.o"]),
        ("assembler-override", ["m68k-elf-gcc", "-Wa,-m68020", "-c", "invalid-cpu.s", "-o", "invalid.o"]),
    ]:
        with (output / f"reject-68020-{name}.log").open("w") as log:
            result = subprocess.run([*base, *command], stdout=log, stderr=subprocess.STDOUT)
        if result.returncode == 0:
            raise AssertionError(f"{name} accepted a 68020-only instruction or CPU option")
    (output / "invalid-fpu.s").write_text(".text\n fnop\n")
    with (output / "reject-fpu-instruction.log").open("w") as log:
        result = subprocess.run([*base, "m68k-elf-as", "invalid-fpu.s", "-o", "invalid.o"], stdout=log, stderr=subprocess.STDOUT)
    if result.returncode == 0:
        raise AssertionError("Assembler accepted an FPU instruction")

    # Preserve GCC's assembler CPU forwarding when installing custom specs.
    # A 68020 BRA.L is invalid on a 68000; GAS must expand far jumps safely.
    (output / "far-branch.s").write_text(".text\n.globl _start\n_start:\n jra far\n.globl finished\nfinished:\n nop\n.space 40000\nfar:\n moveq #0,%d0\n jra finished\n")
    run("far-branch", ["m68k-elf-gcc", "-nostdlib", "-Wl,-Ttext=0x10000", "-Wl,-e,_start", "far-branch.s", "-o", "far-branch.elf"])
    run("far-branch-extract", ["sh", "-c", "m68k-elf-objcopy -O binary far-branch.elf far-branch.bin && m68k-elf-nm far-branch.elf > far-branch.nm"])
    if execute(output / "far-branch.bin", output / "far-branch.nm"):
        raise AssertionError("M68000 far-branch regression failed")

    # Also guard the compiler default independently of SGDK. The explicit
    # opt-in is a negative control: GCC 16.2 must reproduce the original bug.
    (output / "copy-probe.c").write_text('''
static const unsigned char source[8192] = {0xf3,0xc3,0xb7,0x02,[8191]=0x5a};
__attribute__((noinline)) void upload(unsigned short to, const unsigned char *from, unsigned short size) {
    unsigned char *src = (unsigned char *)from;
    volatile unsigned char *dst = (unsigned char *)(0xa00000ul + to);
    unsigned short len = size;
    while (len--) *dst++ = *src++;
}
int probe(void) {
    upload(0, source, sizeof(source));
    for (unsigned short i = 0; i < sizeof(source); i++)
        if (((volatile unsigned char *)0xa00000)[i] != source[i]) return 1;
    return 0;
}
''')
    (output / "copy-start.s").write_text(".text\n.globl _start\n_start:\n jsr probe\n.globl finished\nfinished:\n nop\n")
    for name, flags, expected in [("copy-default", [], 0), ("copy-negative-control", ["-fauto-inc-dec"], 1)]:
        run(name, ["m68k-elf-gcc", "-m68000", "-std=c17", "-O3", "-fno-web", "-fno-gcse", "-flto", "-nostdlib",
                   "-Wl,-Ttext=0x10000", "-Wl,-e,_start", "copy-start.s", "copy-probe.c", "-o", f"{name}.elf", *flags])
        run(f"{name}-extract", ["sh", "-c", f"m68k-elf-objcopy -O binary {name}.elf {name}.bin && m68k-elf-nm {name}.elf > {name}.nm"])
        result = execute(output / f"{name}.bin", output / f"{name}.nm")
        if result != expected:
            raise AssertionError(f"{name}: expected {expected}, got {result}; review GCC workaround")
    # GCC's libgcc is built for the base 68000 with multilib disabled. Long
    # division/multiplication must work too, without 68020-only instructions.
    (output / "arithmetic.c").write_text('''
volatile unsigned long a = 0x12345678ul, b = 12345ul;
int probe(void) {
    unsigned long x = a, y = b;
    if (x / y != 24740ul || x % y != 4596ul) return 1;
    if (x * y != 0xddddc0b8ul) return 2;
    return 0;
}
''')
    run("arithmetic", ["m68k-elf-gcc", "-O2", "-nostdlib", "-Wl,-Ttext=0x10000", "-Wl,-e,_start",
                       "copy-start.s", "arithmetic.c", "-lgcc", "-o", "arithmetic.elf"])
    run("arithmetic-extract", ["sh", "-c", "m68k-elf-objcopy -O binary arithmetic.elf arithmetic.bin && m68k-elf-nm arithmetic.elf > arithmetic.nm"])
    if execute(output / "arithmetic.bin", output / "arithmetic.nm"):
        raise AssertionError("M68000 libgcc arithmetic regression failed")
    print("Passed M68000 execution, libgcc arithmetic and failing optimization control", flush=True)
    return {"compiler_default": "passed", "negative_control": "reproduced", "far_branch": "passed",
            "cpu_policy": "passed", "libgcc_arithmetic": "passed", "emulator": "Unicorn 2.1.4 M68000"}
