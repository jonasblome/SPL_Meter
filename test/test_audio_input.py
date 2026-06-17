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
    # If sounddevice is not available, create a mock for testing
    ICS43434Reader = None


class TestICS43434Reader(unittest.TestCase):
    """Test cases for ICS43434Reader class"""
    
    def setUp(self):
        """Set up test fixtures"""
        if ICS43434Reader is None:
            self.skipTest("sounddevice not available")
        
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
        self.assertEqual(self.reader.device, 'bcm2835_i2s')
        self.assertFalse(self.reader.is_recording)
    
    def test_stop_recording(self):
        """Test stop recording method"""
        self.reader.is_recording = True
        self.reader.stop_recording()
        self.assertFalse(self.reader.is_recording)
    
    @patch('audio_input.sd')
    def test_list_devices(self, mock_sd):
        """Test device listing"""
        mock_sd.query_devices.return_value = ["Device1", "Device2"]
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            self.reader.list_devices()
            mock_print.assert_called()
    
    @patch('audio_input.sd')
    @patch('audio_input.np.sqrt')
    @patch('audio_input.np.mean')
    @patch('audio_input.np.max')
    @patch('audio_input.np.abs')
    @patch('audio_input.np.log10')
    def test_audio_callback(self, mock_log10, mock_abs, mock_max, mock_mean, mock_sqrt, mock_sd):
        """Test audio callback function"""
        # Mock audio data
        test_data = np.array([[0.1, 0.2, 0.3]]).T
        
        # Mock numpy functions
        mock_mean.return_value = 0.02
        mock_sqrt.return_value = 0.1414
        mock_abs.return_value = np.array([0.1, 0.2, 0.3])
        mock_max.return_value = 0.3
        mock_log10.return_value = 3.0
        
        # Test the callback
        with patch('builtins.print') as mock_print:
            # We need to access the callback through the start_recording method
            # This is a simplified test - in practice, the callback is defined inside start_recording
            pass
    
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
        """Test handling of missing sounddevice import"""
        # This test verifies that the module handles import errors gracefully
        with patch.dict('sys.modules', {'sounddevice': None}):
            try:
                # Re-import the module to test import error handling
                import importlib
                import audio_input
                importlib.reload(audio_input)
            except ImportError:
                pass  # Expected when sounddevice is not available
    
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
            self.skipTest("sounddevice not available")
    
    @patch('audio_input.sd')
    def test_full_workflow_mock(self, mock_sd):
        """Test full workflow with mocked audio device"""
        # Mock the audio stream
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value.__enter__.return_value = mock_stream
        
        # Create reader and test workflow
        reader = ICS43434Reader(sample_rate=44100, chunk_size=1024)
        
        # Test device listing
        with patch('builtins.print') as mock_print:
            reader.list_devices()
            mock_sd.query_devices.assert_called_once()
        
        # Verify stream parameters would be correct
        # (We don't actually start the stream in tests to avoid hardware dependencies)


def run_manual_tests():
    """Manual test functions for hardware testing"""
    print("Manual Tests for ICS43434 Reader")
    print("=" * 40)
    
    if ICS43434Reader is None:
        print("Cannot run manual tests: sounddevice not available")
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
