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

        if "audio_device_manager" not in st.session_state:
            st.session_state.audio_device_manager = self.audio_device_manager

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

        # Add metrics display placeholders
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        spl_metric = metric_col1.empty()
        rms_metric = metric_col2.empty()
        peak_metric = metric_col3.empty()
        time_weighted_metric = metric_col4.empty()

        def render_metrics():
            spl_metric.metric("SPL", f"{st.session_state.audio_device_manager.latest_spl_db:.2f} dB")
            rms_metric.metric("RMS", f"{st.session_state.audio_device_manager.latest_rms:.2f}")
            peak_metric.metric("Peak", f"{st.session_state.audio_device_manager.latest_peak:.2f}")
            time_weighted_metric.metric("Time Weighted", f"{st.session_state.audio_device_manager.latest_time_weighted_value:.2f}")

        render_metrics()

        while st.session_state.audio_device_manager.is_recording:
            render_metrics()
            time.sleep(0.2)

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
