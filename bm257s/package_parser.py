"""Parse package content to obtain measurement result"""

from .measurement import Measurement, TemperatureMeasurement, VoltageMeasurement
from .package_reader import Symbol


def parse_voltage(pkg, prefix):
    """Parse voltage measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param prefix: Metric prefix of measurement
    :type prefix: str

    :return: Multimeter measurement type and measurement
    :rtype: tuple
    """
    value = pkg.segment_float()

    mapping = {
        Symbol.AC: VoltageMeasurement.CURRENT_AC,
        Symbol.DC: VoltageMeasurement.CURRENT_DC,
    }
    for symbol, current in mapping.items():
        if symbol in pkg.symbols:
            break
    else:
        raise ValueError("Unknown voltage type displayed")

    return VoltageMeasurement(
        display_value=value, current=current, prefix=prefix, timestamp=pkg.timestamp
    )


def parse_current(pkg, prefix):
    """Parse current measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param prefix: Metric prefix of measurement
    :type prefix: str

    :return: Multimeter measurement type and measurement
    :rtype: tuple
    """
    raise NotImplementedError("Type of measurement is not yet supported")


def parse_resistance(pkg, prefix):
    """Parse resistance measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param prefix: Metric prefix of measurement
    :type prefix: str

    :return: Multimeter measurement type and measurement
    :rtype: tuple
    """
    raise NotImplementedError("Type of measurement is not yet supported")


def parse_temperature(pkg, _unused_prefix):
    """Parse temperature measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param prefix: Metric prefix of measurement
    :type prefix: str

    :return: Multimeter measurement type and measurement
    :rtype: tuple
    """
    text = pkg.segment_string()

    unit = text[-1]
    mapping = {
        "F": TemperatureMeasurement.UNIT_FAHRENHEIT,
        "C": TemperatureMeasurement.UNIT_CELSIUS,
    }
    try:
        unit = mapping[unit]
    except KeyError as e:
        raise ValueError(f"Unknown temperature: {text}") from e

    value = int(text[:-1])
    return TemperatureMeasurement(
        unit=unit, display_value=value, timestamp=pkg.timestamp
    )


def parse_prefix(pkg):
    """Parse metrix prefix of measurement

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package

    :return: Prefix shown in measurement
    :rtype: str
    """
    mapping = {
        Symbol.KILO: Measurement.PREFIX_KILO,
        Symbol.MEGA: Measurement.PREFIX_MEGA,
        Symbol.MILLI: Measurement.PREFIX_MILLI,
        Symbol.MICRO: Measurement.PREFIX_MICRO,
    }
    for symbol, prefix in mapping.items():
        if symbol in pkg.symbols:
            break
    else:
        prefix = Measurement.PREFIX_NONE
    return prefix


def parse_package(pkg):
    """Parse package to obtain multimeter measurement

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package

    :return: Multimeter measurement
    :rtype: Measurement subclass
    """
    prefix = parse_prefix(pkg)
    mapping = {
        Symbol.VOLT: parse_voltage,
        Symbol.AMPERE: parse_current,
        Symbol.OHM: parse_resistance,
    }
    for symbol, fn in mapping.items():
        if symbol in pkg.symbols:
            break
    else:
        if pkg.symbols != set():
            raise RuntimeError("Cannot parse multimeter package configuration")
        fn = parse_temperature
    return fn(pkg, prefix)
