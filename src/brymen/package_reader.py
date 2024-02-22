"""Read, organize and validate packages from data input"""

# Protocol documented in BM250-BM250s-6000-count-digital-multimeters-r1.pdf
# See PROTOCOLS.txt

# pylint: disable=R0913

import enum
import queue
import threading
from datetime import datetime

from .buffer import Buffer


class TruncatedPackage(Exception):
    """Exception raised when a truncated package is encountered."""

    def __init__(self, length):
        self.length = length


class Symbol(enum.Enum):
    """Enumeration of all LCD symbols"""

    AUTO = enum.auto()
    DC = enum.auto()
    AC = enum.auto()
    REL = enum.auto()
    BEEP = enum.auto()
    BATTERY = enum.auto()
    LOZ = enum.auto()
    BMINUS = enum.auto()
    HOLD = enum.auto()
    DBM = enum.auto()
    MEGA = enum.auto()
    KILO = enum.auto()
    CREST = enum.auto()
    OHM = enum.auto()
    HZ = enum.auto()
    NANO = enum.auto()
    MAX = enum.auto()
    FARAD = enum.auto()
    MICRO = enum.auto()
    MILLI = enum.auto()
    MIN = enum.auto()
    VOLT = enum.auto()
    AMPERE = enum.auto()
    SCALE = enum.auto()


