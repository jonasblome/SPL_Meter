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
            device_index=None,
            audio_processor=self.audioProcessor
            )
        # self.audioDeviceManager.set_device_index(2)
        self.uiHandler = UIHandler.UIHandler(self.audioDeviceManager)