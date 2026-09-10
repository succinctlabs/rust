#!/usr/bin/env bash
set -euo pipefail

archive=${1:?Usage: validate-toolchain.sh ARCHIVE}
toolchain_dir=$(mktemp -d)
trap 'rm -rf -- "$toolchain_dir"' EXIT

tar -xzf "$archive" -C "$toolchain_dir"
"$toolchain_dir/bin/rustc" --version --verbose

for target in riscv32im-succinct-zkvm-elf riscv64im-succinct-zkvm-elf; do
    for library in core std; do
        libraries=("$toolchain_dir/lib/rustlib/$target/lib/lib$library-"*.rlib)
        if [[ ! -s "${libraries[0]}" ]]; then
            echo "Missing nonempty lib$library for $target" >&2
            exit 1
        fi
    done
done
