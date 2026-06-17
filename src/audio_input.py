#!/usr/bin/env python3
"""
Audio Input Module for ICS43434 Microphone
Simple I2S microphone reader for Raspberry Pi Zero W
"""

import time
import numpy as np
try:
    import pyaudio
except ImportError:
    print("pyaudio not installed. Please install with: pip install pyaudio")
    exit(1)


class ICS43434Reader:
    """Simple reader for ICS43434 I2S microphone"""
    
    def __init__(self, sample_rate=44100, chunk_size=1024, device_index=0):
        """
        Initialize the microphone reader
        
        Args:
            sample_rate (int): Audio sample rate in Hz
            chunk_size (int): Number of samples per chunk
            device_index (int): PyAudio device index to use
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.device_index = device_index
        self.is_recording = False
        self.audio = None
        self.stream = None
        
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback function for audio stream"""
        # Convert byte data to numpy array (32-bit PCM, googlevoicehat I2S driver)
        audio_data = np.frombuffer(in_data, dtype=np.int32)
        
        # ICS43434 is 24-bit MSB-justified in 32-bit words, shift right by 8
        audio_data = audio_data >> 8
        
        # Normalize to float [-1.0, 1.0] (24-bit range = 2^23)
        audio_float = audio_data.astype(np.float32) / 8388608.0
        
        # Calculate RMS (Root Mean Square) for simple SPL indication
        rms = np.sqrt(np.mean(audio_float**2))
        
        # Simple SPL calculation (reference: 20 micropascals)
        if rms > 0:
            spl_db = 20 * np.log10(rms / 0.00002)
        else:
            spl_db = -np.inf
            
        # Output raw data
        print(f"RMS: {rms:.6f}, SPL: {spl_db:.2f} dB, Max: {np.max(np.abs(audio_float)):.6f}")
        
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
                channels=2,
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
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
        if self.audio:
            self.audio.terminate()
            self.audio = None
    
    def list_devices(self):
        """List available audio devices"""
        audio = pyaudio.PyAudio()
        print("Available audio devices:")
        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            print(f"  {i}: {info['name']} (inputs: {info['maxInputChannels']})")
        audio.terminate()


def main():
    """Main function for testing"""
    print("ICS43434 Microphone Reader")
    print("=" * 40)
    
    # Create reader instance (device_index=0 = googlevoicehat I2S microphone)
    reader = ICS43434Reader(sample_rate=48000, chunk_size=1024, device_index=0)
    
    # List available devices
    reader.list_devices()
    
    # Start recording
    reader.start_recording()


if __name__ == "__main__":
    main()
