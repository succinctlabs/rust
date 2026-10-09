#![no_std]

use core::sync::atomic::{AtomicU32, Ordering};

#[no_mangle]
pub fn atomic_ops(value: &AtomicU32, replacement: u32) -> u32 {
    let previous = value.load(Ordering::Relaxed);
    value.store(replacement, Ordering::Relaxed);
    let _ = value.compare_exchange(previous, replacement, Ordering::Relaxed, Ordering::Relaxed);
    value.fetch_add(1, Ordering::Relaxed)
}
