use super::abi;
use crate::alloc::{GlobalAlloc, Layout, System};
use crate::cell::UnsafeCell;

const WORD_SIZE: usize = core::mem::size_of::<u32>();

#[stable(feature = "alloc_system_type", since = "1.28.0")]
unsafe impl GlobalAlloc for System {
    #[inline]
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let nwords = layout
            .align_to(WORD_SIZE)
            .expect("Unable to align allocation to word size")
            .pad_to_align()
            .size()
            / WORD_SIZE;

        abi::zkvm_abi_alloc_words(nwords) as *mut u8
    }

    #[inline]
    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {
        // this allocator never deallocates memory
    }
}
