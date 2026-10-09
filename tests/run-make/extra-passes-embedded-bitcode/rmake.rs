//! User passes must run before bitcode is embedded for downstream LTO.

//@ needs-target-std
//@ needs-target-has-atomic: 32
//@ ignore-wasm

use run_make_support::object::read::archive::ArchiveFile;
use run_make_support::object::{Object, ObjectSection};
use run_make_support::{llvm_dis, object, rfs, rustc};

fn main() {
    for opt_level in ["0", "3"] {
        for lto in ["off", "thin", "fat"] {
            rustc()
                .input("atomic.rs")
                .crate_type("rlib")
                .output("libatomic.rlib")
                .codegen_units(1)
                .opt_level(opt_level)
                .arg(format!("-Clto={lto}"))
                .arg("-Cembed-bitcode=yes")
                .arg("-Cpasses=lower-atomic")
                .run();

            let bytes = rfs::read("libatomic.rlib");
            let archive = ArchiveFile::parse(bytes.as_slice()).unwrap();
            let mut objects = 0;
            for member in archive.members() {
                let member = member.unwrap();
                if !member.name().ends_with(b".o") {
                    continue;
                }
                objects += 1;
                let object = object::File::parse(member.data(bytes.as_slice()).unwrap()).unwrap();
                let bitcode = object
                    .section_by_name(".llvmbc")
                    .or_else(|| object.section_by_name("__bitcode"))
                    .expect("missing embedded bitcode");
                rfs::write("atomic.bc", bitcode.data().unwrap());
                let output = llvm_dis().input("atomic.bc").arg("-o").arg("-").run();
                output.assert_stdout_contains("@atomic_ops");
                for instruction in ["load atomic", "store atomic", "atomicrmw", "cmpxchg"] {
                    output.assert_stdout_not_contains(instruction);
                }
            }
            assert_eq!(objects, 1);
            println!("PASS: codegen-units=1, opt-level={opt_level}, LTO={lto}");
        }
    }
}
