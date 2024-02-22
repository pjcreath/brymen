"""Unit tests for package parser module"""

import unittest

import brymen.measurement as measure
import brymen.package_parser as parser
import brymen.package_reader as reader


class TestPackageParsers(unittest.TestCase):
    """Testcase for package parser unit tests"""

    READER_TIMEOUT = 0.1

    def test_measurement_parsers(self):
        """Test measurement parsing of packages"""
        for raw_package, (expected_type, expected_value) in SAMPLE_PACKAGES.items():
            pkg = reader.parse_package(bytes.fromhex(raw_package))
            measurement = parser.parse_package(pkg)
            parsed_type = measurement.type
            parsed_value = str(measurement)
            self.assertEqual(parsed_type, expected_type)
            self.assertEqual(parsed_value, expected_value)

    def test_measurement_list_reset(self):
        """Test handling when the measurement unit changes"""
        transition_packages = {
            (
                "02 1A 20 3C 47 50 6A 78 8F 9F A7 B0 C0 D0 E5",  # 513.6Vrms
                "02 1c 20 3e 4b 5e 6b 7f 8b 9a ad b0 c0 d1 e5",  # 0.02mV
                "02 1c 20 3e 4b 51 6a 74 8e 9c af b0 c0 d0 e5",  # 0.149V
            ): 2,  # only the last two are the same units
            (
                "02 1c 20 3f 4b 5f 6b 7e 87 9e af b0 c0 d0 e5",  # -0.068V
                "02 10 20 3e 4b 50 6a 7c 8f 9e a1 b0 c0 d0 e0",  # 19C
                "02 10 20 3e 4b 5e 67 78 8a 9e a4 b0 c0 d0 e0",  # 67F
            ): 1,  # only the last one is the same unit
        }

        for sequences, result in transition_packages.items():
            pkgs = [reader.parse_package(bytes.fromhex(s)) for s in sequences]

            # Make sure the default exception is raised
            self.assertRaises(
                RuntimeError,
                lambda _: parser.parse_package_list(pkgs),  # pylint: disable=W0640
                "Didn't raise an exception as expected",
            )

            # Make sure the list was truncated
            meas = parser.parse_package_list(pkgs, mode_change="truncate")
            self.assertEqual(
                len(meas),
                result,
                "Measurements of differing units were returned",
            )

            # Make sure "ignore" works as well
            meas = parser.parse_package_list(pkgs, mode_change="ignore")
            self.assertEqual(
                len(meas),
                len(pkgs),
                "Measurements were truncated",
            )

    def test_invalid_readings(self):
        """Test handling of invalid readings

        Make sure invalid readings get passed through parsing and
        ignored by measurement.average()
        """
        sequences = (
            "02 10 20 3e 4b 5e 67 78 8a 9e a4 b0 c0 d0 e0",  # 67F
            "02 10 20 30 44 50 64 70 84 9e a4 b0 c0 d0 e0",  # ---F"
        )
        # Nothing should be dropped by the parser
        pkgs = [reader.parse_package(bytes.fromhex(s)) for s in sequences]
        meas = parser.parse_package_list(pkgs)
        self.assertEqual(
            len(meas),
            len(pkgs),
            "Blank measurement was considered to be a different unit",
        )
        # The average measurement should equal the only valid measurement
        avg = measure.average(meas)
        self.assertEqual(avg.value, meas[0].value)
        self.assertEqual(len(avg.values), 1)

        return

    def test_optional_properties(self):
        """Test detection of optional properties"""
        sole_properties = ["relative", "recording", "min", "max"]
        sole_packages = {
            "02 1A 20 3C 47 50 6A 78 8F 9F A7 B0 C0 D0 E5": None,
            "02 11 20 3e 4b 5e 6b 7e 8b 9e a4 b0 c0 d0 e0": "relative",
            "02 18 20 3e 4b 5e 67 7c 8f 9e a4 b0 c0 d8 e8": "recording",
            "02 18 20 3e 4b 5e 67 78 8a 9e a4 b0 c0 d0 e8": "min",
            "02 18 20 3e 4b 58 6a 7e 8b 9e a4 b0 c0 d8 e0": "max",
        }
        for raw_package, expected_property in sole_packages.items():
            pkg = reader.parse_package(bytes.fromhex(raw_package))
            measurement = parser.parse_package(pkg)
            for prop in sole_properties:
                expected_value = False
                if prop == expected_property:
                    expected_value = True
                self.assertEqual(measurement.properties[prop], expected_value)
            self.assertEqual(measurement.properties["crest"], False)

        crest_package = "02 12 20 3a 4d 59 6f 7e 8b 9c af b0 c8 d8 e4"  # max
        pkg = reader.parse_package(bytes.fromhex(crest_package))
        measurement = parser.parse_package(pkg)
        self.assertEqual(measurement.properties["crest"], True)
        return


