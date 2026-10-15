#!/usr/bin/env python3
"""Require both architecture suites to pass with matching target payloads."""
import json
from pathlib import Path
import sys


CASES = {"new_project", "hello_world", "bram", "pcm_playback", "transforms", "gfx", "cart",
         "region-US", "region-JP", "region-EU"}


def compare(left, right):
    if {left.get("platform"), right.get("platform")} != {"linux/arm64", "linux/amd64"}:
        raise ValueError("expected one ARM64 report and one AMD64 report")
    for report in (left, right):
        if report.get("passed") is not True or set(report.get("examples", {})) != CASES:
            raise ValueError("incomplete or failed architecture report")
        checks = report.get("m68k_regression", {})
        expected = {"compiler_default": "passed", "negative_control": "reproduced",
                    "far_branch": "passed", "cpu_policy": "passed", "libgcc_arithmetic": "passed"}
        if any(checks.get(key) != value for key, value in expected.items()):
            raise ValueError("missing executed compiler regressions")
        for case, outputs in report["examples"].items():
            if not outputs.get("payloads"):
                raise ValueError(f"{case}: no compiled payloads")
            if case != "cart":
                disc = outputs.get("disc", {})
                if not disc.get("boot") or "files" not in disc:
                    raise ValueError(f"{case}: no disc inspection")
                if case != "hello_world" and not disc["files"]:
                    raise ValueError(f"{case}: no disc files")
    if left.get("sources") != right.get("sources") or not left.get("sources"):
        raise ValueError("architecture reports used different source inputs")
    if left["examples"] != right["examples"]:
        raise ValueError("ARM64 and AMD64 target payloads differ")


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: compare-reports.py ARM64.json AMD64.json")
    compare(*(json.loads(Path(path).read_text()) for path in sys.argv[1:]))
    print("ARM64 and AMD64: compiler regressions passed; all boot, module and disc payloads match.")


if __name__ == "__main__":
    main()
