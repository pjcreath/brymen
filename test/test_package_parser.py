"""Unit tests for package parser module"""
import unittest

import bm257s.package_parser as measure
import bm257s.package_reader as reader


class TestPackageParsers(unittest.TestCase):
    """Testcase for package parser unit tests"""

    READER_TIMEOUT = 0.1

    def test_measurement_parsers(self):
        """Test measurement parsing of packages"""
        for raw_package, (expected_type, expected_value) in SAMPLE_PACKAGES.items():
            pkg = reader.parse_package(bytes.fromhex(raw_package))
            measurement = measure.parse_package(pkg)
            parsed_type = measurement.type
            parsed_value = str(measurement)
            self.assertEqual(parsed_type, expected_type)
            self.assertEqual(parsed_value, expected_value)


SAMPLE_PACKAGES = {
    "02 1A 20 3C 47 50 6A 78 8F 9F A7 B0 C0 D0 E5": ("Voltage", "513.6V [~]"),
    "02 1c 20 3e 4b 5e 6b 7f 8b 9a ad b0 c0 d1 e5": ("Voltage", "0.02mV"),
    "02 1c 20 3e 4b 51 6a 74 8e 9c af b0 c0 d0 e5": ("Voltage", "0.149V"),
    "02 1c 20 3f 4b 5f 6b 7e 87 9e af b0 c0 d0 e5": ("Voltage", "-0.068V"),
    "02 10 20 3e 4b 5e 67 78 8a 9e a4 b0 c0 d0 e0": ("Temperature", "67°F"),
    "02 10 20 3e 4b 50 6a 7c 8f 9e a1 b0 c0 d0 e0": ("Temperature", "19°C"),
}
