import AudioDeviceManager
import UIHandler
import AudioProcessor
import numpy as np

class SPLMeter:
    def __init__(self):
        print("SPLMeter: Initializing")

        self.audioDeviceManager = AudioDeviceManager.AudioDeviceManager()
        self.uiHandler = UIHandler.UIHandler()
        self.audioProcessor = AudioProcessor.AudioProcessor()

        # Testing audio processing with generated noise
        noise = self.generate_noise()
        spl_db = self.audioProcessor.compute_spl_db(noise)
        print(f"Computed SPL: {spl_db:.2f} dB")

    def generate_noise(self, duration_seconds=1, sample_rate=44100):
        num_samples = duration_seconds * sample_rate
        noise = np.random.normal(0, 1, num_samples)

        return noise