import AudioDeviceManager
import UIHandler
import AudioProcessor
import numpy as np

class SPLMeter:
    def __init__(self):
        print("SPLMeter: Initializing")

        self.audioProcessor = AudioProcessor.AudioProcessor()
        self.audioDeviceManager = AudioDeviceManager.AudioDeviceManager(
            sample_rate=48000,
            chunk_size=1024,
            device_index=6,
            audio_processor=self.audioProcessor
            )
        self.uiHandler = UIHandler.UIHandler(self.audioDeviceManager)

    def generate_noise(self, duration_seconds=1, sample_rate=48000):
        num_samples = duration_seconds * sample_rate
        noise = np.random.normal(0, 1, num_samples)

        return noise