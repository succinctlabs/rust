use alloc::string::String;
use core::panic::BoxMeUp;

// Forward the abort message to libc's android_set_abort_message. We try our best to populate the
// message but as this function may already be called as part of a failed allocation, it might not be
// possible to do so.
//
// Some methods of core are on purpose avoided (such as try_reserve) as these rely on the correct
// resolution of rust_eh_personality which is loosely defined in panic_abort.
//
// Weakly resolve the symbol for android_set_abort_message. This function is only available
// for API >= 21.
pub(crate) unsafe fn zkvm_set_abort_message(payload: &mut dyn BoxMeUp) {
    let payload = payload.get();
    let msg = match payload.downcast_ref::<&'static str>() {
        Some(msg) => msg.as_bytes(),
        None => match payload.downcast_ref::<String>() {
            Some(msg) => msg.as_bytes(),
            None => &[],
        },
    };
    if msg.is_empty() {
        return;
    }

    extern "C" {
        fn sys_panic(msg_ptr: *const u8, len: usize) -> !;
    }

    sys_panic(msg.as_ptr(), msg.len());
}
