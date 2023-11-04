"""Unit tests for thread-safe buffer module"""

import unittest
from datetime import datetime, timedelta

from bm257s.buffer import Buffer


class TestBuffer(unittest.TestCase):
    """Testcase for buffer unit tests"""

    TIMEOUT = 0.025
    FIXED_COUNT = 5

    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls._fixed_buffer = Buffer(count=self.FIXED_COUNT)
        cls._timed_buffer = Buffer(window=self.TIMEOUT)

    def setUp(self):
        """Set up package reader to get tested"""
        super().setUp()

        self.assertTrue(
            self._mock_reader.all_data_used(),
            msg="Mock data should be empty before test start",
        )

        self._pkg_reader.start()

    def tearDown(self):
        """Stop package reader"""
        super().tearDown()

        self._pkg_reader.stop()
        self.assertTrue(
            self._mock_reader.all_data_used(),
            msg="Mock data should be empty after test end",
        )
    '''

    def test_fixed_buffer(self):
        """Test a buffer with a fixed maximum number of entries"""
        count = self.FIXED_COUNT
        buffer = Buffer(count=count)
        self.assertTrue(buffer.empty())

        # Add twice as many entries as the buffer will hold.
        overflow = count * 2
        for i in range(0, overflow):
            buffer.append(i)
        self.assertFalse(buffer.empty())

        # Check the latest entry
        latest = buffer.read_latest()
        self.assertEqual(latest, overflow - 1)

        # Make sure it's repeatable
        self.assertEqual(latest, buffer.read_latest())

        # Check the full contents of the buffer
        buffered = buffer.read_all(clear=False)
        self.assertEqual(len(buffered), count)
        for i in range(0, count):
            self.assertEqual(buffered[i], count + i)

        # Make sure it's repeatable
        buffered2 = buffer.read_all()
        self.assertEqual(buffered, buffered2)
        return

    def test_timed_buffer(self):
        """Test a buffer with a time-limited set of entries"""
        window = self.TIMEOUT
        buffer = Buffer(window=window)
        self.assertTrue(buffer.empty())

        class _TimedItem:  # pylint: disable=R0903
            def __init__(self, value):
                self.timestamp = datetime.now()
                self.value = value

        # Add samples for twice as long as the maximum window
        window = timedelta(seconds=window)
        start = datetime.now()
        end = start + 2 * window
        i = 0
        while datetime.now() < end:
            buffer.append(_TimedItem(i))
            i += 1

        # Read and clear the buffer
        buffered = buffer.read_all()
        self.assertTrue(len(buffered) > 0)

        # Make sure that only samples within the window were kept
        span = buffered[-1].timestamp - buffered[0].timestamp
        self.assertTrue(span <= window, msg=f"{span} should be <= {window}")

        # Make sure that at least some samples were discarded
        self.assertTrue(buffered[0].value > 0)
        return

    def test_clearing(self):
        """Test explicit and implicit buffer clearing"""
        count = self.FIXED_COUNT
        buffer = Buffer(count=count)
        for i in range(0, count):
            buffer.append(i)

        # Confirm that read_latest doesn't clear by default
        latest = buffer.read_latest()
        self.assertFalse(buffer.empty())

        # Confirm that read_latest does clear when requested
        self.assertEqual(buffer.read_latest(clear=True), latest)
        self.assertTrue(buffer.empty())

        # Refill the buffer
        for i in range(0, count):
            buffer.append(i)

        # Confirm that read_all doeesn't clear when requested
        buffered = buffer.read_all(clear=False)
        self.assertFalse(buffer.empty())

        # Confirm that read_all does clear by defaut
        buffered2 = buffer.read_all()
        self.assertEqual(buffered, buffered2)
        self.assertTrue(buffer.empty())

        # Refill the buffer
        for i in range(0, count):
            buffer.append(i)

        # Test clear()
        self.assertFalse(buffer.empty())
        buffer.clear()
        self.assertTrue(buffer.empty())

        # Test exceptions when reading an empty buffer without blocking
        with self.assertRaises(IndexError):
            buffer.read_latest()

        return

    def test_wait(self):
        """Test blocking behavior of wait()"""
        count = self.FIXED_COUNT
        buffer = Buffer()
        for i in range(0, count):
            buffer.append(i)

        self.assertTrue(buffer.wait(self.TIMEOUT))
        buffer.clear()

        timeout = timedelta(seconds=self.TIMEOUT)
        start = datetime.now()
        self.assertFalse(buffer.wait(self.TIMEOUT))
        end = datetime.now()
        self.assertTrue(
            end - start >= timeout,
            msg="Waiting should time out when the buffer is empty",
        )

        return
