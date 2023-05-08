use super::{abi, WORD_SIZE};
use crate::alloc::{GlobalAlloc, Layout, System};

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

        abi::sys_alloc_words(nwords) as *mut u8
    }

    #[inline]
    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {
        // this allocator never deallocates memory
    }
}
