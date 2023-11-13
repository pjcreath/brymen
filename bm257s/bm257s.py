"""Serial interface library for brymen bm257s multimeters"""
import serial

import bm257s.package_parser as parser

from .package_reader import PackageReader

# def parse_lcd(lcd):
#    """Parse measurement information from received lcd display state
#
#    :param lcd: Current lcd display state
#    :type lcd: BM257sLCD
#
#    :return: Name of measurement quantity and measurement
#    :rtype: tuple
#    :raise RuntimeError: If lcd state seems invalid
#    """
#    # pylint: disable=R0912
#    # This method will get replaced soon
#
#    segments = lcd.segment_data()
#    symbols = set(lcd.symbols())
#
#    res_symbols = {BM257sLCD.SYMBOL_OHM, BM257sLCD.SYMBOL_k, BM257sLCD.SYMBOL_M}
#    vol_symbols = {BM257sLCD.SYMBOL_V, BM257sLCD.SYMBOL_AC, BM257sLCD.SYMBOL_DC}
#
#    if symbols == set():
#        temp_unit_mapping = {
#            "C": TemperatureMeasurement.UNIT_CELSIUS,
#            "F": TemperatureMeasurement.UNIT_FAHRENHEIT,
#        }
#        if segments.chars[3] in temp_unit_mapping:
#            if segments.string_value(0, 2) == "---":
#                value = None
#            else:
#                value = segments.int_value(0, 2)
#                if value is None:
#                    raise RuntimeError("Cannot parse temperature value")
#
#            return (
#                Measurement.TEMPERATURE,
#                TemperatureMeasurement(
#                    unit=temp_unit_mapping[segments.chars[3]], value=value
#                ),
#            )
#
#    elif BM257sLCD.SYMBOL_OHM in symbols and symbols.issubset(res_symbols):
#        if segments.string_value() == " 0.L ":
#           return (Measurement.RESISTANCE, ResistanceMeasurement(value=None))
#
#        value = segments.float_value()
#
#        if BM257sLCD.SYMBOL_k in symbols:
#            prefix = Measurement.PREFIX_KILO
#        elif BM257sLCD.SYMBOL_M in symbols:
#            prefix = Measurement.PREFIX_MEGA
#        else:
#            prefix = Measurement.PREFIX_NONE
#
#        if value is not None:
#            return (
#               Measurement.RESISTANCE,
#               ResistanceMeasurement(value=value, prefix=prefix),
#           )
#
#    elif BM257sLCD.SYMBOL_V in symbols and symbols.issubset(vol_symbols):
#        value = segments.float_value()
#
#        if BM257sLCD.SYMBOL_AC in symbols:
#            current = VoltageMeasurement.CURRENT_AC
#        elif BM257sLCD.SYMBOL_DC in symbols:
#            current = VoltageMeasurement.CURRENT_DC
#
#        return (Measurement.VOLTAGE, VoltageMeasurement(value=value, current=current))
#
#    raise RuntimeError("Cannot parse LCD configuration")


class BM257sSerialInterface:
    """Serial interface used to communicate with brymen bm257s multimeters

    :param port: Device name to use
    :type port: str
    :param read_timeout: Maximum timeout for waiting while reading
    :type read_timeout: float
    :raise RuntimeError: If opening port is not possible
    """

    def __init__(self, port="/dev/ttyUSB0", read_timeout=0.1, window=None, log=None):
        try:
            self._serial = serial.Serial(
                port,
                baudrate=9600,
                parity=serial.PARITY_NONE,
                bytesize=serial.EIGHTBITS,
                stopbits=serial.STOPBITS_ONE,
                timeout=read_timeout,
            )
        except serial.SerialException as ex:
            raise RuntimeError(f"Could not open port {port}", ex) from ex

        self.window = window
        self._package_reader = PackageReader(self._serial, window=window)
        self._log = log

    def start(self):
        """Start reading serial measurements

        Call this at most once before calling stop()
        """
        self._package_reader.start(log=self._log)

    def stop(self):
        """Stop reading serial measurements

        Call this only when you called start() before
        """
        self._package_reader.stop()

    def wait(self, timeout=None):
        """Block until a measurement is available

        :param timeout: Maximum time to wait, or None for unlimited
        :type timeout: float or None

        :return: True if data is read, False if waiting timed out
        :rtype: bool
        """
        return self._package_reader.wait_for_package(timeout)

    def read(self, clear=True):
        """Reads latest measurement from multimeter

        :param clear: Remove the measurement from the buffer (default)
        :type clear: bool
        :return: measurement or None
        :rtype: Measurement
        """
        pkg = self._package_reader.latest_package(clear)
        if pkg is None:
            return None

        return parser.parse_package(pkg)

    def read_all(self, clear=True):
        """Reads all measurements from the multimeter

        :param clear: whether to clear all trailing measurements upon read
        :type clear: bool

        :return: list of measurements or None
        :rtype: list(Measurement)
        """
        pkgs = self._package_reader.all_packages(clear=clear)
        if not pkgs:
            return None

        return parser.parse_package_list(pkgs, mode_change="truncate")

    def close(self):
        """Closes the used serial port"""
        if self._package_reader.is_running():
            self._package_reader.stop()

        self._serial.close()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self._package_reader.stop()
        self.close()
