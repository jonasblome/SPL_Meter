import AudioDeviceManager
import UIHandler
import AudioProcessor
import numpy as np
import streamlit as st

class SPLMeter:
    def __init__(self):
        print("SPLMeter: Initializing")

        if "audio_processor" not in st.session_state:
            st.session_state.audio_processor = AudioProcessor.AudioProcessor()

        if "audio_device_manager" not in st.session_state:
            st.session_state.audio_device_manager = AudioDeviceManager.AudioDeviceManager(
                sample_rate=48000,
                chunk_size=1024,
                device_index=6,
                audio_processor=st.session_state.audio_processor
            )

        self.audioProcessor = st.session_state.audio_processor
        self.audioDeviceManager = st.session_state.audio_device_manager
        # self.audioDeviceManager.set_device_index(2)
        self.uiHandler = UIHandler.UIHandler(self.audioDeviceManager)