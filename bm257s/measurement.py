"""Representation of measurements taken by bm257s multimeter"""
# pylint: disable=R0903
# Remove this once usage becomes clearer


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

    def __init__(self, prefix=PREFIX_NONE):
        self.prefix = prefix

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

    def __init__(self, unit, value):
        if unit not in [self.UNIT_CELSIUS, self.UNIT_FAHRENHEIT]:
            raise ValueError(f"Unknown temperature unit: {unit}")
        self.unit = unit
        self.value = value

        super().__init__()

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

    def __init__(self, value, prefix=Measurement.PREFIX_NONE):
        self.value = value

        super().__init__(prefix)

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

    def __init__(self, value, current, prefix=Measurement.PREFIX_NONE):
        self.value = value
        self.current = current

        super().__init__(prefix)

    def __str__(self):
        current_postfix = {self.CURRENT_AC: " [~]", self.CURRENT_DC: ""}
        return f"{self.value}{self.prefix}V{current_postfix[self.current]}"
