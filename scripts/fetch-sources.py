#!/usr/bin/env python3
"""Fetch exactly the locked sources; reject incomplete or altered downloads."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=Path("/build/sources.lock.json"))
    parser.add_argument("--output", type=Path, default=Path("/opt/sources"))
    parser.add_argument("names", nargs="+")
    args = parser.parse_args()
    sources = json.loads(args.lock.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    for name in args.names:
        source = sources[name]
        target = args.output / source["archive"]
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == source["sha256"]:
            continue
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=args.output, delete=False) as out:
                temporary = Path(out.name)
                with urllib.request.urlopen(source["url"], timeout=120) as response:
                    shutil.copyfileobj(response, out)
            actual = hashlib.sha256(temporary.read_bytes()).hexdigest()
            if actual != source["sha256"]:
                raise ValueError(f"{name}: source checksum mismatch")
            temporary.replace(target)
            print(f"Verified {name} {source['version']}", flush=True)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
