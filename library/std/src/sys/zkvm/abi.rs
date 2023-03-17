//! ABI definitions for symbols exported by risc0-zkvm-platform.

// Included here so we don't have to depend on risc0-zkvm-platform.
//
// TODO: Should we move this to the "libc" crate?  It seems like other
// architectures put a lot of this kind of stuff there.  But there's
// currently no risc0 fork of the libc crate, so we'd either have to
// fork it or upstream it.

pub const DIGEST_WORDS: usize = 8;

/// Standard IO file descriptors for use with sys_read and sys_write.
pub mod fileno {
    pub const STDIN: u32 = 0;
    pub const STDOUT: u32 = 1;
    pub const STDERR: u32 = 2;
    pub const JOURNAL: u32 = 3;
}

extern "C" {
    // Syscall names are all nul-terminated c-style string.  Raw access to syscalls:
    pub fn syscall_0(name: *const u8, from_host: *mut u32, from_host_words: usize) -> (u32, u32);
    pub fn syscall_1(
        name: *const u8,
        from_host: *mut u32,
        from_host_words: usize,
        a3: u32,
    ) -> (u32, u32);
    pub fn syscall_2(
        name: *const u8,
        from_host: *mut u32,
        from_host_words: usize,
        a3: u32,
        a4: u32,
    ) -> (u32, u32);
    pub fn syscall_3(
        name: *const u8,
        from_host: *mut u32,
        from_host_words: usize,
        a3: u32,
        a4: u32,
        a5: u32,
    ) -> (u32, u32);
    pub fn syscall_4(
        name: *const u8,
        from_host: *mut u32,
        from_host_words: usize,
        a3: u32,
        a4: u32,
        a5: u32,
        a6: u32,
    ) -> (u32, u32);
    pub fn syscall_5(
        name: *const u8,
        from_host: *mut u32,
        from_host_words: usize,
        a3: u32,
        a4: u32,
        a5: u32,
        a6: u32,
        a7: u32,
    ) -> (u32, u32);

    // Wrappers around syscalls provided by risc0-zkvm-platform:
    pub fn sys_halt();
    pub fn sys_output(output_id: u32, output_value: u32);
    pub fn sys_sha_compress(
        out_state: *mut [u32; DIGEST_WORDS],
        in_state: *const [u32; DIGEST_WORDS],
        block1_ptr: *const [u32; DIGEST_WORDS],
        block2_ptr: *const [u32; DIGEST_WORDS],
    );
    pub fn sys_sha_buffer(
        out_state: *mut [u32; DIGEST_WORDS],
        in_state: *const [u32; DIGEST_WORDS],
        buf: *const u8,
        count: u32,
    );
    pub fn sys_rand(recv_buf: *mut u32, words: usize);
    pub fn sys_panic(msg_ptr: *const u8, len: usize) -> !;
    pub fn sys_log(msg_ptr: *const u8, len: usize);
    pub fn sys_cycle_count() -> usize;
    pub fn sys_read(fd: u32, recv_buf: *mut u8, nrequested: usize) -> usize;
    pub fn sys_write(fd: u32, write_buf: *const u8, nbytes: usize);
    pub fn sys_getenv(
        recv_buf: *mut u32,
        words: usize,
        varname: *const u8,
        varname_len: usize,
    ) -> usize;

    // Allocate memory from global HEAP.
    pub fn sys_alloc_words(nwords: usize) -> *mut u32;
}
