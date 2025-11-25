from datetime import datetime

class Timer:
    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = datetime.now()
        self.end_time = None

    def stop(self):
        self.end_time = datetime.now()

    def elapsed(self):
        if self.start_time is None:
            return "Timer has not been started."
        if self.end_time is None:
            return "Timer has not been stopped."
        elapsed_time = self.end_time - self.start_time
        return f"Elapsed time: {elapsed_time}"