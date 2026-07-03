import time
import json
import threading
import helpers
from flask import Flask, Response, request, jsonify

HTML_PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPL Meter</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
        h1 { color: #333; }
        h3 { color: #333; }
        .controls { display: flex; gap: 12px; margin: 20px 0; align-items: center; }
        button { padding: 10px 24px; font-size: 16px; border: none; border-radius: 6px; cursor: pointer; }
        #btn-start { background: #4CAF50; color: white; }
        #btn-stop  { background: #f44336; color: white; }
        #btn-start:disabled, #btn-stop:disabled { opacity: 0.4; cursor: default; }
        .weighting { display: flex; gap: 16px; align-items: center; margin: 12px 0; }
        .weighting label { font-size: 16px; cursor: pointer; }
        .store-toggle { display: flex; align-items: center; gap: 8px; margin: 12px 0; font-size: 16px; cursor: pointer; }
        .status { font-size: 18px; font-weight: bold; margin: 16px 0; }
        .status.running { color: #4CAF50; }
        .status.stopped { color: #f44336; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 16px; margin-top: 24px; }
        .metric-box { background: white; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-label { font-size: 13px; color: #666; margin-bottom: 8px; }
        .metric-value { font-size: 28px; font-weight: bold; color: #333; }
        .filterband-section { margin-top: 24px; }
        .filterband-grid { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; }
        .filterband-box { display: flex; flex-direction: column; align-items: center; width: 60px; }
        .filterband-value {
            font-size: 14px;
            font-weight: bold;
            margin-bottom: 4px;
            white-space: nowrap;
            text-align: center;
            line-height: 1.2;
        }
        .filterband-bar-container { display: flex; flex-direction: column-reverse; width: 30px; height: 150px; background: #f0f2f6; border-radius: 4px; border: 1px solid #e1e4e8; }
        .filterband-bar-fill { background: #ff4b4b; border-radius: 0 0 4px 4px; width: 100%; transition: height 0.2s; }
        .filterband-freq { font-size: 12px; color: #666; margin-top: 4px; }
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
    <label class="store-toggle">
        <input type="checkbox" id="store-audio" onchange="setStoreAudio(this.checked)">
        Store Audio
    </label>

    <div class="weighting">
        <strong>Calibration:</strong>
        <input id="reference-db" type="number" value="94" min="40" max="140" step="0.1">
        <span>dB</span>
        <button onclick="calibrateMicrophone()">Calibrate Microphone</button>
        <span id="calibration-status">Not calibrated</span>
    </div>
    <hr>
    <div class="status stopped" id="status">Status: Stopped</div>
    <hr>
    <div class="metrics">
        <div class="metric-box"><div class="metric-label">A-Weighted</div><div class="metric-value" id="a-weighted">-- dB</div></div>
        <div class="metric-box"><div class="metric-label">SPL</div><div class="metric-value" id="spl">-- dB</div></div>
        <div class="metric-box"><div class="metric-label">RMS</div><div class="metric-value" id="rms">--</div></div>
        <div class="metric-box"><div class="metric-label">Peak</div><div class="metric-value" id="peak">--</div></div>
        <div class="metric-box"><div class="metric-label">Fast</div><div class="metric-value" id="fast">--</div></div>
        <div class="metric-box"><div class="metric-label">Slow</div><div class="metric-value" id="slow">--</div></div>
        <div class="metric-box"><div class="metric-label">Time Weighted</div><div class="metric-value" id="tw">--</div></div>
    </div>
    <hr>
    <div class="filterband-section">
        <h3>Filterband SPL Levels (dB)</h3>
        <div class="filterband-grid" id="filterband-grid">
"""

HTML_PAGE_TAIL = """
        </div>
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
        function calibrateMicrophone() {
            const referenceDb = Number(
                document.getElementById('reference-db').value
            );

            fetch('/calibrate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({reference_db: referenceDb})
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('calibration-status').textContent =
                    'Offset: ' + data.offset_db.toFixed(2) + ' dB';
            });
        }
        function setStoreAudio(checked) {
            fetch('/store_recording', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({store: checked})});
        }

        function startSSE() {
            if (evtSource) evtSource.close();
            evtSource = new EventSource('/stream');
            evtSource.onmessage = function(e) {
                const d = JSON.parse(e.data);
                document.getElementById('a-weighted').textContent = d.a_weighted.toFixed(2) + ' dB';
                document.getElementById('spl').textContent  = d.spl_db.toFixed(2) + ' dB';
                document.getElementById('rms').textContent  = d.rms.toFixed(6);
                document.getElementById('peak').textContent = d.peak.toFixed(6);
                document.getElementById('fast').textContent = d.fast.toFixed(6);
                document.getElementById('slow').textContent = d.slow.toFixed(6);
                document.getElementById('tw').textContent   = d.time_weighted.toFixed(6);
                if (d.filterband_spl_db) {
                    d.filterband_spl_db.forEach((spl, i) => {
                        const normalized = Math.max(0.0, Math.min(1.0, (spl + 100.0) / 200.0));
                        const fill = document.getElementById('band-' + i + '-fill');
                        const value = document.getElementById('band-' + i + '-value');
                        if (fill) fill.style.height = (normalized * 100).toFixed(1) + '%';
                        if (value) value.textContent = spl.toFixed(1) + '\u00A0dB';
                    });
                }
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

    def _get_html_page(self):
        boxes = "".join(
            f'<div class="filterband-box" id="band-{i}">'
            f'<div class="filterband-value" id="band-{i}-value">--</div>'
            f'<div class="filterband-bar-container">'
            f'<div class="filterband-bar-fill" id="band-{i}-fill" style="height: 0%;"></div>'
            f'</div>'
            f'<div class="filterband-freq">{freq} Hz</div>'
            f'</div>'
            for i, freq in enumerate(helpers.frequency_weights_octave.keys())
        )
        return HTML_PAGE_HEAD + boxes + HTML_PAGE_TAIL

    def _register_routes(self):
        adm = self.audio_device_manager

        @self.app.route("/")
        def index():
            return self._get_html_page()

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
        @self.app.route("/calibrate", methods=["POST"])
        def calibrate():
            if not adm.is_recording:
                return jsonify({
                    "error": "Start measurement before calibration."
                }), 400

            data = request.get_json() or {}
            reference_db = float(data.get("reference_db", 94.0))

            result = adm.calibrate_microphone(reference_db)
            return jsonify(result)
        @self.app.route("/store_recording", methods=["POST"])
        def store_recording():
            data = request.get_json()
            adm.should_store_recording = bool(data.get("store", False))
            return jsonify({"store": adm.should_store_recording})

        @self.app.route("/stream")
        def stream():
            def event_generator():
                while adm.is_recording:
                    payload = json.dumps({
                        "a_weighted":    adm.latest_a_weighted_spl_db,
                        "spl_db":        adm.latest_spl_db,
                        "rms":           adm.latest_rms,
                        "peak":          adm.latest_peak,
                        "fast":          adm.latest_fast_state,
                        "slow":          adm.latest_slow_state,
                        "time_weighted": adm.latest_time_weighted_value,
                        "filterband_spl_db": adm.latest_filterband_spl_db,
                    })
                    yield f"data: {payload}\n\n"
                    time.sleep(0.2)
            return Response(event_generator(), mimetype="text/event-stream")

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
