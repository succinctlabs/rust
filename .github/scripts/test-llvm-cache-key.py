#!/usr/bin/env python3
"""Check cache invalidation against small real Git repositories."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "llvm_cache_key", Path(__file__).with_name("llvm-cache-key.py")
)
cache = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache)
spec = importlib.util.spec_from_file_location(
    "configure_toolchain", Path(__file__).with_name("configure-toolchain.py")
)
configure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configure)


class CacheKeyTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.rust = Path(self.directory.name) / "rust"
        self.sp1 = Path(self.directory.name) / "sp1"
        for repo in (self.rust, self.sp1):
            repo.mkdir()
            self.git(repo, "init", "-q")
            self.git(repo, "config", "user.name", "Test")
            self.git(repo, "config", "user.email", "test@example.invalid")
        for path in (
            "src/llvm-project/source", "src/bootstrap/config", "src/build_helper/source",
            "src/version", "compiler/rustc_target/source", "Cargo.toml", "Cargo.lock",
            ".github/workflows/ci.yml", "compiler/rustc_llvm/wrapper",
        ):
            self.write(self.rust, path, "initial")
        self.write(self.sp1, "crates/cli/src/commands/bootstrap.toml", "[rust]\nlld = true\n")
        for repo in (self.rust, self.sp1):
            self.commit(repo)
        self.system = {"compiler": "compiler-1", "sdk": "sdk-1", "flags": ""}
        mock = patch.object(cache, "system_inputs", side_effect=lambda: self.system)
        mock.start()
        self.addCleanup(mock.stop)

    def git(self, repo, *args):
        return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.STDOUT)

    def write(self, repo, path, value):
        file = repo / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(value)

    def commit(self, repo):
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "test: update fixture")

    def key(self, host="aarch64-apple-darwin"):
        return cache.cache_key(self.rust, self.sp1, host)

    def test_rust_wrapper_change_reuses_llvm(self):
        before = self.key()
        self.write(self.rust, "compiler/rustc_llvm/wrapper", "changed")
        self.commit(self.rust)
        self.assertEqual(before, self.key())

    def test_llvm_build_inputs_invalidate_cache(self):
        for path in (
            "src/llvm-project/source", "src/bootstrap/config", "src/build_helper/source",
            "src/version", "compiler/rustc_target/source", "Cargo.lock",
            ".github/workflows/ci.yml",
        ):
            with self.subTest(path=path):
                before = self.key()
                self.write(self.rust, path, "changed")
                self.commit(self.rust)
                self.assertNotEqual(before, self.key())

    def test_builder_configuration_invalidates_cache(self):
        before = self.key()
        self.write(self.sp1, "crates/cli/src/commands/bootstrap.toml", "changed")
        self.commit(self.sp1)
        self.assertNotEqual(before, self.key())

    def test_ci_override_preserves_options_and_invalidates_cache(self):
        before = self.key()
        path = self.sp1 / "crates/cli/src/commands/bootstrap.toml"
        path.write_text(configure.retain_commit_hash(path.read_text()))
        self.assertEqual(path.read_text(), "[rust]\nomit-git-hash = false\nlld = true\n")
        # The checkout commit stays the same; the actual builder config must be keyed.
        self.assertNotEqual(before, self.key())

    def test_config_override_rejects_ambiguous_input(self):
        for value in ("[build]\n", "[rust]\n[rust]\n", "[rust]\nomit-git-hash = true\n"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                configure.retain_commit_hash(value)

    def test_host_compiler_sdk_and_flags_invalidate_cache(self):
        self.assertNotEqual(self.key(), self.key("x86_64-unknown-linux-gnu"))
        for name in self.system:
            with self.subTest(name=name):
                before = self.key()
                self.system[name] = "changed"
                self.assertNotEqual(before, self.key())

    def test_missing_input_fails(self):
        self.git(self.rust, "rm", "src/version")
        self.commit(self.rust)
        with self.assertRaises(subprocess.CalledProcessError):
            self.key()

    def test_shallow_clone_preserves_key_and_commit_metadata(self):
        shallow = Path(self.directory.name) / "shallow"
        self.git(self.rust, "clone", "-q", "--depth=1", self.rust.as_uri(), str(shallow))
        self.assertEqual(self.git(shallow, "rev-parse", "--is-shallow-repository").strip(), b"true")
        self.assertEqual(
            self.git(self.rust, "log", "-1", "--format=%H %cs"),
            self.git(shallow, "log", "-1", "--format=%H %cs"),
        )
        # Compare the same install path because CMake outputs can embed it.
        original = self.rust.with_name("original")
        self.rust.rename(original)
        shallow.rename(self.rust)
        shallow_key = self.key()
        self.rust.rename(shallow)
        original.rename(self.rust)
        self.assertEqual(self.key(), shallow_key)


if __name__ == "__main__":
    unittest.main()