SAMPLE_PACKAGES = {
    "02 1A 20 3C 47 50 6A 78 8F 9F A7 B0 C0 D0 E5": ("Voltage", "513.6V [~]"),
    "02 1c 20 3e 4b 5e 6b 7f 8b 9a ad b0 c0 d1 e5": ("Voltage", "0.02mV"),
    "02 1c 20 3e 4b 51 6a 74 8e 9c af b0 c0 d0 e5": ("Voltage", "0.149V"),
    "02 1c 20 3f 4b 5f 6b 7e 87 9e af b0 c0 d0 e5": ("Voltage", "-0.068V"),
    "02 10 20 3e 4b 5e 67 78 8a 9e a4 b0 c0 d0 e0": ("Temperature", "67°F"),
    "02 10 20 3e 4b 50 6a 7c 8f 9e a1 b0 c0 d0 e0": ("Temperature", "19°C"),
    "02 10 20 30 44 50 64 70 84 9e a4 b0 c0 d0 e0": ("Temperature", "---°F"),
    "02 10 20 3a 4d 5e 6b 7e 8b 9a ad b0 c0 d0 e0": ("Temperature", "---°?"),  # noise
    "02 18 20 3e 4b 50 6a 7e 8b 9b ad b0 c4 d0 e1": ("Resistance", "10.2Ω"),
    "02 18 20 30 4a 5f 6b 7e 8b 9a ad b1 c4 d0 e1": ("Resistance", "1.002kΩ"),
    "02 18 20 3e 4b 5e 67 71 8a 90 aa b1 c4 d0 e1": ("Resistance", "6.11kΩ"),
    "02 18 20 3a 4d 5d 67 7e 8b 9c a7 b2 c4 d0 e1": ("Resistance", "2.505MΩ"),
    "02 18 20 30 40 5e 6b 77 81 90 a0 b2 c4 d0 e1": ("Resistance", "OL"),
    "02 10 28 30 40 5e 6b 76 81 91 a0 b0 c4 d0 e1": ("Resistance", "OL"),  # continuity
    "02 18 20 3e 4b 5e 6b 71 8a 9a ad b0 c1 d4 e0": ("Capacitance", "0.12nF"),
    "02 18 20 30 4a 5c 6f 7e 8b 9d a7 b0 c1 d4 e0": ("Capacitance", "190.5nF"),
    "02 18 20 30 4a 5b 6d 74 8e 90 aa b0 c0 d6 e0": ("Capacitance", "1.241uF"),
    "02 18 20 3a 4d 58 6a 7d 8f 9c a7 b0 c0 d6 e0": ("Capacitance", "27.95uF"),
    "02 1c 20 3e 4b 5a 6d 78 8a 95 ae b0 c0 d2 e3": ("Current", "27.4uA"),
    "02 14 20 30 4a 5e 6b 7a 8d 9e af b0 c8 da e2": ("Current", "1028.0uA"),
    "02 14 20 3e 4b 50 6a 7a 8d 91 aa b0 c8 d9 e2": ("Current", "12.1mA"),
    "02 14 20 3e 4b 58 6a 79 8a 9e af b0 c8 d8 e2": ("Current", "7.78A"),
    "02 1a 20 3e 4b 5f 6b 7e 8b 9c a7 b8 c0 d0 e3": ("Current", "0.005A [~]"),
    "02 10 20 3f 4b 5f 6b 7e 8b 9e ab b0 c0 d0 e4": ("Diode", "-0.0V"),
    "02 10 20 30 40 5f 6b 76 81 90 a0 b0 c0 d0 e4": ("Diode", "OL"),
    "02 18 20 3e 47 5e 6b 7f 8b 9e ab b0 c2 d0 e1": ("Frequency", "60.0Hz"),
    "02 18 20 34 4e 5c 6f 7d 8f 9e af b1 c2 d0 e1": ("Frequency", "49.98kHz"),
    "02 18 20 30 4a 5f 6b 7e 8b 9e ab b2 c2 d0 e1": ("Frequency", "1.0MHz"),
    "02 10 22 3e 4e 52 63 76 85 92 a7 b0 c0 d0 e0": ("Auto", ""),
    "02 10 20 30 40 5e 65 7f 84 91 a0 b0 c0 d0 e0": ("Electric Field", "0.0V"),
    "02 10 20 31 40 50 60 70 80 90 a0 b0 c0 d0 e0": ("Electric Field", "20.0V"),
    "02 10 20 31 44 50 64 70 84 90 a4 b0 c0 d0 e0": ("Electric Field", "440.0V"),
}
