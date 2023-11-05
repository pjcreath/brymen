"""Representation of measurements taken by bm257s multimeter"""
# pylint: disable=R0903
# Remove this once usage becomes clearer
import copy
import statistics
from datetime import datetime


def average(measurements):
    """Combine a list of measurements into a single composite measurement
    whose value is the average of all the measurements

    :return: measurement with an extra .values attribute containing all
        of the numeric values in the set of measurements
    :rtype: Measurement subclass (or None)
    """
    if not measurements:
        return None
    meas = copy.copy(measurements[-1])  # Use the latest timestamp
    values = []
    for m in measurements:
        if m.unit != meas.unit:
            raise ValueError("Measurement unit changed while monitoring!")
        values.append(m.value)
    meas.value = statistics.mean(values)
    meas.values = values
    return meas


class Measurement:
    """Generic measurement representation

    :param prefix: Metric prefix of measurement
    :type prefix: str
    """

    PRECISION = 4  # Other multimeters might have greater display precision
    PREFIX_MULTIPLIERS = {
        "": 1.0,
        "k": 1000.0,
        "M": 1000000.0,
        "m": 0.001,
        "u": 0.000001,
    }
    PREFIX_NONE = ""
    PREFIX_KILO = "k"
    PREFIX_MEGA = "M"
    PREFIX_MILLI = "m"
    PREFIX_MICRO = "u"
    unit = None  # should be overridden by all subclasses

    def __init__(self, display_value, prefix=PREFIX_NONE, timestamp=None):
        self.prefix = prefix
        self.display_unit = f"{self.prefix}{self.unit}"
        self.display_value = display_value
        if display_value is None:
            self._value = None
        else:
            self._value = display_value * self.PREFIX_MULTIPLIERS[self.prefix]
        if timestamp is None:
            timestamp = datetime.now()
        self.timestamp = timestamp

    @property
    def type(self):
        """Type of measurement

        Raises an exception if the subclass fails to define it
        """
        return self._type  # pylint: disable=E1101

    @property
    def value(self):
        """Value of measurement"""
        return self._value

    @value.setter
    def value(self, value):
        """Update display_value when value is updated"""
        self._value = value
        if value is None:
            self.display_value = None
        else:
            display_value = value / self.PREFIX_MULTIPLIERS[self.prefix]
            self.display_value = round(display_value, self.PRECISION)
        return

    def __str__(self):
        return f"{self.display_value}{self.display_unit}"


class TemperatureMeasurement(Measurement):
    """Representation of temperature measurement

    :param unit: Unit of measurement, either UNIT_CELSIUS or UNIT_FAHRENHEIT
    :type unit: int
    :param display_value: Measured temperature or None if no probe is connected
    :type value: int
    """

    _type = "Temperature"

    UNIT_CELSIUS = "C"
    UNIT_FAHRENHEIT = "F"

    def __init__(self, unit, display_value, timestamp=None):
        if unit not in [self.UNIT_CELSIUS, self.UNIT_FAHRENHEIT]:
            raise ValueError(f"Unknown temperature unit: {unit}")
        self.unit = unit

        super().__init__(display_value, timestamp=timestamp)
        self.display_unit = f"°{self.unit}"
        if display_value is None:
            self.display_value = "--"
            self.display_unit = ""
        return


class ResistanceMeasurement(Measurement):
    """Representation of resistance measurement

    :param value: Measured resistance or None if open loop
    :type value: float
    :param prefix: Metrix prefix of measurement
    :type prefix: int
    """

    _type = "Resistance"
    unit = "Ω"

    def __init__(self, display_value, prefix=Measurement.PREFIX_NONE, timestamp=None):
        super().__init__(display_value, prefix, timestamp=timestamp)
        if display_value is None:
            self.display_value = "0.L"
            self.display_unit = ""
        return


class VoltageMeasurement(Measurement):
    """Representation of voltage measurement

    :param value: Measured voltage
    :type value: float
    :param current: Type of current measured
    :type current: int
    :param prefix: Metrix prefix of measurement
    :type prefix: int
    """

    _type = "Voltage"
    unit = "V"

    CURRENT_AC = 1
    CURRENT_DC = 2

    def __init__(
        self, display_value, current, prefix=Measurement.PREFIX_NONE, timestamp=None
    ):
        self.current = current
        super().__init__(display_value, prefix=prefix, timestamp=timestamp)
        return

    def __str__(self):
        current_postfix = {self.CURRENT_AC: " [~]", self.CURRENT_DC: ""}
        return super().__str__() + current_postfix[self.current]
