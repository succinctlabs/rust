use crate::ffi::OsString;
use crate::fmt;

pub struct Args {
    i_forward: usize,
    i_back: usize,
    count: usize,
}

pub fn args() -> Args {
    Args { i_forward: 0, i_back: 0, count: 0 }
}

impl Args {
    /// Args::argv is currently not implemented.
    fn argv(_i: usize) -> OsString {
        panic!("Args::argv is currently not implemented");
    }
}

impl fmt::Debug for Args {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_list().finish()
    }
}

impl Iterator for Args {
    type Item = OsString;

    fn next(&mut self) -> Option<OsString> {
        if self.i_forward >= self.count - self.i_back {
            None
        } else {
            let arg = Self::argv(self.i_forward);
            self.i_forward += 1;
            Some(arg)
        }
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.count, Some(self.count))
    }
}

impl ExactSizeIterator for Args {
    fn len(&self) -> usize {
        self.count
    }
}

impl DoubleEndedIterator for Args {
    fn next_back(&mut self) -> Option<OsString> {
        if self.i_back >= self.count - self.i_forward {
            None
        } else {
            let arg = Self::argv(self.count - 1 - self.i_back);
            self.i_back += 1;
            Some(arg)
        }
    }
}
