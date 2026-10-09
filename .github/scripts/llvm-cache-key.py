#!/usr/bin/env python3
"""Identify installed LLVM outputs that can be reused by the CI build."""

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


def output(*args, cwd=None):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def system_inputs():
    inputs = {tool: output(tool, "--version") for tool in ("cc", "c++", "cmake", "ninja")}
    inputs["rustc"] = output("rustc", "-vV")
    inputs["platform"] = platform.platform()
    if sys.platform == "darwin":
        inputs["sdk"] = output("xcrun", "--sdk", "macosx", "--show-sdk-version")
        inputs["sdk_path"] = output("xcrun", "--sdk", "macosx", "--show-sdk-path")
        inputs["xcode"] = output("xcodebuild", "-version")
    else:
        inputs["packages"] = output("dpkg-query", "-W")
    inputs["environment"] = {
        name: os.environ.get(name, "")
        for name in (
            "ImageOS", "ImageVersion", "RUSTUP_TOOLCHAIN", "CC", "CXX", "AR",
            "CFLAGS", "CXXFLAGS", "CPPFLAGS", "LDFLAGS", "SDKROOT",
            "MACOSX_DEPLOYMENT_TARGET", "CMAKE_TOOLCHAIN_FILE", "DEVELOPER_DIR",
        )
    }
    return inputs


def cache_key(rust, sp1, host):
    # Bootstrap controls LLVM flags; the pinned builder supplies bootstrap.toml.
    sources = {
        path: output("git", "rev-parse", f"HEAD:{path}", cwd=rust)
        for path in (
            "src/llvm-project", "src/bootstrap", "src/build_helper", "src/version",
            "compiler/rustc_target", "Cargo.toml", "Cargo.lock",
        )
    }
    inputs = {
        "sources": sources,
        "builder": output("git", "rev-parse", "HEAD", cwd=sp1),
        "builder_config": (sp1 / "crates/cli/src/commands/bootstrap.toml").read_text(),
        "host": host,
        # Installed CMake files can contain absolute paths.
        "workspace": str(rust.resolve()),
        "system": system_inputs(),
        "workflow": (rust / ".github/workflows/ci.yml").read_text(),
        "key_script": Path(__file__).read_text(),
    }
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    return f"llvm-v1-{host}-{digest}"


if __name__ == "__main__":
    rust = Path(__file__).resolve().parents[2]
    print(cache_key(rust, rust.parent / "sp1", sys.argv[1]))
