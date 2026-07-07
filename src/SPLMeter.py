import AudioDeviceManager
import AudioDeviceSimulator
import UIHandler
import AudioProcessor

class SPLMeter:
    def __init__(self, simulate=False, wav_path=None):
        print("SPLMeter: Initializing")

        self.audioProcessor = AudioProcessor.AudioProcessor()

        if simulate and wav_path:
            self.audioDeviceManager = AudioDeviceSimulator.AudioDeviceSimulator(
                wav_path=wav_path,
                chunk_size=1024,
                audio_processor=self.audioProcessor
            )
        else:
            self.audioDeviceManager = AudioDeviceManager.AudioDeviceManager(
                sample_rate=48000,
                chunk_size=1024,
                device_index=1, # set to 0 for Pi microphone, adjust as needed
                audio_processor=self.audioProcessor
            )
        self.audioDeviceManager.list_devices()

        self.uiHandler = UIHandler.UIHandler(self.audioDeviceManager)

    def run(self):
        self.uiHandler.run()
