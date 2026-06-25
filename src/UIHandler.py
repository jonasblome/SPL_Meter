import sys
import time
import threading
import numpy as np
from pathlib import Path
import streamlit as st
import helpers

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

        # Add display placeholders for audio metrics
        c1, c2, c3, c4, c5 = st.columns(5)

        spl_metric = c1.empty()
        rms_metric = c2.empty()
        peak_metric = c3.empty()
        time_weighted_metric = c4.empty()
        a_weighted_metric = c5.empty()

        # Add level meters for filterbands
        st.subheader("Filterband SPL Levels (dB)")
        filterband_cols = st.columns(len(helpers.frequency_weights_octave))
        filterband_metrics = [col.empty() for col in filterband_cols]

        def vertical_bar(percent: float, height: int = 200):
            # Ensure percent is between 0.0 and 1.0
            percent_filled = max(0.0, min(1.0, percent))
            
            # Calculate pixel heights
            filled_pixels = int(height * percent_filled)
            empty_pixels = height - filled_pixels
            
            # Create the vertical bar using inline CSS flex/divs
            bar_html = f"""
            <div style="
                display: flex;
                flex-direction: column-reverse;
                width: 30px;
                height: {height}px;
                background-color: #f0f2f6;
                border-radius: 4px; 
                border: 1px solid #e1e4e8;
                margin: 0 auto;">
                <div style="height: {filled_pixels}px; background-color: #ff4b4b; border-radius: 0 0 4px 4px;"></div>
            </div>
            <p style="text-align: center; font-family: sans-serif; margin-top: 5px;">{int(percent_filled * 100)}%</p>
            """
            st.markdown(bar_html, unsafe_allow_html=True)

        def render_data():
            # Single values
            spl_metric.metric("SPL", f"{st.session_state.audio_device_manager.latest_spl_db:.1f} dB")
            rms_metric.metric("RMS", f"{st.session_state.audio_device_manager.latest_rms:.1f}")
            peak_metric.metric("Peak", f"{st.session_state.audio_device_manager.latest_peak:.1f}")
            time_weighted_metric.metric("Time Weighted", f"{st.session_state.audio_device_manager.latest_time_weighted_value:.1f}")
            a_weighted_metric.metric("A-Weighted", f"{st.session_state.audio_device_manager.latest_a_weighted_spl_db:.1f} dB")

            # Filterband visualization
            if len(st.session_state.audio_device_manager.latest_filterband_spl_db) == len(filterband_metrics):
                for i, (band, freq) in enumerate(zip(filterband_metrics, list(helpers.frequency_weights_octave.keys()))):
                    spl_value = st.session_state.audio_device_manager.latest_filterband_spl_db[i]
                    normalized_spl = (spl_value + 100.0) / 200.0
                    clipped_value = np.clip(normalized_spl, 0, 1)

                    with band.container():
                        vertical_bar(float(clipped_value), height=int(150))
                        st.write(f"{spl_value:.1f}")
                        st.write("dB")
                        st.write(f"{int(freq)}")
                        st.write("Hz")

        render_data()

        while st.session_state.audio_device_manager.is_recording:
            render_data()
            time.sleep(0.05)

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
