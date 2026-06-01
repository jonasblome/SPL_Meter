import AudioDeviceManager
import UIHandler
import AudioProcessor

class SPLMeter:
    def __init__(self):
        print("SPLMeter: Initializing")

        self.audioDeviceManager = AudioDeviceManager.AudioDeviceManager()
        self.uiHandler = UIHandler.UIHandler()
        self.audioProcessor = AudioProcessor.AudioProcessor()