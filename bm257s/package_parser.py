"""Parse package content to obtain measurement result"""

from .measurement import (
    CapacitanceMeasurement,
    CurrentMeasurement,
    Measurement,
    ResistanceMeasurement,
    TemperatureMeasurement,
    VoltageMeasurement,
)
from .package_reader import Symbol


def parse_voltage(pkg, prefix):
    """Parse voltage measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param prefix: Metric prefix of measurement
    :type prefix: str

    :return: Multimeter measurement type and measurement
    :rtype: VoltageMeasurement
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
    :rtype: CurrentMeasurement
    """
    value = pkg.segment_float()

    mapping = {
        Symbol.AC: CurrentMeasurement.COUPLING_AC,
        Symbol.DC: CurrentMeasurement.COUPLING_DC,
    }
    for symbol, coupling in mapping.items():
        if symbol in pkg.symbols:
            break
    else:
        raise ValueError("Unknown current type displayed")

    return CurrentMeasurement(
        display_value=value, coupling=coupling, prefix=prefix, timestamp=pkg.timestamp
    )


def parse_resistance(pkg, prefix):
    """Parse resistance measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param prefix: Metric prefix of measurement
    :type prefix: str

    :return: Multimeter measurement type and measurement
    :rtype: ResistanceMeasurement
    """
    raw_str = pkg.segment_string()
    if "0.L" in raw_str:
        value = None
    else:
        value = float(raw_str)
    return ResistanceMeasurement(
        display_value=value, prefix=prefix, timestamp=pkg.timestamp
    )


def parse_temperature(pkg, _unused_prefix):
    """Parse temperature measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param prefix: Metric prefix of measurement
    :type prefix: str

    :return: Multimeter measurement type and measurement
    :rtype: TemperatureMeasurement
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

    text = text[:-1]
    if text == "---":
        value = None
    else:
        value = int(text)
    return TemperatureMeasurement(
        unit=unit, display_value=value, timestamp=pkg.timestamp
    )


def parse_capacitance(pkg, prefix):
    """Parse capacitance measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param prefix: Metric prefix of measurement
    :type prefix: str

    :return: Multimeter measurement type and measurement
    :rtype: CapacitanceMeasurement
    """
    value = pkg.segment_float()
    return CapacitanceMeasurement(
        display_value=value, prefix=prefix, timestamp=pkg.timestamp
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
        Symbol.NANO: Measurement.PREFIX_NANO,
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
        Symbol.FARAD: parse_capacitance,
    }
    for symbol, fn in mapping.items():
        if symbol in pkg.symbols:
            break
    else:
        if pkg.symbols != set():
            raise RuntimeError("Cannot parse multimeter package configuration")
        fn = parse_temperature
    return fn(pkg, prefix)


def parse_package_list(pkgs, mode_change="exception"):
    """Parse a list of packages to obtain a list of multimeter measurements,
    making sure to return only measurements of the same thing.

    :param pkgs: List of packages to parse
    :type pkgs: list(bm257s.package_parser.Package)
    :param mode_change: Specifies how to respond if meter's mode changed
        and it started measuring something different within the list.
        "exception": Raise a RuntimeError (default)
        "truncate": Drop any older packets that don't match the most
            recent measurement.
        "ignore": Keep all the measurements. Note that measurement.average
            will raise an exception if they are not all the same unit.
    :param mode_change: str

    :return: List of Multimeter measurements
    :rtype: list(Measurement subclass)
    """
    valid_set = set(["exception", "truncate", "ignore"])
    if mode_change not in valid_set:
        raise RuntimeError(f"mode_change not one of {valid_set}")

    meas = []
    for p in pkgs:
        m = parse_package(p)
        if meas and m.unit != meas[-1].unit:
            if mode_change == "exception":
                raise RuntimeError(
                    f"Meter changed from reading {meas[-1].unit} to {m.unit}"
                )
            if mode_change == "truncate":
                # Drop any previous samples that measured something different
                meas = []
        meas.append(m)
    return meas
