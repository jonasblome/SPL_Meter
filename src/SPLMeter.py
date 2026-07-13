import AudioDeviceManager
import AudioDeviceSimulator
import UIHandler
import AudioProcessor

class SPLMeter:
    def __init__(self, simulate=False, wav_path=None):
        print("SPLMeter: Initializing")

        self.audio_processor = AudioProcessor.AudioProcessor()

        if simulate and wav_path:
            self.audio_device_manager = AudioDeviceSimulator.AudioDeviceSimulator(
                wav_path=wav_path,
                chunk_size=1024,
                audio_processor=self.audio_processor
            )
        else:
            self.audio_device_manager = AudioDeviceManager.AudioDeviceManager(
                sample_rate=48000,
                chunk_size=1024,
                device_index=2, # set to 0 for Pi microphone, adjust as needed
                audio_processor=self.audio_processor
            )
        self.audio_device_manager.list_devices()

        self.ui_handler = UIHandler.UIHandler(self.audio_device_manager)

    def run(self):
        self.ui_handler.run()
