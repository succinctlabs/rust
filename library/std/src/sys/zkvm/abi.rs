extern "Rust" {
    pub(crate) fn zkvm_abi_alloc_words(nwords: usize) -> *mut u32;
    pub(crate) fn zkvm_abi_write_stdout(buf: &[u8]);
    pub(crate) fn zkvm_abi_write_stderr(buf: &[u8]);
}
