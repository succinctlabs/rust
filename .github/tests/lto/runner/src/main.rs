use std::sync::Arc;

use sp1_core_executor::{MinimalExecutorEnum, Program};

fn main() {
    let path = std::env::args().nth(1).expect("expected guest ELF path");
    let program = Arc::new(Program::from_elf(&path).expect("invalid guest ELF"));
    for n in [41_u64, 42] {
        let mut executor = MinimalExecutorEnum::new(program.clone(), false, Some(100_000));
        executor.with_input(&bincode::serialize(&n).unwrap());
        while executor.try_execute_chunk().expect("guest execution failed").is_some() {
            assert!(executor.global_clk() < 1_000_000, "guest did not halt");
        }
        if n == 42 {
            assert_eq!(executor.exit_code(), 1, "panic must fail the guest");
            assert!(executor.public_values_stream().is_empty());
        } else {
            assert_eq!(executor.exit_code(), 0);
            assert_eq!(executor.public_values_stream(), &bincode::serialize(&n).unwrap());
        }
        println!("PASS: input={n}, exit_code={}", executor.exit_code());
    }
}
