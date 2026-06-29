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
        self.audioDeviceManager.list_devices()
        self.audioDeviceManager.set_device_index(2) # Laptop microphone on Jonas' laptop, comment out if not needed!
        self.uiHandler = UIHandler.UIHandler(self.audioDeviceManager)