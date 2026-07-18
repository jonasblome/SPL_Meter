#!/usr/bin/env python3
"""
Audio Input Module for ICS43434 Microphone
Simple I2S microphone reader for Raspberry Pi Zero W
"""

import os
import time
import glob
import numpy as np
import helpers

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
    """
    Manages real-time audio input and stores the latest measurement values.

    The class opens the microphone stream, receives audio blocks in the
    PyAudio callback and updates the values used by the Web UI and JSON
    export. It also handles calibration, optional WAV recording, Leq/LAeq
    processing and timestamped measurement history.
    """
    
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
        self.calibration_offset_rms = 0.0
        self.calibration_offset_db = 0.0
        self.latest_spl_db = 0.0
        self.latest_rms = 0.0
        self.latest_peak = 0.0

        # Latest Leq values used by the UI stream and JSON export.
        self.latest_leq_db = None
        self.latest_leq_is_complete = False

        # Latest LAeq values used by the UI stream and JSON export.
        # LAeq is the equivalent continuous level of the A-weighted signal.
        self.latest_laeq_db = None
        self.latest_laeq_is_complete = False

        # Prepare filterbank in advance to only calculate once
        self.octave_filterbank = self.audio_processor.design_a_weighting_filterbank(self.sample_rate, is_octave=True)
        self.third_octave_filterbank = self.audio_processor.design_a_weighting_filterbank(self.sample_rate, is_octave=False)
        self.show_third_octave_bands = False
        self.active_filterbank_freqs = list(helpers.frequency_weights_octave.keys())
        self.num_bands = len(self.octave_filterbank)
        self.latest_filterband_spl_db = [0.0] * len(self.octave_filterbank)
        self.latest_a_weighted_spl_db = 0.0
       
        # Calibration
        self.octave_center_freqs = list(helpers.frequency_weights_octave.keys())
        self.calibration_band_index = min(
            range(len(self.octave_center_freqs)),
            key=lambda i: abs(float(self.octave_center_freqs[i]) - 1000.0)
        )
        self.is_calibrating = False
        self.calibration_status = "Not calibrated"
        self.calibration_reference_db = 94.0
        self.calibration_threshold_db = 50.0
        self.calibration_timeout_s = 5.0
        self.calibration_duration_s = 1.0
        self.calibration_started_at = None
        self.calibration_measurement_started = False
        self.calibration_power_sum = 0.0
        self.calibration_sample_count = 0
        self.calibration_measured_db = None
        self.latest_calibration_band_spl_db = 0.0
        
        # Time weighting
        self.latest_fast_state = 0.0
        self.latest_slow_state = 0.0

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
        self.recordings_dir = "./" # Use for personal laptop
        # self.recordings_dir = "/home/teamrapsberry/recordings_local" # Comment out for personal laptop
        # os.makedirs(self.recordings_dir, exist_ok=True) # Comment out for personal laptop

        # Maximum total size for stored recordings: 1.6 GB
        self.max_recordings_size_bytes = int(1.6 * 1024 * 1024 * 1024)

        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream"""
        # Convert byte data to numpy array (32-bit PCM, googlevoicehat I2S driver)
        raw_audio_data = np.frombuffer(in_data, dtype=np.int32)
        
        # ICS43434 is 24-bit MSB-justified in 32-bit words, shift right by 8
        audio_data = raw_audio_data >> 8
        
        # Normalize to float [-1.0, 1.0] (24-bit range = 2^23)
        audio_float = audio_data.astype(np.float32) / 8388608.0
        
        # Process microphone calibration if active
        self.process_microphone_calibration(audio_float)
        
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
        self.latest_rms = float(self.audio_processor.compute_rms(audio_float) + self.calibration_offset_rms)
        self.latest_peak = float(self.audio_processor.compute_peak(audio_float) + self.calibration_offset_rms)

        # Compute filterband levels and A-weighting (only active number of bands from the top)
        if self.show_third_octave_bands:
            total_num_bands = len(self.third_octave_filterbank)
            active_filterbank = self.third_octave_filterbank[total_num_bands - self.num_bands : total_num_bands]
            self.active_filterbank_freqs = list(helpers.frequency_weights_3rd_octave.keys())[total_num_bands - self.num_bands : total_num_bands]
        else:
            total_num_bands = len(self.octave_filterbank)
            active_filterbank = self.octave_filterbank[total_num_bands - self.num_bands : total_num_bands]
            self.active_filterbank_freqs = list(helpers.frequency_weights_octave.keys())[total_num_bands - self.num_bands : total_num_bands]
        
        filtered_signals = self.audio_processor.apply_filterbank(audio_float, active_filterbank)
        self.latest_filterband_spl_db = [
            float(max(-120.0, self.audio_processor.compute_spl_db(signal)))
            for signal in filtered_signals
        ]
        self.latest_a_weighted_spl_db = float(max(-120.0, self.audio_processor.compute_a_weighting(filtered_signals, not self.show_third_octave_bands) + self.calibration_offset_db))

        # If a LAeq measurement is active, process the current A-weighted audio block.
        # LAeq is calculated from A-weighted signal energy, not by averaging A-weighted dB values.
        if self.audio_processor.laeq_is_running:
            a_weighted_signal = self.audio_processor.compute_a_weighted_signal(filtered_signals)

            laeq_db, laeq_is_complete = self.audio_processor.process_laeq_measurement(
                a_weighted_signal
            )

            if laeq_is_complete:
                self.latest_laeq_db = float(laeq_db)
                self.latest_laeq_is_complete = True
                print(f"LAeq complete: {self.latest_laeq_db:.2f} dB")
            else:
                self.latest_laeq_is_complete = False

        # Compute Fast and Slow time-weighted levels.
        # Both values are returned in dB SPL and then shifted by the calibration offset.
        fast_db = self.audio_processor.compute_fast_state(audio_float)
        slow_db = self.audio_processor.compute_slow_state(audio_float)

        self.latest_fast_state = float(fast_db + self.calibration_offset_db)
        self.latest_slow_state = float(slow_db + self.calibration_offset_db)

        # Store timestamped measurement values for JSON export.
        self.store_measurement_history_sample()
        
        return (in_data, pyaudio.paContinue)
    
    def calibrate_microphone(self, reference_db=94.0, threshold_db=50.0):
        """Start microphone calibration using the 1 kHz octave band."""
        self.calibration_reference_db = float(reference_db)
        self.calibration_threshold_db = float(threshold_db)

        self.is_calibrating = True
        # Wait 5s to start
        self.calibration_status = (
            f"Waiting for 1 kHz signal above {self.calibration_threshold_db:.1f} dB..."
        )

        self.calibration_started_at = time.time()
        self.calibration_measurement_started = False
        self.calibration_power_sum = 0.0
        self.calibration_sample_count = 0
        self.calibration_measured_db = None
        self.latest_calibration_band_spl_db = 0.0
        
        return {
            "status": "started",
            "message": self.calibration_status,
            "reference_db": self.calibration_reference_db,
            "threshold_db": self.calibration_threshold_db,
        }
    
    def process_microphone_calibration(self, audio_float):
        """Process calibration using the 1 kHz octave band."""
        if not self.is_calibrating:
            return

        now = time.time()

        sos_1khz = self.octave_filterbank[self.calibration_band_index]
        filtered_1khz, band_spl_db = self.audio_processor.compute_filtered_band_spl_db(
            audio_float,
            sos_1khz
        )

        self.latest_calibration_band_spl_db = float(band_spl_db)

        # Step 1: wait for 1 kHz signal above threshold
        if not self.calibration_measurement_started:
            if band_spl_db >= self.calibration_threshold_db:
                self.calibration_measurement_started = True
                self.calibration_power_sum = 0.0
                self.calibration_sample_count = 0
                self.calibration_status = "1 kHz signal detected. Measuring for 1 second..."
            elif now - self.calibration_started_at >= self.calibration_timeout_s:
                self.is_calibrating = False
                self.calibration_status = "Calibration failed: no 1 kHz signal detected."
                return
            else:
                return

        # Step 2: collect exactly 1 second of filtered 1 kHz signal
        required_samples = int(self.sample_rate * self.calibration_duration_s)
        remaining_samples = required_samples - self.calibration_sample_count

        block = filtered_1khz[:remaining_samples]

        self.calibration_power_sum += float(
            np.sum(block.astype(np.float64) ** 2)
        )
        self.calibration_sample_count += len(block)

        # Step 3: finish calibration
        if self.calibration_sample_count >= required_samples:
            mean_square = self.calibration_power_sum / max(1, self.calibration_sample_count)
            measured_db = self.audio_processor.mean_square_to_spl_db(mean_square)

            self.calibration_offset_rms = mean_square
            self.calibration_measured_db = float(measured_db)
            self.calibration_offset_db = float(self.calibration_reference_db - measured_db)

            self.is_calibrating = False
            self.calibration_status = (
                f"Calibration complete. "
                f"Measured: {measured_db:.2f} dB, "
                f"Offset: {self.calibration_offset_db:.2f} dB"
            )
    
    def store_measurement_history_sample(self):
        """
        Store one timestamped measurement sample for JSON export.

        The audio callback runs many times per second. For the export, we only
        store one reduced measurement sample at the configured history interval.
        Filterband values are stored in the same order as the top-level
        filterband center frequencies in the JSON export.
        """
        if self._measurement_start_time is None:
            return

        now = time.monotonic()

        if now - self._last_history_sample_time < self.measurement_history_interval_seconds:
            return

        elapsed_seconds = now - self._measurement_start_time

        sample = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "elapsed_seconds": elapsed_seconds,

            "spl_db": self._safe_float(self.latest_spl_db),
            "raw_spl_db": self._safe_float(getattr(self, "latest_raw_spl_db", None)),
            "rms": self._safe_float(self.latest_rms),
            "peak": self._safe_float(self.latest_peak),

            "a_weighted_spl_db": self._safe_float(self.latest_a_weighted_spl_db),
            "fast_db": self._safe_float(self.latest_fast_state),
            "slow_db": self._safe_float(self.latest_slow_state),

            # Filterband SPL values for this timestamp.
            # The corresponding center frequencies are stored once in
            # export["filterbands"]["center_frequency_hz"].
            "filterband_spl_db": [
                self._safe_float(value)
                for value in getattr(self, "latest_filterband_spl_db", [])
            ],
        }

        self.measurement_history.append(sample)
        self._last_history_sample_time = now

    def _safe_float(self, value):
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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
                stream_callback=self.audio_callback
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
        self.cleanup_old_recordings()

    def cleanup_old_recordings(self):
        """Delete oldest recordings if total size exceeds 1.6 GB."""
        wav_files = glob.glob(os.path.join(self.recordings_dir, "*.wav"))
        if not wav_files:
            return

        total_size = sum(os.path.getsize(f) for f in wav_files)
        if total_size <= self.max_recordings_size_bytes:
            return

        # Sort by modification time, oldest first
        wav_files.sort(key=lambda f: os.path.getmtime(f))

        while wav_files and total_size > self.max_recordings_size_bytes:
            oldest = wav_files.pop(0)
            try:
                file_size = os.path.getsize(oldest)
                os.remove(oldest)
                total_size -= file_size
                print(f"Deleted old recording to free space: {oldest}")
            except OSError as e:
                print(f"Failed to delete old recording {oldest}: {e}")

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

    def set_num_bands(self, num_bands):
        """Set the number of filterbank bands to compute and display."""
        num_bands = int(num_bands)
        valid_num_bands = len(self.third_octave_filterbank) if self.show_third_octave_bands else len(self.octave_filterbank)

        if num_bands < 1 or num_bands > valid_num_bands:
            print(f"num_bands must be between 1 and {valid_num_bands}")
        else:
            self.num_bands = num_bands
        
        return self.num_bands