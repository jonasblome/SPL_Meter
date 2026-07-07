import AudioDeviceManager
import AudioDeviceSimulator
import UIHandler
import AudioProcessor
import threading
# import CommandLineHandler

class SPLMeter:
    def __init__(self,
                 should_simulate=False,
                 wav_path=None):
        print("SPLMeter: Initializing")

        self.recording_thread = None
        self.audio_processor = AudioProcessor.AudioProcessor()

        if should_simulate and wav_path:
            self.audio_device_manager = AudioDeviceSimulator.AudioDeviceSimulator(
                wav_path=wav_path,
                chunk_size=1024,
                audio_processor=self.audio_processor
            )
        else:
            self.audio_device_manager = AudioDeviceManager.AudioDeviceManager(
                sample_rate=48000,
                chunk_size=1024,
                device_index=3, # set to 0 for Pi microphone, adjust as needed
                audio_processor=self.audio_processor
            )
        self.audio_device_manager.list_devices()

        # self.commandLineHandler = CommandLineHandler.CommandLineHandler(self.audioDeviceManager)

    def run(self):
        self.ui_handler = UIHandler.UIHandler(self.audio_device_manager)
        self.ui_handler.run()

    def start_recording_thread(self):
        if self.recording_thread is None or not self.recording_thread.is_alive():
            self.recording_thread = threading.Thread(
                target=self.audio_device_manager.start_recording, daemon=True
            )
            self.recording_thread.start()

    def stop_recording_thread(self):
        self.audio_device_manager.stop_recording()
        thread = self.recording_thread
        self.recording_thread = None
        if thread is not None:
            thread.join(timeout=2)
            if thread.is_alive():
                print("Warning: recording thread did not exit within timeout.")

    def calibrate(self, reference_db):
        self.audio_device_manager.calibrate_microphone(reference_db)
    
    def measure(self, length):
        def stop_measurement():
            self.stop_recording_thread()
            print("Measurement stopped")

        time_measurement = threading.Timer(length, stop_measurement)
        self.start_recording_thread()
        time_measurement.start()
        print(f"Starting fixed measurement with length {length}s")
