import sys
from contextlib import contextmanager


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data):
        for s in self.streams:
            s.write(data)
            s.flush()
        return len(data)

    def flush(self):
        for s in self.streams:
            s.flush()

@contextmanager
def tee_stdout(file_path, mode="w", encoding="utf-8"):
    original_stdout = sys.stdout
    f = open(file_path, mode, encoding=encoding)
    sys.stdout = Tee(original_stdout, f)
    try:
        yield
    finally:
        sys.stdout = original_stdout
        f.close()
