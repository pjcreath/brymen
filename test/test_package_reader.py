"""Unit tests for package reader module"""

import unittest

import bm257s.measurement
import bm257s.package_parser
from bm257s.package_reader import PackageReader, TruncatedPackage, parse_package

from .helpers.mock_data_reader import MockDataReader
from .helpers.raw_package_helpers import (
    EXAMPLE_RAW_PKG,
    change_byte_index,
    check_example_pkg,
)


class TestPackageReader(unittest.TestCase):
    """Testcase for package reader unit tests"""

    READER_TIMEOUT = 0.1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls):
        cls._mock_reader = MockDataReader()
        cls._pkg_reader = PackageReader(cls._mock_reader, window=0.5)

    def setUp(self):
        """Set up package reader to get tested"""
        super().setUp()

        self.assertTrue(
            self._mock_reader.all_data_used(),
            msg="Mock data should be empty before test start",
        )

        self._pkg_reader.start()

    def tearDown(self):
        """Stop package reader"""
        super().tearDown()

        self._pkg_reader.stop()
        self.assertTrue(
            self._mock_reader.all_data_used(),
            msg="Mock data should be empty after test end",
        )

    def test_reader_restart(self):
        """Test restart behavior of package reader"""
        self._mock_reader.set_next_data(EXAMPLE_RAW_PKG)
        self.assertTrue(
            self._pkg_reader.wait_for_package(self.READER_TIMEOUT),
            msg="Reader should read package from input",
        )
        self.assertTrue(
            self._mock_reader.all_data_used(),
            "Reader should read all input data to get a package",
        )
        self.assertTrue(
            self._pkg_reader.is_running(), "Reader should normally be running"
        )

        # Stop reader
        self._pkg_reader.stop()
        self.assertFalse(
            self._pkg_reader.is_running(), "Reader should not be running after stop"
        )

        self._pkg_reader.start()
        self.assertTrue(
            self._pkg_reader.is_running(), "Reader should be running again after start"
        )

        # Should not keep any package lying around
        self.assertIsNone(
            self._pkg_reader.next_package(), msg="Restart should clear read packages"
        )

        # But should read new packages again
        self._mock_reader.set_next_data(EXAMPLE_RAW_PKG)
        self.assertTrue(
            self._pkg_reader.wait_for_package(self.READER_TIMEOUT),
            msg="Package reader reads new package after restart",
        )
        pkg = self._pkg_reader.next_package()
        self.assertIsNotNone(
            pkg, msg="Successfull waiting after reastart should yield a package"
        )
        check_example_pkg(self, pkg)

    def test_example_package(self):
        """Test parsing with 'spec'-provided example package"""
        self._mock_reader.set_next_data(EXAMPLE_RAW_PKG)
        self.assertTrue(
            self._pkg_reader.wait_for_package(self.READER_TIMEOUT),
            "Read package data from raw data reader",
        )
        pkg = self._pkg_reader.next_package()
        self.assertIsNotNone(pkg, "Package could get parsed fully")
        self.assertTrue(self._mock_reader.all_data_used)

        check_example_pkg(self, pkg)

    def test_misaligned_package(self):
        """Test alignment handling of package parser"""
        misaligned_data = {
            1: (EXAMPLE_RAW_PKG[14:15] + EXAMPLE_RAW_PKG),
            9: (EXAMPLE_RAW_PKG[9:15] + EXAMPLE_RAW_PKG),
            14: (EXAMPLE_RAW_PKG[1:15] + EXAMPLE_RAW_PKG),
        }

        for misalignment, data in misaligned_data.items():
            self.assertTrue(
                self._mock_reader.all_data_used,
                "Mock data should be empty before test start",
            )

            self._mock_reader.set_next_data(data)
            self.assertTrue(
                self._pkg_reader.wait_for_package(self.READER_TIMEOUT),
                f"Read package from raw data reader (misaligned by {misalignment})",
            )
            pkg = self._pkg_reader.next_package()
            self.assertIsNotNone(
                pkg, f"Package could not get parsed (misaligned by {misalignment})"
            )
            self.assertTrue(
                self._mock_reader.all_data_used,
                msg="Did not read all data from package (misaligned by "
                f"{misalignment})",
            )

            check_example_pkg(self, pkg)

    def test_truncated_package(self):
        """Test handling of truncated packages"""
        truncated_data = {
            1: (EXAMPLE_RAW_PKG[:1] + EXAMPLE_RAW_PKG),
            9: (EXAMPLE_RAW_PKG[:9] + EXAMPLE_RAW_PKG),
            14: (EXAMPLE_RAW_PKG[:14] + EXAMPLE_RAW_PKG),
        }

        for length, data in truncated_data.items():
            self.assertTrue(
                self._mock_reader.all_data_used,
                "Mock data should be empty before test start",
            )

            self._mock_reader.set_next_data(data)
            self.assertTrue(
                self._pkg_reader.wait_for_package(self.READER_TIMEOUT),
                f"Read package from raw data reader (truncated to {length})",
            )
            pkg = self._pkg_reader.next_package()
            self.assertIsNotNone(
                pkg, f"Package could not get parsed (truncated to {length})"
            )
            self.assertTrue(
                self._mock_reader.all_data_used,
                msg=f"Did not read all data from package (truncated to {length})",
            )

            check_example_pkg(self, pkg)

    def test_windowed_buffer(self):
        """Test handling of multiple packets in a windowed buffer"""
        self.assertTrue(
            self._mock_reader.all_data_used,
            "Mock data should be empty before test start",
        )

        test_packages = {
            "02 1c 20 3e 4b 5e 6b 7f 8b 9a ad b0 c0 d1 e5": 0.00002,  # 0.02 mV
            "02 1c 20 3e 4b 51 6a 74 8e 9c af b0 c0 d0 e5": 0.149,  # V
            "02 1c 20 3f 4b 5f 6b 7e 87 9e af b0 c0 d0 e5": -0.068,  # V
        }
        data = bytes.fromhex(" ".join(test_packages.keys()))

        self._mock_reader.set_next_data(data)
        self.assertTrue(
            self._pkg_reader.wait_for_package(self.READER_TIMEOUT),
            "Read packages from raw data reader (windowed)",
        )
        read_packages = self._pkg_reader.all_packages()
        self.assertTrue(
            self._mock_reader.all_data_used,
            "Did not read all data from packages (windowed)",
        )

        # Check list of packages
        self.assertEqual(
            len(read_packages),
            len(test_packages),
            "Packages could not get parsed (windowed)",
        )
        measurements = [bm257s.package_parser.parse_package(p) for p in read_packages]
        read_values = [m.value for m in measurements]
        test_values = list(test_packages.values())
        self.assertEqual(
            read_values,
            test_values,
            "Package values were not correctly parsed (windowed)",
        )

        # Check measurement.average()
        avg = bm257s.measurement.average(measurements)
        self.assertEqual(
            avg.values,
            test_values,
            "measurement.average() did not preserve all values",
        )
        self.assertAlmostEqual(
            avg.value,
            sum(test_values) / len(test_values),
            msg="measurement.average() did not average all values",
        )


class TestPackageParsing(unittest.TestCase):
    """Testcase for parsing of raw data packages"""

    def test_example_package(self):
        """Test parsing with 'spec'-provided example package"""
        # Example package should get parsed fine
        try:
            pkg = parse_package(EXAMPLE_RAW_PKG)
        except RuntimeError:
            self.fail("Falsely detected error in raw example package")

        check_example_pkg(self, pkg)

    def test_index_checking(self):
        """Test checking of byte indices in raw packages"""
        self.assertRaises(
            TruncatedPackage,
            lambda _: parse_package(change_byte_index(EXAMPLE_RAW_PKG, 0, 1)),
            "Detect incremented first byte index",
        )
        self.assertRaises(
            TruncatedPackage,
            lambda _: parse_package(change_byte_index(EXAMPLE_RAW_PKG, 14, 13)),
            "Detect decremented last byte index",
        )
        self.assertRaises(
            TruncatedPackage,
            lambda _: parse_package(change_byte_index(EXAMPLE_RAW_PKG, 7, 12)),
            "Detect changed byte index in middle of package",
        )
