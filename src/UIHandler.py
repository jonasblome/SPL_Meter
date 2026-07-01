import sys
import time
import threading
from pathlib import Path
import streamlit as st

class UIHandler:
    def __init__(self, audio_device_manager):
        print("UIHandler: Initializing")

        self.audio_device_manager = audio_device_manager

        # Make sure src path is available
        CURRENT_DIR = Path(__file__).resolve().parent
        sys.path.insert(0, str(CURRENT_DIR))

        # Setup UI page
        st.set_page_config(
            page_title="SPL Meter UI",
            page_icon="🎙️",
            layout="centered",
        )

        # Set title and info
        st.title("🎙️ SPL Meter Web UI")
        st.write("Simple web interface for the Raspberry Pi SPL Meter.")

        if "recording_thread" not in st.session_state:
            st.session_state.recording_thread = None

        if "measurement_status" not in st.session_state:
            st.session_state.measurement_status = "Stopped"

        # Add start/stop measurement buttons
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
        
        # Add slow/fast time weighting selection 
        weighting = st.radio(
            "Time Weighting",
            ["Fast", "Slow"],
            horizontal=True
        )

        self.audio_device_manager.time_weighting = weighting

        st.divider()

        # Add status
        status = st.session_state.measurement_status
        st.subheader(f"Status: {status}")

        st.divider()

        # Add metrics display
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        metric_col1.metric("SPL", f"{self.audio_device_manager.latest_spl_db:.2f} dB")
        metric_col2.metric("RMS", f"{self.audio_device_manager.latest_rms:.6f}")
        metric_col3.metric("Peak", f"{self.audio_device_manager.latest_peak:.6f}")
        metric_col4.metric("Time Weighted", f"{self.audio_device_manager.latest_time_weighted_value:.6f}")

        # Trigger periodic rerun while recording is active
        if self.audio_device_manager.is_recording:
            time.sleep(0.2)
            st.rerun()

    def start_recording_thread(self):
        if st.session_state.recording_thread is None or not st.session_state.recording_thread.is_alive():
            st.session_state.measurement_status = "Running"
            thread = threading.Thread(target=st.session_state.audio_device_manager.start_recording, daemon=True)
            st.session_state.recording_thread = thread
            thread.start()

    def stop_recording_thread(self):
        st.session_state.measurement_status = "Stopped"
        if st.session_state.recording_thread is not None and st.session_state.recording_thread.is_alive():
            st.session_state.audio_device_manager.stop_recording()
            st.session_state.recording_thread.join(timeout=2)
            if st.session_state.recording_thread.is_alive():
                print("Warning: recording thread did not exit within timeout.")
