"""Parse package content to obtain measurement result"""

from .measurement import (
    CapacitanceMeasurement,
    CurrentMeasurement,
    DiodeTest,
    Measurement,
    ResistanceMeasurement,
    TemperatureMeasurement,
    TextDisplay,
    VoltageMeasurement,
)
from .package_reader import Symbol


def parse_text(pkg, properties):
    """Parse text display from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param properties: Properties common to any measurements
    :type properties: dict

    :return: Measurement subclass whose display_value is the text
    :rtype: TextDisplay
    """
    raw_str = pkg.segment_string()
    return TextDisplay(raw_str, properties)


def parse_voltage(pkg, properties):
    """Parse voltage measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param properties: Properties common to any measurements
    :type properties: dict

    :return: Multimeter measurement
    :rtype: VoltageMeasurement
    """
    raw_str = pkg.segment_string()

    if ".0L" in raw_str:
        # Only seen in diode test
        value = None
    else:
        value = float(raw_str)

    mapping = {
        Symbol.AC: VoltageMeasurement.COUPLING_AC,
        Symbol.DC: VoltageMeasurement.COUPLING_DC,
    }
    for symbol, coupling in mapping.items():
        if symbol in pkg.symbols:
            break
    else:
        return DiodeTest(value, properties)

    if value is None:
        raise ValueError(f"unexpected voltage display: '{raw_str}'")
    return VoltageMeasurement(value, coupling, properties)


def parse_current(pkg, properties):
    """Parse current measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param properties: Properties common to any measurements
    :type properties: dict

    :return: Multimeter measurement
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

    return CurrentMeasurement(value, coupling, properties)


def parse_resistance(pkg, properties):
    """Parse resistance measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param properties: Properties common to any measurements
    :type properties: dict

    :return: Multimeter measurement
    :rtype: ResistanceMeasurement
    """
    raw_str = pkg.segment_string()
    if "0.L" in raw_str:
        value = None
    elif "0L." in raw_str:  # continuity test mode
        value = None
    else:
        value = float(raw_str)
    return ResistanceMeasurement(value, properties)


def parse_temperature(pkg, properties):
    """Parse temperature measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param properties: Properties common to any measurements
    :type properties: dict

    :return: Multimeter measurement
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
    except KeyError:
        # When the thermocouple is attached while monitoring,
        # there are sometimes transient 4-digit readings.
        unit = "?"
        text = "---?"

    text = text[:-1]
    if text == "---":
        value = None
    else:
        value = int(text)
    return TemperatureMeasurement(value, unit, properties)


def parse_capacitance(pkg, properties):
    """Parse capacitance measurement from package

    :param pkg: Package to parse
    :type pkg: bm257s.package_parser.Package
    :param properties: Properties common to any measurements
    :type properties: dict

    :return: Multimeter measurement
    :rtype: CapacitanceMeasurement
    """
    value = pkg.segment_float()
    return CapacitanceMeasurement(value, properties)


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
    properties = {
        "prefix": parse_prefix(pkg),
        "timestamp": pkg.timestamp,
    }
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
        if pkg.symbols == set([Symbol.LOZ]):
            fn = parse_text
        elif pkg.symbols == set():
            fn = parse_temperature
        else:
            raise RuntimeError(
                f"Cannot parse multimeter package configuration: {pkg.symbols}"
            )
    return fn(pkg, properties)


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
