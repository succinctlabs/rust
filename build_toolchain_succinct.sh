#!/usr/bin/env bash
# rust/build-toolchain.sh
# Builds the SP1 custom toolchain and packs stage2 into rust-toolchain-<host>.tar.gz

set -euo pipefail

TARGET_RISCV="riscv64im-succinct-zkvm-elf"
HOST_TRIPLE="$(rustc -vV | awk '/^host:/ {print $2}')"

echo "==> host triple: $HOST_TRIPLE"
echo "==> building rust stage2 for targets: $TARGET_RISCV, $HOST_TRIPLE"

##############################
# 1. one-line sanity work-arounds
##############################
TMP_TARGET_DIR="$(mktemp -d)"
touch "$TMP_TARGET_DIR/${TARGET_RISCV}.json"      # bypass target-sanity check
export RUST_TARGET_PATH="$TMP_TARGET_DIR"
export CARGO_TARGET_RISCV64IM_SUCCINCT_ZKVM_ELF_RUSTFLAGS="-Cpasses=lower-atomic"

##############################
# 2. compile
##############################
  cat > bootstrap.toml <<TOML
[build]
extended = true
tools = ["cargo", "cargo-clippy", "clippy", "rustfmt"]
configure-args = []
cargo-native-static = true

[rust]
lld = true
llvm-tools = true

[llvm]
download-ci-llvm = false
TOML

python3 x.py build --stage 2 library \
  --target "${TARGET_RISCV},${HOST_TRIPLE}"

##############################
# 3. pack artifact
##############################
STAGE2_DIR="$(find build -maxdepth 2 -type d -name stage2 | head -n1)"
[[ -d "$STAGE2_DIR" ]] || { echo "error: stage2 not found"; exit 1; }

OUT_TAR="rust-toolchain-${HOST_TRIPLE}.tar.gz"
tar --exclude 'lib/rustlib/src' \
    --exclude 'lib/rustlib/rustc-src' \
    -hczvf "$OUT_TAR" -C "$STAGE2_DIR" .

echo "==> done – artifact: $OUT_TAR"
