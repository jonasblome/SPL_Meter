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
import scipy.io.wavfile as wf
from datetime import datetime


class AudioDeviceManager:
    """Manages ICS43434 I2S microphone audio input and processing"""
    
    def __init__(self, audio_processor, sample_rate=48000, chunk_size=1024, device_index=0):
        """
        Initialize the audio device manager
        
        Args:
            audio_processor (AudioProcessor): The audio processor instance
            sample_rate (int): Audio sample rate in Hz
            chunk_size (int): Number of samples per chunk
            device_index (int): PyAudio device index to use
        """
        print("AudioDeviceManager: Initializing")

        # Device/recording state
        self.device_index = device_index
        self.num_channels = 2
        self.recording_format = pyaudio.paInt32
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio = None
        self.stream = None

        # Audio processing
        self.audio_processor = audio_processor
        self.latest_filterband_spl_db = [0.0] * 8
        self.latest_a_weighted_spl_db = 0.0
        self.latest_rms = 0.0
        self.latest_spl_db = 0.0
        self.latest_peak = 0.0
        self.latest_fast_state = 0.0
        self.latest_slow_state = 0.0
        self.latest_time_weighted_value = 0.0
        self.time_weighting = "Fast"

        # File recording
        self.storing_format = pyaudio.paFloat32
        self.should_store_recording = False
        self.recording_data_blocks = []

        # Prepare filterbank in advance to only calculate once
        self.filterbank = self.audio_processor.design_a_weighting_filterbank(self.sample_rate, is_octave=True)
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream"""
        # Convert byte data to numpy array (32-bit PCM, googlevoicehat I2S driver)
        raw_audio_data = np.frombuffer(in_data, dtype=np.int32)
        
        # ICS43434 is 24-bit MSB-justified in 32-bit words, shift right by 8
        audio_data = audio_data >> 8
        
        # Normalize to float [-1.0, 1.0] (24-bit range = 2^23)
        audio_float = audio_data.astype(np.float32) / 8388608.0
        
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
        # print(f"RMS: {self.latest_rms:.6f}, SPL: {self.latest_spl_db:.2f} dB, Peak: {self.latest_peak:.6f}, Time Weighted: {self.latest_time_weighted_value:.6f}")
        
        return (in_data, pyaudio.paContinue)
        
    def start_recording(self):
        """Start recording from the microphone"""
        try:
            self.is_recording = True
            print(f"Starting recording at {self.sample_rate} Hz...")
            print("Press Ctrl+C to stop recording")

            # Reset recorded audio
            self.recording_data_blocks = []
            
            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            
            # Open audio stream on the I2S device
            self.stream = self.audio.open(
                format=self.recording_format,
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
        except Exception as e:
            print(f"Error during recording: {e}")
            self.stop_recording()
    
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False

        if self.should_store_recording:
            self.write_recording_to_file(f"{datetime.now()}.wav")

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

    def store_recording(self, recording_data):
        self.recording_data_blocks.append(recording_data)

    def write_recording_to_file(self, file_name):
        print(f"Storing recorded audio to file: {file_name}")
        all_recording_data = np.concatenate(self.recording_data_blocks).ravel()
        wf.write(file_name, self.sample_rate, all_recording_data)

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