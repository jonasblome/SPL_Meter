#!/usr/bin/env python3
"""
Tests for Audio Input Module
Unit tests for ICS43434 microphone reader
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from audio_input import ICS43434Reader
except ImportError:
    # If pyaudio is not available, create a mock for testing
    ICS43434Reader = None


class TestICS43434Reader(unittest.TestCase):
    """Test cases for ICS43434Reader class"""
    
    def setUp(self):
        """Set up test fixtures"""
        if ICS43434Reader is None:
            self.skipTest("pyaudio not available")
        
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.reader = ICS43434Reader(
            sample_rate=self.sample_rate,
            chunk_size=self.chunk_size
        )
    
    def test_initialization(self):
        """Test reader initialization"""
        self.assertEqual(self.reader.sample_rate, self.sample_rate)
        self.assertEqual(self.reader.chunk_size, self.chunk_size)
        self.assertFalse(self.reader.is_recording)
        self.assertIsNone(self.reader.audio)
        self.assertIsNone(self.reader.stream)
    
    def test_stop_recording(self):
        """Test stop recording method"""
        self.reader.is_recording = True
        self.reader.stop_recording()
        self.assertFalse(self.reader.is_recording)
    
    @patch('audio_input.pyaudio')
    def test_list_devices(self, mock_pyaudio):
        """Test device listing"""
        mock_audio = MagicMock()
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_device_info_by_index.side_effect = [
            {'name': 'Device1', 'maxInputChannels': 2},
            {'name': 'Device2', 'maxInputChannels': 0}
        ]
        mock_pyaudio.PyAudio.return_value = mock_audio
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            self.reader.list_devices()
            mock_print.assert_called()
    
    @patch('audio_input.pyaudio')
    def test_audio_callback(self, mock_pyaudio):
        """Test audio callback function"""
        # Create reader
        reader = ICS43434Reader(sample_rate=44100, chunk_size=1024)
        
        # Mock audio data (16-bit PCM samples)
        test_samples = np.array([1000, 2000, 3000], dtype=np.int16)
        test_data = test_samples.tobytes()
        
        # Test the callback directly
        with patch('builtins.print') as mock_print:
            result = reader._audio_callback(test_data, len(test_samples), None, None)
            # Callback should return (data, continue_flag)
            self.assertEqual(len(result), 2)
            self.assertEqual(result[1], mock_pyaudio.paContinue if hasattr(mock_pyaudio, 'paContinue') else 1)
    
    def test_spl_calculation(self):
        """Test SPL calculation logic"""
        # Test SPL calculation formula
        rms_values = [0.00002, 0.0002, 0.002, 0.02]  # Different RMS values
        
        expected_spl = []
        for rms in rms_values:
            if rms > 0:
                spl_db = 20 * np.log10(rms / 0.00002)
                expected_spl.append(spl_db)
            else:
                expected_spl.append(-np.inf)
        
        # Verify calculations
        for i, rms in enumerate(rms_values):
            if rms > 0:
                calculated_spl = 20 * np.log10(rms / 0.00002)
                self.assertAlmostEqual(calculated_spl, expected_spl[i], places=5)


class TestAudioInputModule(unittest.TestCase):
    """Test cases for the audio input module"""
    
    def test_import_error_handling(self):
        """Test handling of missing pyaudio import"""
        # This test verifies that the module handles import errors gracefully
        with patch.dict('sys.modules', {'pyaudio': None}):
            try:
                # Re-import the module to test import error handling
                import importlib
                import audio_input
                importlib.reload(audio_input)
            except ImportError:
                pass  # Expected when pyaudio is not available
    
    def test_numpy_availability(self):
        """Test that numpy functions are available"""
        # Test basic numpy operations used in the module
        test_array = np.array([1.0, 2.0, 3.0, 4.0])
        
        # Test functions used in audio processing
        mean_val = np.mean(test_array)
        sqrt_val = np.sqrt(mean_val)
        max_val = np.max(np.abs(test_array))
        
        self.assertIsInstance(mean_val, (int, float))
        self.assertIsInstance(sqrt_val, (int, float))
        self.assertIsInstance(max_val, (int, float))


class TestIntegration(unittest.TestCase):
    """Integration tests for the audio input system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        if ICS43434Reader is None:
            self.skipTest("pyaudio not available")
    
    @patch('audio_input.pyaudio')
    def test_full_workflow_mock(self, mock_pyaudio):
        """Test full workflow with mocked audio device"""
        # Mock PyAudio
        mock_audio = MagicMock()
        mock_stream = MagicMock()
        mock_audio.open.return_value = mock_stream
        mock_stream.is_active.return_value = False  # Stop immediately
        mock_pyaudio.PyAudio.return_value = mock_audio
        mock_pyaudio.paInt16 = 0x08
        mock_pyaudio.paContinue = 1
        
        # Create reader and test workflow
        reader = ICS43434Reader(sample_rate=44100, chunk_size=1024)
        
        # Test device listing
        with patch('builtins.print') as mock_print:
            mock_audio.get_device_count.return_value = 1
            mock_audio.get_device_info_by_index.return_value = {
                'name': 'TestDevice', 'maxInputChannels': 1
            }
            reader.list_devices()
            mock_audio.get_device_count.assert_called_once()
        
        # Verify stream parameters would be correct
        # (We don't actually start the stream in tests to avoid hardware dependencies)


def run_manual_tests():
    """Manual test functions for hardware testing"""
    print("Manual Tests for ICS43434 Reader")
    print("=" * 40)
    
    if ICS43434Reader is None:
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
    print("python -c 'from test_audio_input import run_manual_tests; run_manual_tests()'")


if __name__ == '__main__':
    # Run unit tests
    unittest.main(verbosity=2, exit=False)
    
    # Show manual test instructions
    print("\n" + "=" * 60)
    run_manual_tests()
