import AudioDeviceManager
import UIHandler
import AudioProcessor
import numpy as np

class SPLMeter:
    def __init__(self):
        print("SPLMeter: Initializing")

        self.audioDeviceManager = AudioDeviceManager.AudioDeviceManager(
            sample_rate=48000,
            chunk_size=1024,
            device_index=6,
            )
        self.audioProcessor = AudioProcessor.AudioProcessor()
        self.uiHandler = UIHandler.UIHandler(self.audioDeviceManager, self.audioProcessor)

        # Testing SPL computation
        # noise = self.generate_noise()
        # spl_db = self.audioProcessor.compute_spl_db(noise)
        # print(f"Computed SPL: {spl_db:.2f} dB")

        # Testing A-weighting
        # is_octave = True
        # a_weighting_filterbank = self.audioProcessor.design_a_weighting_filterbank(48000, is_octave)
        # filtered_signals = self.audioProcessor.apply_filterbank(noise, a_weighting_filterbank)
        # spl_a_weighted = self.audioProcessor.compute_a_weighting(filtered_signals, is_octave)
        # print(f"Computed A-weighted SPL: {spl_a_weighted:.2f} dB")

        # Output SPL for each band
        # spl_db_list = [self.audioProcessor.compute_spl_db(filtered_signal) for filtered_signal in filtered_signals]
        # for i, spl in enumerate(spl_db_list):
        #     print(f"Computed SPL for band {i+1}: {spl:.2f} dB")

    def generate_noise(self, duration_seconds=1, sample_rate=48000):
        num_samples = duration_seconds * sample_rate
        noise = np.random.normal(0, 1, num_samples)

        return noise