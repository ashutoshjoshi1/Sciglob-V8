import unittest
from unittest import mock
import numpy as np

# Adjust import path for drivers
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Modules to be tested
from drivers import spectrometer as drv_spectrometer
from drivers.avaspec import AvsIdentityType, MeasConfigType # Import structures for type checking if needed

# --- Globals that might be accessed by drivers.spectrometer ---
# If drivers.spectrometer directly uses drivers.globals, we might need to mock them too,
# or ensure they have default values. For now, assuming SpectrometerDriver class is self-contained
# or that its interactions with globals are minimal for these tests.
# Example:
# drv_globals_mock = mock.MagicMock()
# drv_globals_mock.INVALID_AVS_HANDLE_VALUE = 1000
# sys.modules['drivers.globals'] = drv_globals_mock


# --- Mocking the avaspec module ---
# Create a mock object for the entire avaspec module
avaspec_mock = mock.MagicMock()

# Define return values or side effects for each avaspec function used
# by spectrometer.py (both standalone functions and SpectrometerDriver class)

# For connect_spectrometer() and SpectrometerDriver.reset()
avaspec_mock.AVS_Init.return_value = 1 # Number of devices
avaspec_mock.AVS_UpdateUSBDevices.return_value = 1
mock_dev_id = AvsIdentityType()
mock_dev_id.SerialNumber = b"testserial"
mock_dev_id.Status = b'\x01' # Typical status for available
avaspec_mock.AVS_GetList.return_value = [mock_dev_id] # List of one device

# Activated handle (needs to be a value, not INVALID_AVS_HANDLE_VALUE)
# INVALID_AVS_HANDLE_VALUE is 1000, so a valid handle could be 0, 1, etc.
# Let's make it a distinct integer not 0, as 0 can sometimes be special.
MOCK_VALID_HANDLE = 1
avaspec_mock.AVS_Activate.return_value = MOCK_VALID_HANDLE
avaspec_mock.INVALID_AVS_HANDLE_VALUE = 1000 # Ensure this constant is available

mock_device_config = mock.Mock() # Simplified mock for DeviceConfigType
mock_device_config.m_Detector_m_NrPixels = 2048
avaspec_mock.AVS_GetParameter.return_value = mock_device_config

mock_wavelengths = np.linspace(200, 900, 2048)
# AVS_GetLambda returns a ctypes array pointer, so we need to mock that behavior somewhat
# For simplicity, we'll have it return something that can be processed by np.ctypeslib.as_array
# or directly a numpy array if the calling code handles it.
# The actual spectrometer.py does: np.ctypeslib.as_array(AVS_GetLambda(handle))
# So AVS_GetLambda should return a ctypes array.
WAVELENGTH_ARRAY_TYPE = ctypes.c_double * 2048
mock_ctypes_wavelengths = WAVELENGTH_ARRAY_TYPE(*mock_wavelengths)
avaspec_mock.AVS_GetLambda.return_value = mock_ctypes_wavelengths

# For starting/stopping measurements
avaspec_mock.AVS_PrepareMeasure.return_value = 0 # SUCCESS
avaspec_mock.AVS_MeasureCallback.return_value = 0 # SUCCESS
avaspec_mock.AVS_StopMeasure.return_value = 0 # SUCCESS
avaspec_mock.AVS_Deactivate.return_value = True # Success

# For getting data
# AVS_GetScopeData returns (timestamp, spectrum_data_pointer)
# spectrum_data_pointer is POINTER(ctypes.c_double * 4096)
# Let's prepare mock spectral data
mock_spectrum_values = np.random.rand(4096) * 60000
SPECTRUM_ARRAY_TYPE = ctypes.c_double * 4096
mock_ctypes_spectrum = SPECTRUM_ARRAY_TYPE(*mock_spectrum_values)
avaspec_mock.AVS_GetScopeData.return_value = (12345, mock_ctypes_spectrum)


# Apply the mock to sys.modules so it's used by "from avaspec import *"
# This needs to be done BEFORE `drivers.spectrometer` is imported by the test runner for the first time
# or we need to reload `drivers.spectrometer`.
# For safety, it's often best done globally or via a context manager for specific tests.
# Here, we are doing it globally for this test file.
# If tests were run in parallel or if module was already imported, this could be tricky.
# A common pattern is to place mocks in a fixture or setUp method.

