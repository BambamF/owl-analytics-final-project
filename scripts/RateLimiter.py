from collections import deque
import threading
import time
import logging

class RateLimiter:

    def __init__(self, max_calls: int, period: float):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
        self.lock = threading.Lock()
        self.wait_calls = 0

    def acquire(self):
        with self.lock:
            now = time.monotonic()
            while self.calls and self.calls[0] <= now - self.period:
                self.calls.popleft()

            if len(self.calls) >= self.max_calls:
                sleep_time = self.period - (now - self.calls[0])
                self.wait_calls += 1
                logging.info(f"Rate Limit Reached ({self.max_calls} req/{int(self.period)}s). "
                             f"Waiting {sleep_time:.2f}s before next request.")
            else:
                sleep_time = 0

            if sleep_time > 0:
                time.sleep(sleep_time)
            self.calls.append(time.monotonic())