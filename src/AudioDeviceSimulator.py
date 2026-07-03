#!/usr/bin/env python3
"""
Audio Simulator for testing without a physical microphone.
Reads a WAV file and simulates the AudioDeviceManager interface.
"""

import time
import wave
import numpy as np


class AudioDeviceSimulator:
    """Simulates AudioDeviceManager using a WAV file as audio source"""

    def __init__(self, wav_path, chunk_size=1024, audio_processor=None):
        print("AudioDeviceSimulator: Initializing")
        self.wav_path = wav_path
        self.chunk_size = chunk_size
        self.is_recording = False

        # Audio processing
        self.audio_processor = audio_processor
        self.latest_rms = 0.0
        self.latest_spl_db = 0.0
        self.latest_peak = 0.0
        # Prepare filterbank in advance to only calculate once
        self.filterbank = self.audio_processor.design_a_weighting_filterbank(self.sample_rate, is_octave=True)
        self.latest_filterband_spl_db = [0.0] * len(self.filterbank)
        self.latest_a_weighted_spl_db = 0.0
        self.latest_fast_state = 0.0
        self.latest_slow_state = 0.0

        with wave.open(self.wav_path, "rb") as wf:
            self.sample_rate = wf.getframerate()
            self.num_channels = wf.getnchannels()
            self.sample_width = wf.getsampwidth()
            total_frames = wf.getnframes()
            raw = wf.readframes(total_frames)

        if self.sample_width == 2:
            self._audio_int = np.frombuffer(raw, dtype=np.int16)
            self._audio_float = self._audio_int.astype(np.float32) / 32768.0
        elif self.sample_width == 4:
            self._audio_int = np.frombuffer(raw, dtype=np.int32)
            self._audio_float = self._audio_int.astype(np.float32) / 2147483648.0
        else:
            raise ValueError(f"Unsupported sample width: {self.sample_width} bytes")

        if self.num_channels > 1:
            self._audio_float = self._audio_float[::self.num_channels]

        print(f"AudioSimulator: Loaded '{wav_path}' — "
              f"{self.sample_rate} Hz, {self.num_channels}ch, "
              f"{len(self._audio_float)} samples")

    def start_recording(self):
        """Simulate recording by looping through the WAV file chunk by chunk"""
        self.is_recording = True
        print(f"AudioSimulator: Starting playback at {self.sample_rate} Hz...")
        print("Press Ctrl+C to stop")

        seconds_per_chunk = self.chunk_size / self.sample_rate
        total_samples = len(self._audio_float)
        pos = 0

        try:
            while self.is_recording:
                chunk = self._audio_float[pos:pos + self.chunk_size]

                if len(chunk) < self.chunk_size:
                    chunk = np.concatenate([
                        chunk,
                        self._audio_float[:self.chunk_size - len(chunk)]
                    ])
                    pos = self.chunk_size - (total_samples - pos)
                else:
                    pos += self.chunk_size

                if pos >= total_samples:
                    pos = 0

                self._process_chunk(chunk)
                time.sleep(seconds_per_chunk)

        except KeyboardInterrupt:
            print("\nAudioSimulator: Stopped by user")
        finally:
            self.is_recording = False

    def stop_recording(self):
        """Stop the simulation"""
        self.is_recording = False

    def _process_chunk(self, audio_float):
        """Process one chunk — same logic as AudioDeviceManager._audio_callback"""
        self.latest_rms = float(self.audio_processor.compute_rms(audio_float))
        self.latest_spl_db = float(self.audio_processor.compute_spl_db(audio_float))
        self.latest_peak = float(self.audio_processor.compute_peak(audio_float))

        # Compute filterband levels and A-weighting
        filtered_signals = self.audio_processor.apply_filterbank(audio_float, self.filterbank)
        self.latest_filterband_spl_db = [
            float(max(-120.0, self.audio_processor.compute_spl_db(signal)))
            for signal in filtered_signals
        ]
        self.latest_a_weighted_spl_db = float(max(-120.0, self.audio_processor.compute_a_weighting(filtered_signals)))

        # Time weighting
        self.latest_fast_state = float(self.audio_processor.compute_fast_state(audio_float))
        self.latest_slow_state = float(self.audio_processor.compute_slow_state(audio_float))

        # Output raw data
        # print(f"RMS: {self.latest_rms:.2f}, SPL: {self.latest_spl_db:.2f} dB, "
        #       f"Peak: {self.latest_peak:.2}, Time Weighted: {self.latest_a_weighted_spl_db:.2f}")
