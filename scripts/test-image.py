#!/usr/bin/env python3
"""Build fresh upstream projects and execute compiler correctness regressions."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from disc import digest, inspect_iso
from m68k_regression import run_regression


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument("--platform", required=True, choices=("linux/arm64", "linux/amd64"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    metadata = json.loads(subprocess.check_output(["docker", "image", "inspect", args.image], text=True))[0]
    if metadata["Architecture"] != args.platform.split("/")[1] or metadata["Config"]["User"] != "megadev":
        raise AssertionError("wrong architecture or default image user")
    base = ["docker", "run", "--rm", "--platform", args.platform,
            "--user", f"{os.getuid()}:{os.getgid()}", "--mount", f"type=bind,source={output},target=/workspace", args.image]

    def run(name, command, expected=0):
        log = output / f"{name}.log"
        with log.open("w") as stream:
            result = subprocess.run([*base, *command], stdout=stream, stderr=subprocess.STDOUT, timeout=300)
        if result.returncode != expected:
            raise RuntimeError(f"{name}: expected exit {expected}, got {result.returncode}; see {log}")
        return log.read_text()

    doctor = run("doctor", ["doctor"])
    assert ("aarch64" if args.platform.endswith("arm64") else "x86_64") in doctor
    assert "16.2.0" in doctor and "2.47" in doctor and "18.1" in doctor and "m68k-elf" in doctor
    root = Path(__file__).resolve().parents[1]
    sources = json.loads(run("locked-sources", ["cat", "/usr/local/share/megadev/sources.lock.json"]))
    debugger = json.loads(run("locked-debugger", ["cat", "/usr/local/share/megadev/debugger.lock.json"]))
    assert sources == json.loads((root / "sources.lock.json").read_text()), "image source inputs differ from this checkout"
    assert debugger == json.loads((root / "debugger.lock.json").read_text()), "image debugger inputs differ from this checkout"
    assert sources["megadev"]["commit"] in doctor
    run("source-access", ["sh", "-c", 'test -r /usr/local/share/megadev/sources/gcc.tar.xz && test -r /usr/local/share/megadev/sources/gdb.tar.xz && test -r /opt/megadev/LICENSE'])
    assert run("arguments", ["sh", "-c", 'printf "%s\\n" "$@"', "label", "two words", "semi;colon"]) == "two words\nsemi;colon\n"
    run("failure", ["sh", "-c", "exit 17"], expected=17)
    run("new", ["sh", "-c", 'mkdir "my game" && cd "my game" && megadev init'])
    run("protect-existing", ["sh", "-c", 'cd "my game" && megadev init'], expected=1)
    regression = run_regression(base, output)
    (output / "language.c").write_text('#if __STDC_VERSION__ != 201710L\n#error GNU C17 must be the default\n#endif\nint answer(void) { return 42; }\n')
    run("c17", ["m68k-elf-gcc", "-g", "-c", "language.c", "-o", "language.o"])
    assert "answer" in run("debugger", ["m68k-elf-gdb", "--batch", "-ex", "file language.o", "-ex", "info functions answer"])
    cases = {name: ("new_project" if name == "new_project" else f"examples/{name}", [])
             for name in ("new_project", "hello_world", "bram", "pcm_playback", "transforms", "gfx", "cart")}
    cases.update({f"region-{region}": ("new_project", [f"REGION={region}", f"VIDEO={'PAL' if region == 'EU' else 'NTSC'}"])
                  for region in ("US", "JP", "EU")})
    results = {}
    for name, (source, flags) in cases.items():
        run(f"copy-{name}", ["sh", "-c", 'cp -R "$MEGADEV_PATH/$1" "$2"; mkdir -p "$2/build" "$2/disc"', "copy", source, name])
        run(f"build-{name}", ["build", "-C", name, *flags])
        project = output / name
        payloads = {str(path.relative_to(project)): digest(path.read_bytes()) for path in sorted(project.rglob("*"))
                    if path.is_file() and path.suffix in (".bin", ".mmd", ".smd", ".cart") and path.parts[-2] in ("build", "disc", name)}
        assert payloads, f"{name}: no binary output"
        result = {"payloads": payloads}
        if name != "cart":
            images = list(project.glob("*.iso"))
            assert len(images) == 1
            result["disc"] = inspect_iso(images[0].read_bytes())
            run(f"cue-{name}", ["cue", str(images[0].relative_to(output))])
        else:
            assert next(project.glob("*.cart")).read_bytes()[0x100:0x104] == b"SEGA"
        results[name] = result
        print(f"Passed {name}", flush=True)
    run("spaced-path-build", ["sh", "-c", 'cd "my game" && megadev build'])
    run("clean", ["build", "-C", "new_project", "clean"])
    (output / "new_project/src/ipx.c").write_text('#error Intentional test failure\n')
    run("build-failure", ["build", "-C", "new_project"], expected=2)
    report = {"passed": True, "platform": args.platform, "image_id": metadata["Id"],
              "sources": {**sources, **debugger}, "doctor": doctor, "m68k_regression": regression, "examples": results}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Passed {args.platform}; report: {output / 'report.json'}")


if __name__ == "__main__":
    main()
