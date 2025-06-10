import unittest
from unittest import mock
import math
import datetime

# Attempt to import utils from the parent directory.
# This might need adjustment based on how tests are run (e.g., using python -m unittest)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

# Mock astral if not installed, or for consistent testing
try:
    from astral import LocationInfo
    from astral.sun import azimuth, elevation
except ImportError:
    # Mock astral objects and functions if not available
    class MockObserver:
        pass

    class MockLocationInfo:
        def __init__(self, latitude, longitude, timezone="UTC", elevation=0):
            self.observer = MockObserver()
            self.latitude = latitude
            self.longitude = longitude
            self.timezone = timezone
            self.elevation = elevation

    def mock_azimuth(observer, timestamp):
        return 180.0 # Example value

    def mock_elevation(observer, timestamp):
        return 45.0  # Example value

    utils.LocationInfo = MockLocationInfo
    utils.azimuth = mock_azimuth
    utils.elevation = mock_elevation


class TestUtils(unittest.TestCase):

    def test_compute_sun_vector(self):
        # Test with a known location and time
        # For this example, let's use a fixed time and location
        # Replace with actual known values if possible for more accurate testing
        lat = 51.5  # London latitude
        lon = -0.12  # London longitude

        # Mock datetime to a fixed point for reproducible tests
        fixed_datetime = datetime.datetime(2023, 10, 26, 12, 0, 0, tzinfo=datetime.timezone.utc)

        with mock.patch('datetime.datetime', wraps=datetime.datetime) as patched_datetime:
            patched_datetime.now.return_value = fixed_datetime

            # Expected values for London, 2023-10-26 12:00:00 UTC (approximate)
            # Azimuth ~180.3 deg, Elevation ~24.8 deg (from an online calculator)
            # These values will depend on the astral library's accuracy or the mock.
            # If using the mock astral above: az=180, el=45
            # expected_az = 180.3
            # expected_el = 24.8
            # For the mock:
            expected_az_mock = 180.0
            expected_el_mock = 45.0

            azr = math.radians(expected_az_mock)
            elr = math.radians(expected_el_mock)

            # expected_x = math.cos(elr) * math.sin(azr) # Around 0 for az=180
            # expected_y = math.cos(elr) * math.cos(azr) # Around -cos(elr) for az=180
            # expected_z = math.sin(elr)

            # Using the mocked astral values
            # az = 180, el = 45
            # azr = pi, elr = pi/4
            # x = cos(pi/4)*sin(pi) = (sqrt(2)/2) * 0 = 0
            # y = cos(pi/4)*cos(pi) = (sqrt(2)/2) * (-1) = -0.70710678
            # z = sin(pi/4) = sqrt(2)/2 = 0.70710678

            expected_x = 0.0
            expected_y = -math.cos(math.pi/4)
            expected_z = math.sin(math.pi/4)

            x, y, z = utils.compute_sun_vector(lat, lon)

            self.assertAlmostEqual(x, expected_x, places=5)
            self.assertAlmostEqual(y, expected_y, places=5)
            self.assertAlmostEqual(z, expected_z, places=5)

    def test_modbus_crc16_fallback(self):
        # Test the pure Python fallback implementation
        # Known CRC for "123456789" is 0x4B37 (or 19255 in decimal)
        # For Modbus, the polynomial is 0xA001 (reversed 0x8005), init 0xFFFF
        # Test case from a known online calculator for Modbus CRC-16:
        # Data: 01 03 00 00 00 01 (hex bytes) -> CRC: 84 0A (hex, low byte first) -> 0x0A84
        data_bytes = b'\x01\x03\x00\x00\x00\x01'
        expected_crc = 0x0A84 # Standard Modbus: low byte, then high byte

        # Temporarily make libscrc fail to import to test fallback
        with mock.patch.dict('sys.modules', {'libscrc': None}):
            # Need to reload utils for the change to take effect if utils already imported libscrc
            import importlib
            importlib.reload(utils)
            crc = utils.modbus_crc16(data_bytes)
            self.assertEqual(crc, expected_crc)
        # Reload utils again to restore original state if libscrc was available
        importlib.reload(utils)


    @mock.patch('utils.libscrc', None) # Force fallback for this specific test too
    def test_modbus_crc16_fallback_direct(self, mock_libscrc):
        # Test with a different known value if needed
        data_bytes = b'HelloWorld'
        # Pre-calculated CRC for "HelloWorld" with Modbus settings:
        # (poly=0xA001, init=0xFFFF, rev=True for data bytes, rev=True for final CRC, xor_out=0x0000)
        # This depends on exact interpretation. A common online tool gives 0x9477 for this.
        # Let's use the same 010300000001 -> 0x0A84 as it's standard.
        data_bytes_2 = b'\x01\x03\x00\x00\x00\x01'
        expected_crc_2 = 0x0A84
        crc = utils.modbus_crc16(data_bytes_2)
        self.assertEqual(crc, expected_crc_2)

    def test_modbus_crc16_libscrc(self):
        # This test will run if libscrc is installed and imported by utils
        try:
            import libscrc
            # Test case from a known online calculator for Modbus CRC-16:
            # Data: 01 03 00 00 00 01 (hex bytes) -> CRC: 84 0A (hex, low byte first) -> 0x0A84
            data_bytes = b'\x01\x03\x00\x00\x00\x01'
            expected_crc = 0x0A84 # Standard Modbus: low byte, then high byte

            # Ensure utils is using the libscrc version for this test
            import importlib
            if 'libscrc' not in sys.modules: # If it was mocked out and reloaded
                 sys.modules['libscrc'] = libscrc # try to put it back
            importlib.reload(utils)

            if not hasattr(utils, 'libscrc') or utils.libscrc is None:
                self.skipTest("libscrc not available or not loaded by utils, skipping libscrc test.")

            crc = utils.modbus_crc16(data_bytes)
            self.assertEqual(crc, expected_crc)
        except ImportError:
            self.skipTest("libscrc not installed, skipping libscrc test.")
        finally:
            # Reload utils again to restore original state if it was modified
            import importlib
            importlib.reload(utils)


    def test_draw_device_orientation(self):
        # This is a visual function. We'll mostly test if it runs without errors.
        # Mock matplotlib's pyplot and Axes3D
        mock_ax = mock.Mock(spec=['clear', 'set_xlim', 'set_ylim', 'set_zlim',
                                  'set_xlabel', 'set_ylabel', 'set_zlabel',
                                  'plot3D', 'scatter', 'quiver', 'set_title',
                                  'set_box_aspect'])

        # Call the function with some typical values
        try:
            utils.draw_device_orientation(mock_ax, roll=10, pitch=20, yaw=30)
        except Exception as e:
            self.fail(f"draw_device_orientation raised an exception: {e}")

        # Check if some basic ax methods were called
        mock_ax.clear.assert_called_once()
        mock_ax.set_xlim.assert_called_with(-1, 1)
        mock_ax.set_title.assert_called()


if __name__ == '__main__':
    unittest.main()
