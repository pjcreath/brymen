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

    PREFIX_NONE = ""
    PREFIX_KILO = "k"
    PREFIX_MEGA = "M"
    PREFIX_MILLI = "m"
    PREFIX_MICRO = "u"

    def __init__(self, prefix=PREFIX_NONE, timestamp=None):
        self.prefix = prefix
        if timestamp is None:
            timestamp = datetime.now()
        self.timestamp = timestamp

    @property
    def type(self):
        """Type of measurement

        Raises an exception if the subclass fails to define it
        """
        return self._type  # pylint: disable=E1101


class TemperatureMeasurement(Measurement):
    """Representation of temperature measurement

    :param unit: Unit of measurement, either UNIT_CELSIUS or UNIT_FAHRENHEIT
    :type unit: int
    :param value: Measured temperature or None if no probe is connected
    :type value: int
    """

    _type = "Temperature"

    UNIT_CELSIUS = "C"
    UNIT_FAHRENHEIT = "F"

    def __init__(self, unit, value, timestamp=None):
        if unit not in [self.UNIT_CELSIUS, self.UNIT_FAHRENHEIT]:
            raise ValueError(f"Unknown temperature unit: {unit}")
        self.unit = unit
        self.value = value

        super().__init__(timestamp=timestamp)

    def __str__(self):
        value_str = "--" if self.value is None else self.value
        unit_str = self.unit
        return f"{value_str}°{unit_str}"


class ResistanceMeasurement(Measurement):
    """Representation of resistance measurement

    :param value: Measured resistance or None if open loop
    :type value: float
    :param prefix: Metrix prefix of measurement
    :type prefix: int
    """

    _type = "Resistance"

    def __init__(self, value, prefix=Measurement.PREFIX_NONE, timestamp=None):
        self.value = value

        super().__init__(prefix, timestamp=timestamp)

    def __str__(self):
        if self.value is not None:
            return f"{self.value}{self.prefix}Ω"

        return "0.L"


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

    CURRENT_AC = 1
    CURRENT_DC = 2

    def __init__(self, value, current, prefix=Measurement.PREFIX_NONE, timestamp=None):
        self.unit = "V"
        self.value = value
        self.current = current

        super().__init__(prefix, timestamp=timestamp)

    def __str__(self):
        current_postfix = {self.CURRENT_AC: " [~]", self.CURRENT_DC: ""}
        return f"{self.value}{self.prefix}V{current_postfix[self.current]}"
