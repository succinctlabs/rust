#!/usr/bin/env python3
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile


validator = Path(__file__).with_name("validate-toolchain.sh")
libraries = [
    f"lib/rustlib/{target}/lib/lib{library}-test.rlib"
    for target in ("riscv32im-succinct-zkvm-elf", "riscv64im-succinct-zkvm-elf")
    for library in ("core", "std")
]
members = {"bin/rustc": b"#!/bin/sh\nexit 0\n", **dict.fromkeys(libraries, b"test")}
cases = [("complete", members, True)]
for missing in members:
    cases.append((f"missing {missing}", {k: v for k, v in members.items() if k != missing}, False))
cases.extend([
    ("compiler fails", {**members, "bin/rustc": b"#!/bin/sh\nexit 1\n"}, False),
    ("empty library", {**members, libraries[0]: b""}, False),
])

with tempfile.TemporaryDirectory() as directory:
    archive = Path(directory) / "toolchain.tar.gz"
    for name, files, expected_success in cases:
        with tarfile.open(archive, "w:gz") as output:
            for path, data in files.items():
                entry = tarfile.TarInfo(path)
                entry.size = len(data)
                entry.mode = 0o755 if path == "bin/rustc" else 0o644
                output.addfile(entry, io.BytesIO(data))
        result = subprocess.run(["bash", str(validator), str(archive)], capture_output=True, text=True)
        assert (result.returncode == 0) == expected_success, f"{name}: {result.stderr}"
        print(f"PASS: {name}")