class Package:
    """Represents a single 15-byte serial package

    :param segments: List of tuples of 7-segment display segment occupancies
    :type segments: list
    :param dots: List of dot occupancies
    :type dots: list
    :param minus: Occupancy of minus sign
    :type minus: bool
    :param symbols: Set of symbols currently shown
    :type symbol: set
    """

    def __init__(self, segments, dots, minus, symbols, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now()
        self.segments = segments
        self.dots = dots
        self.minus = minus
        self.symbols = symbols
        self.timestamp = timestamp

    def segment_character(self, pos):
        """Read character from segment display

        :param pos: Number of digit to read
        :type pos: int

        :return: Character shown by segment
        :rtype: str
        :raise RuntimeError: If the segment doesn't show a character
        """

        character_segments = {
            (True, True, True, True, True, True, False): "0",
            (False, True, True, False, False, False, False): "1",
            (True, True, False, True, True, False, True): "2",
            (True, True, True, True, False, False, True): "3",
            (False, True, True, False, False, True, True): "4",
            (True, False, True, True, False, True, True): "5",
            (True, False, True, True, True, True, True): "6",
            (True, True, True, False, False, False, False): "7",
            (True, True, True, True, True, True, True): "8",
            (True, True, True, True, False, True, True): "9",
            (True, False, False, True, True, True, False): "C",
            (True, False, False, False, True, True, True): "F",
            (False, False, False, False, False, False, True): "-",
            (False, False, False, False, False, False, False): " ",
            (False, False, False, True, True, True, False): "L",
            (True, True, True, False, True, True, True): "A",
            (False, False, True, True, True, False, False): "u",
            (False, False, False, True, True, True, True): "t",
            (False, False, True, True, True, False, True): "o",
            (True, False, False, True, True, True, True): "E",
        }

        if self.segments[pos] in character_segments:
            return character_segments[self.segments[pos]]

        raise RuntimeError(f"Cannot read character from segment {pos}")

    def segment_string(self, start_i=0, end_i=3, use_dots=True, use_minus=True):
        """Read segment string value from segment display

        :param start_i: First digit to consider
        :type start_i: int
        :param end_i: Last digit to consider
        :type end_i: int
        :param use_dots: Whether to include dots if present
        :type use_dots: bool
        :param use_minus: Whether to include minus if present
        :type use_minus: bool

        :return: String formed by segment display
        :rtype: str
        :raise RuntimeError: If the segment display contains invalid characters
        """
        if use_minus and self.minus:
            result = "-"
        else:
            result = ""

        # Go through first three segments so we can do chars + dots together
        for i in range(start_i, end_i):
            result += self.segment_character(i)

            if use_dots:
                result += "." if self.dots[i] else ""

        result += self.segment_character(end_i)

        return result

    def segment_float(self, start_i=0, end_i=3, use_minus=True):
        """Read segment float value from segment display

        :param start_i: First digit to consider
        :type start_i: int
        :param end_i: Last digit to consider
        :type end_i: int
        :param use_minus: Whether to include minus in evaluation
        :type use_minus: bool

        :return: Float number formed by segment display
        :rtype: float
        :raise RuntimeError: If the segment display doesn't show a float number
        """
        raw_str = self.segment_string(start_i, end_i, use_minus)

        try:
            return float(raw_str)
        except ValueError as ex:
            raise RuntimeError(
                "Cannot read float value from segment display", ex
            ) from ex


def parse_segment(data, pos):
    """Parses a single 7-segment digit from raw multimeter data

    :param data: Raw multimeter data, aligned to 15-byte boundary
    :type data: bytes
    :param pos: Number of segment to parse (numbered left to right)
    :type pos: int

    :return: 7-segment digit configuration
    :rtype: tuple
    """
    start_i = 3 + 2 * pos
    return (
        bool(data[start_i] & (1 << 3)),  # A
        bool(data[start_i + 1] & (1 << 3)),  # B
        bool(data[start_i + 1] & (1 << 1)),  # C
        bool(data[start_i + 1] & 1),  # D
        bool(data[start_i] & (1 << 1)),  # E
        bool(data[start_i] & (1 << 2)),  # F
        bool(data[start_i + 1] & (1 << 2)),  # G
    )


def parse_dot(data, pos):
    """Parses a single dot from raw multimeter data

    :param data: Raw multimeter data, aligned to 15-byte boundary
    :type data: bytes
    :param pos: Number of dot to parse (numbered left to right)
    :type pos: int

    :return: Whether dot is on
    :rtype: bool
    """
    return bool(data[5 + 2 * pos] & 1)


def parse_symbols(data):
    """Parses symbols from raw multimeter data

    :param data: Raw multimeter data, aligned to 15-byte boundary
    :type data: bytes

    :return: List of shown symbols
    :rtype: list
    """
    symbol_positions = {
        1: (Symbol.AUTO, Symbol.DC, Symbol.AC, Symbol.REL),
        2: (Symbol.BEEP, Symbol.BATTERY, Symbol.LOZ, Symbol.BMINUS),
        11: (Symbol.HOLD, Symbol.DBM, Symbol.MEGA, Symbol.KILO),
        12: (Symbol.CREST, Symbol.OHM, Symbol.HZ, Symbol.NANO),
        13: (Symbol.MAX, Symbol.FARAD, Symbol.MICRO, Symbol.MILLI),
        14: (Symbol.MIN, Symbol.VOLT, Symbol.AMPERE, Symbol.SCALE),
    }

    result = []
    # Go through all bytes
    for i in range(0, 15):
        # Skip segment display section
        if i in symbol_positions:
            # Go through symbol bits
            for j in range(0, 4):
                if data[i] & (1 << j):
                    result.append(symbol_positions[i][3 - j])

    return result


def parse_minus(data):
    """Parse minus sign from raw multimeter data

    :param data: Raw multimeter data, aligned to 15-byte boundary
    :type data: bytes

    :return: Whether minus is on
    :rtype: bool
    """
    return bool(data[3] & 1)


def parse_package(data):
    """Parses a package from raw multimeter data

    :param data: Raw multimeter data, aligned to 15-byte boundary
    :type data: bytes
    :raise RuntimeError: If package contains invalid data
    :raise TruncatedPackage: If the package is incomplete
    """
    # Check byte indices
    index_mask = ((1 << 5) - 1) << 4
    for i, d_i in enumerate(data):
        index_field = (d_i & index_mask) >> 4
        if index_field != i:
            raise TruncatedPackage(i)

    timestamp = datetime.now()
    segments = [parse_segment(data, i) for i in range(0, 4)]
    dots = [parse_dot(data, i) for i in range(0, 3)]
    minus = parse_minus(data)
    symbols = parse_symbols(data)
    return Package(segments, dots, minus, set(symbols), timestamp)


class PackageReader:
    """Read, organize and validate packages from data input

    :param reader: Input reader used
    :type reader: Class with reader.read(len) method
    """

    PKG_LEN = 15
    PKG_START = 0b00000010  # Start of first package byte

    def __init__(self, reader, window=None):
        self._reader = reader
        self._log = None
        self._exception = queue.Queue(maxsize=1)

        self._read_thread = threading.Thread(target=self._run)
        self._read_thread_stop = threading.Event()

        self._buffer = Buffer(window=window)

    def start(self, log=None):
        """Start reading packages in a seperate thread

        Call this at most once until you call stop().

        :param log: filepath at which to log incoming data (optional)
        """
        self._buffer.clear()
        if log:
            self._log = open(log, "w", encoding="utf-8")  # pylint: disable=R1732

        self._read_thread_stop.clear()
        self._read_thread.start()

    def stop(self):
        """Stop reading packages in seperate thread

        Only call this if you previously called start().
        """
        self._read_thread_stop.set()
        self._read_thread.join()
        if self._log:
            self._log.close()
            self._log = None

        self._read_thread = threading.Thread(target=self._run)

    def log(self, message, now=None):
        """Log the message to the logfile (if we're logging)."""
        if self._log:
            if now is None:
                now = datetime.now()
            self._log.write(f"{now} {message}\n")
            self._log.flush()
        return

    def is_running(self):
        """Check if the reader is currently running

        :return: Whether reader is currently running
        :rtype: bool
        """
        return self._read_thread.is_alive()

    def wait_for_package(self, timeout):
        """Wait until a new package is received

        :param timeout: Maximum time to wait in seconds
        :type timeout: float

        :return: Whether a package was received during the given time
        :rtype: bool
        """
        self._propagate_exceptions()
        return self._buffer.wait(timeout)

    def next_package(self):
        """Returns the last received package and removes it from storage

        :return: Last received packgae
        :rtype: Package
        """
        return self.latest_package(clear=True)

    def latest_package(self, clear=False):
        """Returns the last received package and optionally removes it from storage

        :return: Last received packgae
        :rtype: Package
        """
        self._propagate_exceptions()
        try:
            pkg = self._buffer.read_latest(clear=clear)
        except IndexError:
            pkg = None
        return pkg

    def all_packages(self, clear=True):
        """Returns all the packages currently in the buffer and
        optionally clears the buffer

        :param clear: whether to clear the buffer
        :type clear: bool

        :return: List of packages
        :rtype: list(Package)
        """
        self._propagate_exceptions()
        return self._buffer.read_all(clear=clear)

    def _propagate_exceptions(self):
        """Propagate any exceptions that cause the thread to stop"""
        try:
            e = self._exception.get(block=False)
        except queue.Empty:
            return
        raise e

    def _run(self):
        try:
            self._read_and_parse_packages()
        except Exception as e:  # pylint: disable=W0718
            # Pass any unhandled exceptions back to the main thread.
            self._exception.put(e, block=False)
        return

    def _read_and_parse_packages(self):
        data = bytes()

        while not self._read_thread_stop.is_set():
            # Read new data from reader
            length = self.PKG_LEN - len(data)
            if length > 0:
                data = data + self._reader.read(length)

            if len(data) > 0:
                # Find package start and perform alignment with it
                for i, byte in enumerate(data):
                    if byte == self.PKG_START:
                        data = data[i:]
                        break

                # Parse package
                if len(data) >= self.PKG_LEN:
                    try:
                        pkg = parse_package(data[: self.PKG_LEN])
                        self.log(data.hex(" "), pkg.timestamp)
                        data = data[self.PKG_LEN :]
                        self._buffer.append(pkg)
                    except TruncatedPackage as e:
                        data = data[e.length :]
        return
