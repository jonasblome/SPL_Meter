#!/usr/bin/env python3
"""
Audio Simulator for testing without a physical microphone.
Reads a WAV file and simulates the AudioDeviceManager interface.
"""

import time
import wave
import numpy as np


class AudioSimulator:
    """Simulates AudioDeviceManager using a WAV file as audio source"""

    def __init__(self, wav_path, chunk_size=1024, audio_processor=None):
        print("AudioSimulator: Initializing")
        self.wav_path = wav_path
        self.chunk_size = chunk_size
        self.audio_processor = audio_processor

        self.is_recording = False
        self.time_weighting = "Fast"

        self.latest_rms = 0.0
        self.latest_spl_db = 0.0
        self.latest_peak = 0.0
        self.latest_time_weighted_value = 0.0

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
        rms = self.audio_processor.compute_rms(audio_float)
        spl_db = self.audio_processor.compute_spl_db(audio_float)
        peak = self.audio_processor.compute_peak(audio_float)

        if self.time_weighting == "Fast":
            tw = self.audio_processor.compute_fast_state(audio_float)
        else:
            tw = self.audio_processor.compute_slow_state(audio_float)

        self.latest_rms = float(rms)
        self.latest_spl_db = float(spl_db)
        self.latest_peak = float(peak)
        self.latest_time_weighted_value = float(tw)

        print(f"RMS: {self.latest_rms:.6f}, SPL: {self.latest_spl_db:.2f} dB, "
              f"Peak: {self.latest_peak:.6f}, Time Weighted: {self.latest_time_weighted_value:.6f}")
