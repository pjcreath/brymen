"""Unit tests for package parser module"""
import unittest

import bm257s.measurement as measure
import bm257s.package_parser as parser
import bm257s.package_reader as reader


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


SAMPLE_PACKAGES = {
    "02 1A 20 3C 47 50 6A 78 8F 9F A7 B0 C0 D0 E5": ("Voltage", "513.6V [~]"),
    "02 1c 20 3e 4b 5e 6b 7f 8b 9a ad b0 c0 d1 e5": ("Voltage", "0.02mV"),
    "02 1c 20 3e 4b 51 6a 74 8e 9c af b0 c0 d0 e5": ("Voltage", "0.149V"),
    "02 1c 20 3f 4b 5f 6b 7e 87 9e af b0 c0 d0 e5": ("Voltage", "-0.068V"),
    "02 10 20 3e 4b 5e 67 78 8a 9e a4 b0 c0 d0 e0": ("Temperature", "67°F"),
    "02 10 20 3e 4b 50 6a 7c 8f 9e a1 b0 c0 d0 e0": ("Temperature", "19°C"),
    "02 10 20 30 44 50 64 70 84 9e a4 b0 c0 d0 e0": ("Temperature", "---°F"),
}
