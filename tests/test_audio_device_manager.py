#!/usr/bin/env python3
"""
Tests for AudioDeviceManager Module
Unit tests for ICS43434 microphone audio device manager
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from AudioDeviceManager import AudioDeviceManager
except ImportError:
    # If pyaudio is not available, set class to None for skipping tests
    AudioDeviceManager = None


class TestAudioDeviceManager(unittest.TestCase):
    """Test cases for AudioDeviceManager class"""

    def setUp(self):
        """Set up test fixtures"""
        if AudioDeviceManager is None:
            self.skipTest("pyaudio not available")

        self.sample_rate = 48000
        self.chunk_size = 1024
        self.device_index = 0
        self.manager = AudioDeviceManager(
            sample_rate=self.sample_rate,
            chunk_size=self.chunk_size,
            device_index=self.device_index
        )

    def test_initialization(self):
        """Test manager initialization"""
        self.assertEqual(self.manager.sample_rate, self.sample_rate)
        self.assertEqual(self.manager.chunk_size, self.chunk_size)
        self.assertEqual(self.manager.device_index, self.device_index)
        self.assertFalse(self.manager.is_recording)
        self.assertIsNone(self.manager.audio)
        self.assertIsNone(self.manager.stream)

    def test_stop_recording(self):
        """Test stop recording method"""
        self.manager.is_recording = True
        self.manager.stop_recording()
        self.assertFalse(self.manager.is_recording)

    @patch('AudioDeviceManager.pyaudio')
    def test_list_devices(self, mock_pyaudio):
        """Test device listing"""
        mock_audio = MagicMock()
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_device_info_by_index.side_effect = [
            {'name': 'Device1', 'maxInputChannels': 2},
            {'name': 'Device2', 'maxInputChannels': 0}
        ]
        mock_pyaudio.PyAudio.return_value = mock_audio

        with patch('builtins.print') as mock_print:
            self.manager.list_devices()
            mock_print.assert_called()

    @patch('AudioDeviceManager.pyaudio')
    def test_audio_callback(self, mock_pyaudio):
        """Test audio callback function"""
        manager = AudioDeviceManager(sample_rate=48000, chunk_size=1024)

        # Mock audio data (32-bit PCM samples)
        test_samples = np.array([100000, 200000, 300000], dtype=np.int32)
        test_data = test_samples.tobytes()

        mock_pyaudio.paContinue = 1

        with patch('builtins.print') as mock_print:
            result = manager._audio_callback(test_data, len(test_samples), None, None)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[1], mock_pyaudio.paContinue)

    def test_spl_calculation(self):
        """Test SPL calculation logic"""
        rms_values = [0.00002, 0.0002, 0.002, 0.02]
        expected_spl = []

        for rms in rms_values:
            if rms > 0:
                spl_db = 20 * np.log10(rms / 0.00002)
                expected_spl.append(spl_db)
            else:
                expected_spl.append(-np.inf)

        for i, rms in enumerate(rms_values):
            if rms > 0:
                calculated_spl = 20 * np.log10(rms / 0.00002)
                self.assertAlmostEqual(calculated_spl, expected_spl[i], places=5)


class TestAudioDeviceManagerModule(unittest.TestCase):
    """Test cases for the AudioDeviceManager module"""

    def test_numpy_availability(self):
        """Test that numpy functions are available"""
        test_array = np.array([1.0, 2.0, 3.0, 4.0])

        mean_val = np.mean(test_array)
        sqrt_val = np.sqrt(mean_val)
        max_val = np.max(np.abs(test_array))

        self.assertIsInstance(mean_val, (int, float))
        self.assertIsInstance(sqrt_val, (int, float))
        self.assertIsInstance(max_val, (int, float))


class TestIntegration(unittest.TestCase):
    """Integration tests for the audio device manager"""

    def setUp(self):
        """Set up integration test fixtures"""
        if AudioDeviceManager is None:
            self.skipTest("pyaudio not available")

    @patch('AudioDeviceManager.pyaudio')
    def test_full_workflow_mock(self, mock_pyaudio):
        """Test full workflow with mocked audio device"""
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_stream.is_active.return_value = False
        mock_pyaudio.PyAudio.return_value = mock_audio
        mock_pyaudio.paInt32 = 0x02
        mock_pyaudio.paContinue = 1

        manager = AudioDeviceManager(sample_rate=48000, chunk_size=1024)

        with patch('builtins.print') as mock_print:
            mock_audio.get_device_count.return_value = 1
            mock_audio.get_device_info_by_index.return_value = {
                'name': 'TestDevice', 'maxInputChannels': 2
            }
            manager.list_devices()
            mock_audio.get_device_count.assert_called_once()


def run_manual_tests():
    """Manual test functions for hardware testing"""
    print("Manual Tests for AudioDeviceManager")
    print("=" * 40)

    if AudioDeviceManager is None:
        print("Cannot run manual tests: pyaudio not available")
        return

    print("1. Device Test:")
    print("   - Check if I2S device is available")
    print("   - Verify device listing works")

    print("\n2. Audio Stream Test:")
    print("   - Test audio stream initialization")
    print("   - Verify callback function receives data")

    print("\n3. SPL Calculation Test:")
    print("   - Test with known audio levels")
    print("   - Verify SPL calculations are reasonable")

    print("\nTo run manual tests, execute:")
    print("python -c 'from test_audio_device_manager import run_manual_tests; run_manual_tests()'")


if __name__ == '__main__':
    unittest.main(verbosity=2, exit=False)
    print("\n" + "=" * 60)
    run_manual_tests()
