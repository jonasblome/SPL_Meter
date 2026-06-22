import sys
import time
import threading
from pathlib import Path

import streamlit as st

# Make sure src path is available
CURRENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CURRENT_DIR))

from audio_input import ICS43434Reader


st.set_page_config(
    page_title="SPL Meter UI",
    page_icon="🎙️",
    layout="centered",
)

st.title("🎙️ SPL Meter Web UI")
st.write("Simple web interface for the Raspberry Pi SPL Meter.")

if "reader" not in st.session_state:
    st.session_state.reader = ICS43434Reader(
        sample_rate=48000,
        chunk_size=1024,
        device_index=0,
    )

if "recording_thread" not in st.session_state:
    st.session_state.recording_thread = None

reader = st.session_state.reader


def start_recording_thread():
    if st.session_state.recording_thread is None or not st.session_state.recording_thread.is_alive():
        thread = threading.Thread(target=reader.start_recording, daemon=True)
        st.session_state.recording_thread = thread
        thread.start()


col1, col2 = st.columns(2)

with col1:
    if st.button("Start Measurement"):
        start_recording_thread()
        st.success("Measurement started.")

with col2:
    if st.button("Stop Measurement"):
        reader.stop_recording()
        st.warning("Measurement stopped.")


st.divider()
# ===== Time Weighting  =====
weighting = st.radio(
    "Time Weighting",
    ["Fast", "Slow"],
    horizontal=True
)

reader.time_weighting = weighting

status = "Running" if reader.is_recording else "Stopped"
st.subheader(f"Status: {status}")

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric("SPL", f"{reader.latest_spl_db:.2f} dB")
metric_col2.metric("RMS", f"{reader.latest_rms:.6f}")
metric_col3.metric("Peak", f"{reader.latest_peak:.6f}")

st.divider()

st.info(
    "This UI reads the latest RMS, SPL and peak values from the audio callback. "
    "The audio processing remains inside audio_input.py."
)

if st.button("Refresh values"):
    st.rerun()
time.sleep(0.2)
st.rerun()