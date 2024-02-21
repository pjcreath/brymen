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
        if m.value is not None:
            values.append(m.value)
    if values:
        meas.value = statistics.mean(values)
    meas.values = values
    return meas


class Measurement:
    """Generic measurement representation

    :Primary Properties:
    :param type: Physical property being measured (in English)
    :type type: str
    :param unit: Base units for that property, e.g. V, A, etc.
    :type unit: str
    :param value: Measured value in those units
    :type value: float
    :param display_unit: Unit range being measured, as displayed on meter: mV, kΩ, etc.
    :type display_unit: str
    :param display_value: Measured value in those units, as displayed on the meter
    :type display_value: float or None

    :Additional Properties:
    :param timestamp: Time at which the measurement was received
    :type timestamp: datetime
    :param autorange: The meter is currently auto-ranging
    :type autorange: bool
    :param recording: The meter is currently recording min and max measurements
    :type recording: bool
    :param min: Measurement is a recorded minimum (normal or crest)
    :type min: bool
    :param max: Measurement is a recorded maximum (normal or crest)
    :type max: bool
    :param crest: Measurement is an instantaneous peak-hold measurement (CREST)
    :type crest: bool
    :param relative: Measurement is in relative zero mode (REL)
    :type relative: bool
    """

    PRECISION = 4  # Other multimeters might have greater display precision
    PREFIX_MULTIPLIERS = {
        "": 1.0,
        "k": 1.0e03,
        "M": 1.0e06,
        "m": 1.0e-03,
        "u": 1.0e-06,
        "n": 1.0e-09,
    }
    PREFIX_NONE = ""
    PREFIX_KILO = "k"
    PREFIX_MEGA = "M"
    PREFIX_MILLI = "m"
    PREFIX_MICRO = "u"
    PREFIX_NANO = "n"
    unit = None  # should be overridden by all subclasses

    def __init__(self, display_value, properties):
        """
        :param display_value: Value displayed on the meter
        :type display_value: float or None
        :param properties: Properties common to any measurements
        :type properties: dict

        :Recognized Properties:
        :param prefix: Metric prefix of the measurement units
        :type prefix: str
        :param timestamp: Time of the measurement
        :type timestamp: datetime
        """
        self.prefix = properties.pop("prefix", self.PREFIX_NONE)
        self.display_unit = f"{self.prefix}{self.unit}"
        self.display_value = display_value
        if display_value is None:
            self._value = None
        else:
            self._value = display_value * self.PREFIX_MULTIPLIERS[self.prefix]
        self.timestamp = properties.pop("timestamp", datetime.now())
        self.properties = properties  # save any remaining properties

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

    :param display_value: Measured temperature or None if no probe is connected
    :type value: int
    :param unit: Unit of measurement, either UNIT_CELSIUS or UNIT_FAHRENHEIT
    :type unit: str
    """

    _type = "Temperature"

    UNIT_CELSIUS = "C"
    UNIT_FAHRENHEIT = "F"

    def __init__(self, display_value, unit, properties):
        if unit not in [self.UNIT_CELSIUS, self.UNIT_FAHRENHEIT, "?"]:
            raise ValueError(f"Unknown temperature unit: {unit}")
        self.unit = unit

        super().__init__(display_value, properties)
        self.display_unit = f"°{self.unit}"
        if display_value is None:
            self.display_value = "---"
        return


class ResistanceMeasurement(Measurement):
    """Representation of resistance measurement

    :param value: Measured resistance or None if open loop
    :type value: float
    :param properties: Properties common to any measurements
    :type properties: dict
    """

    _type = "Resistance"
    unit = "Ω"

    def __init__(self, display_value, properties):
        super().__init__(display_value, properties)
        if display_value is None:
            self.display_value = "OL"
            self.display_unit = ""
        return


class DiodeTest(Measurement):
    """Representation of diode test

    :param value: Measured voltage
    :type value: float
    :param properties: Properties common to any measurements
    :type properties: dict
    """

    _type = "Diode"
    unit = "V"

    def __init__(self, display_value, properties):
        super().__init__(display_value, properties)
        if display_value is None:
            self.display_value = "OL"
            self.display_unit = ""
        return


class VoltageMeasurement(Measurement):
    """Representation of voltage measurement

    :param value: Measured voltage
    :type value: float
    :param coupoing: Type of voltage measured
    :type coupling: str
    :param properties: Properties common to any measurements
    :type properties: dict
    """

    _type = "Voltage"
    unit = "V"

    COUPLING_AC = "AC"
    COUPLING_DC = "DC"

    def __init__(self, display_value, coupling, properties):
        self.coupling = coupling
        super().__init__(display_value, properties)
        if self.coupling == self.COUPLING_AC:
            self.unit = "Vrms"
        return

    def __str__(self):
        coupling_postfix = {self.COUPLING_AC: " [~]", self.COUPLING_DC: ""}
        return super().__str__() + coupling_postfix[self.coupling]


class CurrentMeasurement(Measurement):
    """Representation of current measurement

    :param value: Measured current
    :type value: float
    :param coupling: Type of current measured
    :type coupling: str
    :param properties: Properties common to any measurements
    :type properties: dict
    """

    _type = "Current"
    unit = "A"

    COUPLING_AC = "AC"
    COUPLING_DC = "DC"

    def __init__(self, display_value, coupling, properties):
        self.coupling = coupling
        super().__init__(display_value, properties)
        if self.coupling == self.COUPLING_AC:
            self.unit = "Arms"
        return

    def __str__(self):
        postfix = {self.COUPLING_AC: " [~]", self.COUPLING_DC: ""}
        return super().__str__() + postfix[self.coupling]


class CapacitanceMeasurement(Measurement):
    """Representation of capacitance measurement

    :param display_value: Measured capacitance as displayed on meter
    :type value: float
    :param properties: Properties common to any measurements
    :type properties: dict
    """

    _type = "Capacitance"
    unit = "F"


class FrequencyMeasurement(Measurement):
    """Representation of frequency measurement

    :param display_value: Measured frequency as displayed on meter
    :type value: float
    :param properties: Properties common to any measurements
    :type properties: dict
    """

    _type = "Frequency"
    unit = "Hz"


class ElectricFieldMeasurement(Measurement):
    """Representation of electric field measurement

    :param display_value: Measured frequency as displayed on meter
    :type value: float
    :param properties: Properties common to any measurements
    :type properties: dict
    """

    _type = "Electric Field"
    unit = "V"


class TextDisplay(Measurement):
    """Representation of capacitance measurement

    :param display_value: Measured capacitance as displayed on meter
    :type value: float
    :param properties: Properties common to any measurements
    :type properties: dict
    """

    _type = "[Text]"
    unit = ""

    def __init__(self, display_value, properties):
        super().__init__(None, properties)
        self._type = display_value
        self.display_value = ""
        return
