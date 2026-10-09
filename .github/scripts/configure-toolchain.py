#!/usr/bin/env python3
"""Retain source commit metadata in the pinned CI builder configuration."""

from pathlib import Path
import sys


def retain_commit_hash(config):
    if config.count("[rust]\n") != 1 or "omit-git-hash" in config:
        raise ValueError("Expected one [rust] section without an omit-git-hash override")
    return config.replace("[rust]\n", "[rust]\nomit-git-hash = false\n")


if __name__ == "__main__":
    path = Path(sys.argv[1]) / "crates/cli/src/commands/bootstrap.toml"
    path.write_text(retain_commit_hash(path.read_text()))
