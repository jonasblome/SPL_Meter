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
        self.set_device_index(device_index)
        self.recording_format = pyaudio.paInt32
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_recording = False
        self.audio = None
        self.stream = None

        # Audio processing
        self.audio_processor = audio_processor
        self.latest_raw_spl_db = 0.0
        self.calibration_offset_db = 0.0
        self.latest_spl_db = 0.0
        self.latest_rms = 0.0
        self.latest_peak = 0.0
        self.latest_leq_db = None
        self.latest_leq_is_complete = False

        # Prepare filterbank in advance to only calculate once
        self.filterbank = self.audio_processor.design_a_weighting_filterbank(self.sample_rate, is_octave=True)
        self.latest_filterband_spl_db = [0.0] * len(self.filterbank)
        self.latest_a_weighted_spl_db = 0.0

        # Time weighting
        self.latest_fast_state = 0.0
        self.latest_slow_state = 0.0

        # Latest Leq values used by the UI stream and JSON export.
        self.latest_leq_db = None
        self.latest_leq_is_complete = False

        # Time series of measurement values for JSON export.
        # One entry is stored approximately once per second during recording.
        self.measurement_history = []
        self.measurement_history_interval_seconds = 1.0
        self._last_history_sample_time = 0.0
        self._measurement_start_time = None

        # File recording
        self.storing_format = pyaudio.paFloat32
        self.should_store_recording = False
        self.recording_data_blocks = []
        self.recordings_dir = "/mnt/usb_share/recordings"
        os.makedirs(self.recordings_dir, exist_ok=True)
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream"""
        # Convert byte data to numpy array (32-bit PCM, googlevoicehat I2S driver)
        raw_audio_data = np.frombuffer(in_data, dtype=np.int32)
        
        # ICS43434 is 24-bit MSB-justified in 32-bit words, shift right by 8
        audio_data = raw_audio_data >> 8
        
        # Normalize to float [-1.0, 1.0] (24-bit range = 2^23)
        audio_float = audio_data.astype(np.float32) / 8388608.0

        # Convert multi-channel audio to mono before SPL/Leq processing.
        # PyAudio's frame_count is the number of time samples per channel.
        # If audio_float contains more values than frame_count, the extra values are channels.
        if frame_count > 0 and len(audio_float) > frame_count:
            channels = len(audio_float) // frame_count
            audio_float = audio_float[:frame_count * channels]
            audio_float = audio_float.reshape(frame_count, channels).mean(axis=1)

        # Store to audio file
        if self.should_store_recording:
            self.store_recording(audio_float)
        
        # If a Leq measurement is active, process the current audio block.
        # Once the selected duration is complete, store the final Leq value for the UI and export.
        if self.audio_processor.leq_is_running:
            leq_db, leq_is_complete = self.audio_processor.process_leq_measurement(audio_float)

            if leq_is_complete:
                self.latest_leq_db = float(leq_db)
                self.latest_leq_is_complete = True
                print(f"Leq complete: {self.latest_leq_db:.2f} dB")
            else:
                self.latest_leq_is_complete = False

        # Compute audio metrics
        self.latest_raw_spl_db = float(self.audio_processor.compute_spl_db(audio_float))
        self.latest_spl_db = float(self.latest_raw_spl_db + self.calibration_offset_db)
        self.latest_rms = float(self.audio_processor.compute_rms(audio_float))
        self.latest_peak = float(self.audio_processor.compute_peak(audio_float))

        # Compute filterband levels and A-weighting
        filtered_signals = self.audio_processor.apply_filterbank(audio_float, self.filterbank)
        self.latest_filterband_spl_db = [
            float(max(-120.0, self.audio_processor.compute_spl_db(signal)))
            for signal in filtered_signals
        ]
        self.latest_a_weighted_spl_db = float(max(-120.0, self.audio_processor.compute_a_weighting(filtered_signals)))

        # Time weighting
        fast_db = self.audio_processor.compute_fast_state(audio_float)
        slow_db = self.audio_processor.compute_slow_state(audio_float)

        self.latest_fast_state = float(fast_db + self.calibration_offset_db)
        self.latest_slow_state = float(slow_db + self.calibration_offset_db)

        # Store timestamped measurement values for JSON export.
        self._store_measurement_history_sample()
        
        return (in_data, pyaudio.paContinue)
    
    def _store_measurement_history_sample(self):
        """
        Store one timestamped measurement sample for JSON export.

        The values are stored once per second instead of every audio callback.
        """
        if self._measurement_start_time is None:
            return

        now = time.monotonic()

        if now - self._last_history_sample_time < self.measurement_history_interval_seconds:
            return

        elapsed_seconds = now - self._measurement_start_time

        sample = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "elapsed_seconds": round(elapsed_seconds, 3),

            "z_weighted_spl_db": self._safe_float(self.latest_spl_db),
            "raw_spl_db": self._safe_float(getattr(self, "latest_raw_spl_db", None)),
            "rms": self._safe_float(self.latest_rms),
            "peak": self._safe_float(self.latest_peak),
            "a_weighted_spl_db": self._safe_float(self.latest_a_weighted_spl_db),

            "fast_db": self._safe_float(self.latest_fast_state),
            "slow_db": self._safe_float(self.latest_slow_state),

            "peak_linear": self._safe_float(self.latest_peak),
            "peak_dbfs": self._safe_float(self._linear_to_dbfs(self.latest_peak)),
        }

        self.measurement_history.append(sample)
        self._last_history_sample_time = now


    # gives back the dBFS (fulls sclae digital signal) value. used for the peak:dBFS in the export
    def _linear_to_dbfs(self, value):
        if value is None or value <= 0:
            return None
        return 20 * np.log10(value)


    def _safe_float(self, value):
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    
    def calibrate_microphone(self, reference_db):
        """Calculate calibration offset from the current detected SPL."""
        self.calibration_offset_db = float(reference_db) - self.latest_raw_spl_db

        return {
            "reference_db": float(reference_db),
            "measured_db": self.latest_raw_spl_db,
            "offset_db": self.calibration_offset_db,
        }

    def start_recording(self):
        """Start recording from the microphone"""

        # Reset exported measurement history for the new measurement.
        self.measurement_history = []
        self._last_history_sample_time = 0.0
        self._measurement_start_time = time.monotonic()

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
            file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".wav"
            self.write_recording_to_file(os.path.join(self.recordings_dir, file_name))

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