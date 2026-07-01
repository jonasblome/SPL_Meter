#!/usr/bin/env python3
"""
Audio Input Module for ICS43434 Microphone
Simple I2S microphone reader for Raspberry Pi Zero W
"""

import os
import time
import numpy as np

os.environ.setdefault("JACK_NO_AUDIO_RESERVATION", "1")
os.environ.setdefault("JACK_NO_START_SERVER", "1")

try:
    import pyaudio
except ImportError:
    print("pyaudio not installed. Please install with: pip install pyaudio")
    exit(1)


class AudioDeviceManager:
    """Manages ICS43434 I2S microphone audio input and processing"""
    
    def __init__(self, sample_rate=48000, chunk_size=1024, device_index=0, audio_processor=None):
        """
        Initialize the audio device manager
        
        Args:
            sample_rate (int): Audio sample rate in Hz
            chunk_size (int): Number of samples per chunk
            device_index (int): PyAudio device index to use
        """
        print("AudioDeviceManager: Initializing")
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.num_channels = 2
        self.is_recording = False
        self.audio = None
        self.stream = None
        self.latest_rms = 0.0
        self.latest_spl_db = 0.0
        self.latest_peak = 0.0
        self.latest_time_weighted_value = 0.0
        self.last_error = None
        self.time_weighting = "Fast"

        self.audio_processor = audio_processor
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream"""
        # Convert byte data to numpy array (32-bit PCM, googlevoicehat I2S driver)
        audio_data = np.frombuffer(in_data, dtype=np.int32)
        
        # Normalize to float [-1.0, 1.0] (32-bit range = 2^31)
        audio_float = audio_data.astype(np.float32) / 2147483648.0
        
        # Compute audio metrics
        rms = self.audio_processor.compute_rms(audio_float)
        spl_db = self.audio_processor.compute_spl_db(audio_float)
        peak = self.audio_processor.compute_peak(audio_float)

        # Time weighting
        if self.time_weighting == "Fast":
            latest_time_weighted_value = self.audio_processor.compute_fast_state(audio_float)
        else:
            latest_time_weighted_value = self.audio_processor.compute_slow_state(audio_float)

        #Save the data
        self.latest_rms = float(rms)
        self.latest_spl_db = float(spl_db)
        self.latest_peak = float(peak)
        self.latest_time_weighted_value = float(latest_time_weighted_value)

        # Output raw data
        print(f"RMS: {self.latest_rms:.6f}, SPL: {self.latest_spl_db:.2f} dB, Peak: {self.latest_peak:.6f}, Time Weighted: {self.latest_time_weighted_value:.6f}")
        
        return (in_data, pyaudio.paContinue)
        
    def start_recording(self):
        """Start recording from the microphone"""
        try:
            self.is_recording = True
            print(f"Starting recording at {self.sample_rate} Hz...")
            print("Press Ctrl+C to stop recording")
            
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Open audio stream on the I2S device
            self.stream = self.audio.open(
                format=pyaudio.paInt32,
                channels=self.num_channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            # Start the stream
            self.stream.start_stream()
            
            # Keep the main thread alive
            while self.is_recording and self.stream.is_active():
                time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            self.stop_recording()
    
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False

        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
            except Exception as e:
                print(f"Error stopping stream: {e}")
            try:
                self.stream.close()
            except Exception as e:
                print(f"Error closing stream: {e}")
            finally:
                self.stream = None

        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                print(f"Error terminating audio: {e}")
            finally:
                self.audio = None
    
    def list_devices(self):
        """List available audio devices"""
        audio = pyaudio.PyAudio()
        print("Available audio devices:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            print(f"  {i}: {info['name']} (inputs: {info['maxInputChannels']})")
        audio.terminate()

    def get_num_channels_of_current_device(self):
        """Get the number of channels for the current device index"""
        if self.device_index is None:
            raise ValueError("Device index is not set. Please set it using set_device_index() method.")
        
        audio = pyaudio.PyAudio()
        try:
            info = audio.get_device_info_by_index(self.device_index)
            num_channels = info['maxInputChannels']
            return num_channels
        finally:
            audio.terminate()

    def set_device_index(self, index):
        """Set the audio device index to use for recording"""
        self.device_index = index
        self.num_channels = self.get_num_channels_of_current_device()
    
    def generate_noise(self, num_samples=48000):
        noise = np.random.normal(0, 1, num_samples)

        return noise