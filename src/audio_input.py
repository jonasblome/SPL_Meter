#!/usr/bin/env python3
"""
Audio Input Module for ICS43434 Microphone
Simple I2S microphone reader for Raspberry Pi Zero W
"""

import time
import numpy as np
try:
    import sounddevice as sd
except ImportError:
    print("sounddevice not installed. Please install with: pip install sounddevice")
    exit(1)


class ICS43434Reader:
    """Simple reader for ICS43434 I2S microphone"""
    
    def __init__(self, sample_rate=44100, chunk_size=1024):
        """
        Initialize the microphone reader
        
        Args:
            sample_rate (int): Audio sample rate in Hz
            chunk_size (int): Number of samples per chunk
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_recording = False
        
        # I2S device configuration for Raspberry Pi
        self.device = 'bcm2835_i2s'  # Standard I2S device on Raspberry Pi
        
    def start_recording(self):
        """Start recording from the microphone"""
        try:
            self.is_recording = True
            print(f"Starting recording at {self.sample_rate} Hz...")
            print("Press Ctrl+C to stop recording")
            
            # Audio callback function
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"Audio status: {status}")
                
                # Calculate RMS (Root Mean Square) for simple SPL indication
                rms = np.sqrt(np.mean(indata**2))
                
                # Simple SPL calculation (reference: 20 micropascals)
                if rms > 0:
                    spl_db = 20 * np.log10(rms / 0.00002)
                else:
                    spl_db = -np.inf
                    
                # Output raw data
                print(f"RMS: {rms:.6f}, SPL: {spl_db:.2f} dB, Max: {np.max(np.abs(indata)):.6f}")
            
            # Start the audio stream
            with sd.InputStream(
                device=self.device,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=audio_callback,
                dtype='float32'
            ):
                while self.is_recording:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
        except Exception as e:
            print(f"Error during recording: {e}")
        finally:
            self.is_recording = False
    
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
    
    def list_devices(self):
        """List available audio devices"""
        print("Available audio devices:")
        print(sd.query_devices())


def main():
    """Main function for testing"""
    print("ICS43434 Microphone Reader")
    print("=" * 40)
    
    # Create reader instance
    reader = ICS43434Reader(sample_rate=44100, chunk_size=1024)
    
    # List available devices
    reader.list_devices()
    
    # Start recording
    reader.start_recording()


if __name__ == "__main__":
    main()
