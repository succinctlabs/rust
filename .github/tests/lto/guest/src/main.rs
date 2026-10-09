#![no_main]

sp1_zkvm::entrypoint!(main);

pub fn main() {
    let n: u64 = sp1_zkvm::io::read();
    if n == 42 {
        panic!("boom {n}");
    }
    sp1_zkvm::io::commit(&n);
}
