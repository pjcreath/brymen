#!/usr/bin/env python3
"""Thread-safe rolling buffer implementation"""

import collections
import datetime
import threading


class Buffer:
    """Thread-safe buffer class to hold some number of recent samples

    It can unlimited, fixed-length, or time-limited (if the elements
    added have a datetime ".timestamp" attribute).

    The buffer also offers blocking via wait().
    """

    def __init__(self, count=1, window=None):
        """Called without parameters, the buffer will hold
        only the most recent sample.

        :param count: Maximum number of samples in the buffer (None=unlimited)
        :type count: int or None
        :param window: Maximum length of the buffer in seconds
            (optional, overrides count)
        :type window: float
        """
        if window:
            window = datetime.timedelta(seconds=window)
            count = None
        self._window = window
        self._deque = collections.deque(maxlen=count)
        self._lock = threading.Lock()
        self._nonempty = threading.Event()
        return

    def append(self, elem):
        """Append an element, expiring old samples (thread-safe)

        :param elem: element to add to the buffer
        :type elem: object (with .timeout attribute for a time-bound buffer)
        """
        with self._lock:
            self._deque.append(elem)
            self._nonempty.set()
            if not self._window:
                # The deque will automatically roll off entries if it
                # is fixed-size.
                return
            # Roll off old samples until we're below the time limit.
            while elem.timestamp - self._deque[0].timestamp > self._window:
                self._deque.popleft()
        return

    def empty(self):
        """Return True if the buffer is empty (thread-safe, non-blocking)"""
        return self._nonempty.is_set() is False

    def clear(self):
        """Clear the buffer (thread-safe)"""
        with self._lock:
            self._clear()

    def _clear(self):
        """Clear the deque and barrier (internal, only use within a lock)"""
        self._deque.clear()
        self._nonempty.clear()

    def wait(self, timeout):
        """Wait until data is in the buffer (thread-safe)

        :param timeout: Maximum time to wait in seconds
        :type timeout: float

        :return: Whether data was in the buffer during the given time
        :rtype: bool
        """
        return self._nonempty.wait(timeout=timeout)

    def read_latest(self, clear=False):
        """Read the latest element in the buffer (thread-safe)

        :param: Clear the buffer after reading (default=False)
        :type: bool

        :raises: IndexError if empty
        :return: The item most recently added to the buffer
        :rtype: object
        """
        with self._lock:
            result = self._deque[-1]
            if clear:
                self._clear()
        return result

    def read_all(self, clear=True):
        """Read all elements in the buffer, clear it, and return
        the elements in a list (thread-safe)

        :param: Clear the buffer after reading (default=True)
        :type: bool

        :return: All items in the buffer (if any)
        :rtype: list(object)
        """
        with self._lock:
            # Convert the deque into a list.
            results = [None] * len(self._deque)
            for i, elem in enumerate(self._deque):
                results[i] = elem
            if clear:
                self._clear()
        return results
