import sys
import time
import threading
from pathlib import Path
import streamlit as st
from AudioDeviceManager import AudioDeviceManager

class UIHandler:
    def __init__(self, audio_device_manager):
        self.audio_device_manager = audio_device_manager

        print("UIHandler: Initializing")

        # Make sure src path is available
        CURRENT_DIR = Path(__file__).resolve().parent
        sys.path.insert(0, str(CURRENT_DIR))

        st.set_page_config(
            page_title="SPL Meter UI",
            page_icon="🎙️",
            layout="centered",
        )

        st.title("🎙️ SPL Meter Web UI")
        st.write("Simple web interface for the Raspberry Pi SPL Meter.")

        if "reader" not in st.session_state:
            st.session_state.reader = self.audio_device_manager

        if "recording_thread" not in st.session_state:
            st.session_state.recording_thread = None

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Start Measurement"):
                self.start_recording_thread()
                st.success("Measurement started.")

        with col2:
            if st.button("Stop Measurement"):
                self.stop_recording_thread()
                st.warning("Measurement stopped.")

        st.divider()
        
        weighting = st.radio(
            "Time Weighting",
            ["Fast", "Slow"],
            horizontal=True
        )

        self.audio_device_manager.time_weighting = weighting

        status = "Running" if self.audio_device_manager.is_recording else "Stopped"
        st.subheader(f"Status: {status}")

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        metric_col1.metric("SPL", f"{self.audio_device_manager.latest_spl_db:.2f} dB")
        metric_col2.metric("RMS", f"{self.audio_device_manager.latest_rms:.2f}")
        metric_col3.metric("Peak", f"{self.audio_device_manager.latest_peak:.2f}")
        metric_col4.metric("Time Weighted", f"{self.audio_device_manager.latest_time_weighted_value:.2f}")

        st.divider()

        st.info(
            "This UI reads the latest RMS, SPL and peak values from the audio callback."
        )

        if st.button("Refresh values"):
            st.rerun()
        
        # time.sleep(0.2)
        # st.rerun()

    def start_recording_thread(self):
        if st.session_state.recording_thread is None or not st.session_state.recording_thread.is_alive():
            thread = threading.Thread(target=self.audio_device_manager.start_recording, daemon=True)
            st.session_state.recording_thread = thread
            thread.start()

    def stop_recording_thread(self):
        if st.session_state.recording_thread is not None and st.session_state.recording_thread.is_alive():
            self.audio_device_manager.stop_recording()
            st.session_state.recording_thread.join()