# sys.modules['avaspec'] = avaspec_mock
# sys.modules['drivers.avaspec'] = avaspec_mock # If spectrometer.py uses "from drivers.avaspec import"

# It's safer to use @mock.patch.dict(sys.modules, {'avaspec': avaspec_mock, 'drivers.avaspec': avaspec_mock})
# per test method or class, or use @mock.patch('drivers.spectrometer.AVS_Init', new=avaspec_mock.AVS_Init) for each.

@mock.patch.dict(sys.modules, {'avaspec': avaspec_mock, 'drivers.avaspec': avaspec_mock})
class TestSpectrometerDriver(unittest.TestCase):

    def setUp(self):
        # Reset mocks before each test to clear call counts, etc.
        avaspec_mock.reset_mock()

        # Reload drv_spectrometer to ensure it picks up the fresh mocks for each test method
        # This is crucial if other tests might have imported it already.
        import importlib
        importlib.reload(drv_spectrometer)

        self.driver = drv_spectrometer.SpectrometerDriver()

    # Test for the standalone connect_spectrometer and deactivate_spectrometer_handle
    def test_standalone_connect_deactivate(self):
        # Reset mocks used by connect_spectrometer specifically
        avaspec_mock.AVS_Init.reset_mock()
        avaspec_mock.AVS_UpdateUSBDevices.reset_mock()
        avaspec_mock.AVS_GetList.reset_mock()
        avaspec_mock.AVS_Activate.reset_mock()
        avaspec_mock.AVS_GetParameter.reset_mock()
        avaspec_mock.AVS_GetLambda.reset_mock()
        avaspec_mock.AVS_Deactivate.reset_mock()
        avaspec_mock.AVS_StopMeasure.reset_mock()

        handle, wavelengths, num_pixels, serial_str = drv_spectrometer.connect_spectrometer()

        avaspec_mock.AVS_Init.assert_called_once_with(0)
        avaspec_mock.AVS_UpdateUSBDevices.assert_called_once()
        avaspec_mock.AVS_GetList.assert_called_once()
        avaspec_mock.AVS_Activate.assert_called_once()
        self.assertEqual(handle, MOCK_VALID_HANDLE)
        self.assertEqual(num_pixels, 2048)
        self.assertEqual(serial_str, "testserial")
        self.assertTrue(np.array_equal(np.array(wavelengths), mock_wavelengths[:2048])) # Wavelengths truncated to num_pixels

        success, msg = drv_spectrometer.deactivate_spectrometer_handle(handle)
        self.assertTrue(success)
        avaspec_mock.AVS_StopMeasure.assert_called_once_with(handle)
        avaspec_mock.AVS_Deactivate.assert_called_once_with(handle)

    def test_driver_initialization(self):
        # SpectrometerDriver.__init__ is simple, doesn't call AVS_Init itself.
        # AVS_Init is called by the global connect_spectrometer, which driver.reset() uses.
        self.assertIsInstance(self.driver, drv_spectrometer.SpectrometerDriver)
        self.assertEqual(self.driver.handles, {})

    @mock.patch('drivers.spectrometer.connect_spectrometer') # Mock the global helper
    def test_driver_reset_connect(self, mock_connect_spectrometer_func):
        # Configure the mock for the global connect_spectrometer
        mock_connect_spectrometer_func.return_value = (
            MOCK_VALID_HANDLE, mock_wavelengths, 2048, "testserial_driver"
        )
        # Mock AVS_MeasureCallback for the ini=True part of reset
        avaspec_mock.AVS_MeasureCallback.return_value = 0 # Success

        success, message = self.driver.reset(ispec=0, ini=True) # ini=True calls measure

        self.assertTrue(success)
        mock_connect_spectrometer_func.assert_called_once()
        self.assertIn(0, self.driver.handles)
        self.assertEqual(self.driver.handles[0]['handle'], MOCK_VALID_HANDLE)
        self.assertEqual(self.driver.handles[0]['serial'], "testserial_driver")
        # Check if measure-related calls happened due to ini=True
        avaspec_mock.AVS_PrepareMeasure.assert_called()
        avaspec_mock.AVS_MeasureCallback.assert_called()


    def test_driver_disconnect(self):
        # First, connect a device using reset (mocking dependencies)
        avaspec_mock.AVS_Activate.return_value = MOCK_VALID_HANDLE + 1 # Use a different handle
        # Minimal setup in self.driver.handles for this test
        self.driver.handles[0] = {'handle': MOCK_VALID_HANDLE + 1, 'num_pixels': 2048, 'integration_time': 50}
        self.driver.data_status[0] = 'READY'

        success, message = self.driver.disconnect(ispec=0)

        self.assertTrue(success)
        avaspec_mock.AVS_StopMeasure.assert_called_with(MOCK_VALID_HANDLE + 1)
        avaspec_mock.AVS_Deactivate.assert_called_with(MOCK_VALID_HANDLE + 1)
        self.assertNotIn(0, self.driver.handles)


    def test_driver_start_stop_measurement(self):
        # Setup a connected spectrometer
        # Use a unique handle to avoid interference from other tests if mocks weren't perfectly reset
        current_test_handle = MOCK_VALID_HANDLE + 2
        avaspec_mock.AVS_Activate.return_value = current_test_handle
        self.driver.handles[0] = {
            'handle': current_test_handle,
            'num_pixels': 2048,
            'integration_time': 50.0 # Default or set via set_it
        }
        self.driver.data_status[0] = 'READY'

        # Test start measurement
        success, message = self.driver.measure(ispec=0, ncy=1)
        self.assertTrue(success, f"Start measurement failed: {message}")
        avaspec_mock.AVS_PrepareMeasure.assert_called_with(
            current_test_handle,
            mock.ANY, # This is the MeasConfigType struct
            # integration_time_ms=50.0, averages=1, cycles=1, repetitions=1 # These are inside the struct
        )
        # Check that the third argument to AVS_MeasureCallback is the callback itself
        avaspec_mock.AVS_MeasureCallback.assert_called_with(current_test_handle, mock.ANY, -1)
        self.assertEqual(self.driver.data_status[0], 'MEASURING')

        # Test stop measurement (via disconnect, as driver has no direct stop_ispec)
        # Or, we can test the global stop_measurement if the handle is known
        drv_spectrometer.stop_measurement(current_test_handle)
        avaspec_mock.AVS_StopMeasure.assert_called_with(current_test_handle)
        # Note: This tests the global helper, not a driver method for stop if one existed.
        # SpectrometerController calls its own stop() which uses StopMeasureThread.


    def test_get_data_via_callback(self):
        # Setup a connected spectrometer
        current_test_handle = MOCK_VALID_HANDLE + 3
        avaspec_mock.AVS_Activate.return_value = current_test_handle
        self.driver.handles[0] = {
            'handle': current_test_handle,
            'num_pixels': 2048,
            'integration_time': 10.0,
            'saturated': False # Initial state
        }
        self.driver.data_status[0] = 'MEASURING' # Assume measurement is active

        # Prepare mock data for the callback
        # The callback expects p_data as POINTER(ctypes.c_int) and p_user as POINTER(ctypes.c_int)
        # p_data[0] is the handle, p_user[0] is the status code from measurement

        # Mock the handle pointer that would be passed to the callback
        mock_p_data = (ctypes.c_int * 1)(current_test_handle) # Pointer to the handle

        # Mock the status code pointer (0 for success)
        mock_p_user_status = (ctypes.c_int * 1)(0)

        # Call the callback directly
        self.driver._measurement_callback(mock_p_data, mock_p_user_status)

        # Assertions
        avaspec_mock.AVS_GetScopeData.assert_called_with(current_test_handle)
        self.assertEqual(self.driver.data_status[0], 'DATA_READY')
        self.assertIn('last_data', self.driver.handles[0])
        # Compare content of last_data with mock_spectrum_values (up to num_pixels)
        # Note: AVS_GetScopeData returns a tuple (timestamp, spectrum_pointer)
        # The callback processes this.
        # self.assertTrue(np.array_equal(self.driver.handles[0]['last_data'], mock_spectrum_values[:2048]))
        # The mock_spectrum_values is 4096, but device is 2048.
        # The callback doesn't seem to truncate based on num_pixels, AVS_GetScopeData returns full 4096.
        # This means self.intens in controller will be 4096, then truncated.
        # Here, driver.handles[0]['last_data'] will be the raw data from AVS_GetScopeData mock.
        self.assertTrue(np.array_equal(self.driver.handles[0]['last_data'], mock_ctypes_spectrum))


if __name__ == '__main__':
    unittest.main()
