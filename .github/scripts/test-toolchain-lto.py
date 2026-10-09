#!/usr/bin/env python3
"""Build and execute an LTO guest using the actual release archive."""

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile


archive = Path(sys.argv[1]).resolve()
manifest = Path(__file__).resolve().parent.parent / "tests/lto/Cargo.toml"
target = "riscv64im-succinct-zkvm-elf"
# Match the SP1 6.8.1 guest build flags.
flags = [
    "-C", "passes=lower-atomic",
    "-C", "link-arg=--image-base=2013265920",
    "-C", "panic=abort",
    "--cfg", 'getrandom_backend="custom"',
    "-C", "llvm-args=-misched-prera-direction=bottomup",
    "-C", "llvm-args=-misched-postra-direction=bottomup",
]

with tempfile.TemporaryDirectory(prefix="sp1-lto-test-") as directory:
    root = Path(directory)
    toolchain = root / "toolchain"
    toolchain.mkdir()
    subprocess.run(["tar", "-xzf", archive, "-C", toolchain], check=True)

    version = subprocess.check_output([toolchain / "bin/rustc", "-vV"], text=True)
    host = next(
        line.removeprefix("host: ") for line in version.splitlines() if line.startswith("host: ")
    )
    llvm = toolchain / "lib/rustlib" / host / "bin"
    for std_target in ("riscv32im-succinct-zkvm-elf", target):
        libraries = list((toolchain / "lib/rustlib" / std_target / "lib").glob("libstd-*.rlib"))
        assert len(libraries) == 1, f"expected one libstd for {std_target}"
        objects = root / std_target
        objects.mkdir()
        subprocess.run([llvm / "llvm-ar", "x", libraries[0]], cwd=objects, check=True)
        members = list(objects.glob("*.o"))
        assert members, f"missing libstd objects for {std_target}"
        for member in members:
            bitcode = member.with_suffix(".bc")
            subprocess.run([
                llvm / "llvm-objcopy", f"--dump-section=.llvmbc={bitcode}", member,
            ], check=True)
            ir = subprocess.check_output([llvm / "llvm-dis", bitcode, "-o", "-"], text=True)
            assert not re.search(r"\b(load atomic|store atomic|atomicrmw|cmpxchg)\b", ir), (
                f"atomic operations remain in {std_target}/{member.name} embedded bitcode"
            )
        print(f"PASS: {std_target} libstd embedded bitcode has no atomic operations", flush=True)

    host_env = os.environ.copy()
    for name in ("RUSTC", "RUSTFLAGS", "CARGO_ENCODED_RUSTFLAGS", "CARGO_PROFILE_RELEASE_LTO"):
        host_env.pop(name, None)
    host_env["CARGO_TARGET_DIR"] = str(root / "host")
    subprocess.run([
        "cargo", "build", "--locked", "--manifest-path", str(manifest),
        "-p", "lto-atomic-runner",
    ], env=host_env, check=True)
    runner = root / "host/debug/lto-atomic-runner"

    for lto in ("off", "thin", "fat"):
        guest_env = host_env.copy()
        guest_env.update({
            "RUSTC": str(toolchain / "bin/rustc"),
            "CARGO_ENCODED_RUSTFLAGS": "\x1f".join(flags),
            "CARGO_PROFILE_RELEASE_LTO": lto,
            "CARGO_TARGET_DIR": str(root / lto),
        })
        subprocess.run([
            "cargo", "build", "--locked", "--manifest-path", str(manifest),
            "-p", "lto-atomic-guest", "--release", "--target", target,
        ], env=guest_env, check=True)
        subprocess.run([runner, root / lto / target / "release/lto-atomic-guest"], check=True)
        print(f"PASS: LTO={lto}", flush=True)
