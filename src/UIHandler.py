import time
import json
import threading
from flask import Flask, Response, request, jsonify

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPL Meter</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
        h1 { color: #333; }
        .controls { display: flex; gap: 12px; margin: 20px 0; align-items: center; }
        button { padding: 10px 24px; font-size: 16px; border: none; border-radius: 6px; cursor: pointer; }
        #btn-start { background: #4CAF50; color: white; }
        #btn-stop  { background: #f44336; color: white; }
        #btn-start:disabled, #btn-stop:disabled { opacity: 0.4; cursor: default; }
        .weighting { display: flex; gap: 16px; align-items: center; margin: 12px 0; }
        .weighting label { font-size: 16px; cursor: pointer; }
        .status { font-size: 18px; font-weight: bold; margin: 16px 0; }
        .status.running { color: #4CAF50; }
        .status.stopped { color: #f44336; }
        .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 24px; }
        .metric-box { background: white; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-label { font-size: 13px; color: #666; margin-bottom: 8px; }
        .metric-value { font-size: 28px; font-weight: bold; color: #333; }
        hr { border: none; border-top: 1px solid #ddd; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>🎙️ SPL Meter Web UI</h1>
    <p>Simple web interface for the Raspberry Pi SPL Meter.</p>
    <hr>
    <div class="controls">
        <button id="btn-start" onclick="startMeasurement()">Start Measurement</button>
        <button id="btn-stop"  onclick="stopMeasurement()" disabled>Stop Measurement</button>
    </div>
    <hr>
    <div class="weighting">
        <strong>Time Weighting:</strong>
        <label><input type="radio" name="weighting" value="Fast" checked onchange="setWeighting(this.value)"> Fast</label>
        <label><input type="radio" name="weighting" value="Slow" onchange="setWeighting(this.value)"> Slow</label>
    </div>
    <hr>
    <div class="status stopped" id="status">Status: Stopped</div>
    <hr>
    <div class="metrics">
        <div class="metric-box"><div class="metric-label">SPL</div><div class="metric-value" id="spl">-- dB</div></div>
        <div class="metric-box"><div class="metric-label">RMS</div><div class="metric-value" id="rms">--</div></div>
        <div class="metric-box"><div class="metric-label">Peak</div><div class="metric-value" id="peak">--</div></div>
        <div class="metric-box"><div class="metric-label">Time Weighted</div><div class="metric-value" id="tw">--</div></div>
    </div>
    <script>
        let evtSource = null;

        function startMeasurement() {
            fetch('/start', {method: 'POST'}).then(() => {
                document.getElementById('btn-start').disabled = true;
                document.getElementById('btn-stop').disabled = false;
                const s = document.getElementById('status');
                s.textContent = 'Status: Running';
                s.className = 'status running';
                startSSE();
            });
        }

        function stopMeasurement() {
            fetch('/stop', {method: 'POST'}).then(() => {
                document.getElementById('btn-start').disabled = false;
                document.getElementById('btn-stop').disabled = true;
                const s = document.getElementById('status');
                s.textContent = 'Status: Stopped';
                s.className = 'status stopped';
                if (evtSource) { evtSource.close(); evtSource = null; }
            });
        }

        function setWeighting(value) {
            fetch('/weighting', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({weighting: value})});
        }

        function startSSE() {
            if (evtSource) evtSource.close();
            evtSource = new EventSource('/stream');
            evtSource.onmessage = function(e) {
                const d = JSON.parse(e.data);
                document.getElementById('spl').textContent  = d.spl_db.toFixed(2) + ' dB';
                document.getElementById('rms').textContent  = d.rms.toFixed(6);
                document.getElementById('peak').textContent = d.peak.toFixed(6);
                document.getElementById('tw').textContent   = d.time_weighted.toFixed(6);
            };
        }
    </script>
</body>
</html>"""


class UIHandler:
    def __init__(self, audio_device_manager, host="0.0.0.0", port=8501):
        print("UIHandler: Initializing")
        self.audio_device_manager = audio_device_manager
        self.recording_thread = None
        self.app = Flask(__name__)
        self._register_routes()
        self.host = host
        self.port = port

    def _register_routes(self):
        adm = self.audio_device_manager

        @self.app.route("/")
        def index():
            return HTML_PAGE

        @self.app.route("/start", methods=["POST"])
        def start():
            self._start_recording_thread()
            return jsonify({"status": "started"})

        @self.app.route("/stop", methods=["POST"])
        def stop():
            self._stop_recording_thread()
            return jsonify({"status": "stopped"})

        @self.app.route("/weighting", methods=["POST"])
        def weighting():
            data = request.get_json()
            adm.time_weighting = data.get("weighting", "Fast")
            return jsonify({"weighting": adm.time_weighting})

        @self.app.route("/stream")
        def stream():
            def event_generator():
                while adm.is_recording:
                    payload = json.dumps({
                        "spl_db":        adm.latest_spl_db,
                        "rms":           adm.latest_rms,
                        "peak":          adm.latest_peak,
                        "time_weighted": adm.latest_time_weighted_value,
                    })
                    yield f"data: {payload}\n\n"
                    time.sleep(0.2)
            return Response(event_generator(), mimetype="text/event-stream")

        # Add toggle to store audio
        if st.toggle("Store Audio", True):
            st.write("Storing audio to file!")
            st.session_state.audio_device_manager.should_store_audio = True
        else:
            st.write("Disabled audio file recording!")
            st.session_state.audio_device_manager.should_store_audio = False

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

        # Add status
        status = st.session_state.measurement_status
        st.subheader(f"Status: {status}")

        st.divider()

        # Add display placeholders for audio metrics
        c1, c2, c3 = st.columns(3)
        a_weighted_metric = c1.empty()
        spl_metric = c2.empty()
        rms_metric = c3.empty()

        c4, c5, c6 = st.columns(3)
        peak_metric = c4.empty()
        fast_state_metric = c5.empty()
        slow_state_metric = c6.empty()

        # Add level meters for filterbands
        st.subheader("Filterband SPL Levels (dB)")
        filterband_cols = st.columns(len(helpers.frequency_weights_octave))
        filterband_metrics = [col.empty() for col in filterband_cols]

        def render_vertical_bar(percent: float, height: int = 200):
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
            """
            st.markdown(bar_html, unsafe_allow_html=True)

        def render_data():
            # Single values
            a_weighted_metric.metric("A-Weighted", f"{st.session_state.audio_device_manager.latest_a_weighted_spl_db:.1f} dB")
            spl_metric.metric("SPL", f"{st.session_state.audio_device_manager.latest_spl_db:.1f} dB")
            rms_metric.metric("RMS", f"{st.session_state.audio_device_manager.latest_rms:.1f}")
            peak_metric.metric("Peak", f"{st.session_state.audio_device_manager.latest_peak:.1f}")
            fast_state_metric.metric("Fast", f"{st.session_state.audio_device_manager.latest_fast_state:.1f}")
            slow_state_metric.metric("Slow", f"{st.session_state.audio_device_manager.latest_slow_state:.1f}")

            # Don't display filterbands if not yet calculated
            if len(st.session_state.audio_device_manager.latest_filterband_spl_db) != len(filterband_metrics):
                return

            # Filterband visualization            
            for i, (band, freq) in enumerate(zip(filterband_metrics, list(helpers.frequency_weights_octave.keys()))):
                spl_value = st.session_state.audio_device_manager.latest_filterband_spl_db[i]
                normalized_spl = (spl_value + 100.0) / 200.0
                clipped_value = np.clip(normalized_spl, 0, 1)

                with band.container():
                    render_vertical_bar(float(clipped_value), height=int(150))
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
    def _start_recording_thread(self):
        if self.recording_thread is None or not self.recording_thread.is_alive():
            self.recording_thread = threading.Thread(
                target=self.audio_device_manager.start_recording, daemon=True
            )
            self.recording_thread.start()

    def _stop_recording_thread(self):
        self.audio_device_manager.stop_recording()
        thread = self.recording_thread
        self.recording_thread = None
        if thread is not None:
            thread.join(timeout=2)
            if thread.is_alive():
                print("Warning: recording thread did not exit within timeout.")

    def run(self):
        print(f"UIHandler: Starting Flask server on http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, threaded=True)
