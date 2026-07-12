import time
import json
import threading
import helpers
from flask import Flask, Response, request, jsonify
from MeasurementExporter import MeasurementExporter
from datetime import datetime

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
    <div class="export">
        <button onclick="downloadJson()">Download JSON</button>
        </div>
    </div>
    <hr>
    <label class="store-toggle">
        <input type="checkbox" id="store-audio" onchange="setStoreAudio(this.checked)">
        Store Audio
    </label>
    <hr>
    <div class="Leq">
        <strong>Leq Duration:</strong>
        <select id="leq-duration" onchange="setLeqDuration(this.value)">
            <option value="0" selected>5 s</option>
            <option value="1">10 s</option>
            <option value="2">15 s</option>
            <option value="3">30 s</option>
            <option value="4">60 s</option>
            <option value="5">300 s</option>
        </select>
        <button onclick="startLeqMeasurement()">Start Leq</button>
    </div>
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
        <div class="metric-box"><div class="metric-label">Leq</div><div class="metric-value" id="leq">--</div></div>
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

        function setLeqDuration(index) {
            fetch('/leq_duration', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({index: Number(index)})
            });
        }

        function startLeqMeasurement() {
            fetch('/leq_start', {method: 'POST'}).then(() => {
                document.getElementById('leq').textContent = 'running...';
                startSSE();
            });
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

        function downloadJson() {
            window.location.href = '/export_json';
        }

        function startSSE() {
            if (evtSource) evtSource.close();
            evtSource = new EventSource('/stream');
            evtSource.onmessage = function(e) {
                const d = JSON.parse(e.data);
                document.getElementById('a-weighted').textContent = d.a_weighted.toFixed(2) + ' dB';
                document.getElementById('spl').textContent  = d.spl_db.toFixed(2) + ' dB';
                document.getElementById('rms').textContent  = d.rms.toFixed(2);
                document.getElementById('peak').textContent = d.peak.toFixed(2);
                document.getElementById('fast').textContent = d.fast.toFixed(2) + ' dB';
                document.getElementById('slow').textContent = d.slow.toFixed(2) + ' dB';
                if (d.leq_is_running) {
                    document.getElementById('leq').textContent = 'running...';
                } else if (d.leq_db !== null) {
                    document.getElementById('leq').textContent = d.leq_db.toFixed(2) + ' dB';
                }
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
    def __init__(self, audio_device_manager=None, host="0.0.0.0", port=8501):
        print("UIHandler: Initializing")

        # Available Leq measurement durations in seconds.
        # The UI can select one of these values by changing leq_duration_index.
        self.leq_durations_seconds = [5, 10, 15, 30, 60, 300]
        self.leq_duration_index = 0

        self.audio_device_manager = audio_device_manager

        # Available Leq measurement durations in seconds.
        # The selected index can later be controlled by the web UI.
        self.leq_durations_seconds = [5, 10, 15, 30, 60, 300]
        self.leq_duration_index = 0
        
        self.measurement_exporter = MeasurementExporter()
        self.recording_thread = None
        self.app = Flask(__name__)
        self._register_routes()
        self.host = host
        self.port = port


    def get_leq_duration_seconds(self):
        """Return the currently selected Leq measurement duration in seconds."""
        return self.leq_durations_seconds[self.leq_duration_index]
    
    def set_leq_duration_index(self, index):
        """Select a Leq duration by index."""
        if index < 0 or index >= len(self.leq_durations_seconds):
            raise ValueError("Invalid Leq duration index")

        self.leq_duration_index = index
        return self.get_leq_duration_seconds()

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
        device_manager = self.audio_device_manager

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
            device_manager.time_weighting = data.get("weighting", "Fast")
            return jsonify({"weighting": device_manager.time_weighting})
        
        @self.app.route("/leq_duration", methods=["POST"])
        def leq_duration():
            data = request.get_json()
            index = int(data.get("index", 0))

            duration_seconds = self.set_leq_duration_index(index)

            print(f"Leq duration set to {duration_seconds} s")

            return jsonify({
                "duration_seconds": duration_seconds
            })

        @self.app.route("/leq_start", methods=["POST"])
        def leq_start():
            duration_seconds = self.get_leq_duration_seconds()

            # Start audio processing automatically if it is not already running.
            # Otherwise the Leq measurement would not receive any audio blocks.
            if not device_manager.is_recording:
                self._start_recording_thread()

            device_manager.latest_leq_db = None
            device_manager.latest_leq_is_complete = False

            device_manager.audio_processor.start_leq_measurement(
                duration_seconds=duration_seconds,
                sample_rate=device_manager.sample_rate
            )

            print(f"Leq measurement started for {duration_seconds} s")

            return jsonify({
                "status": "started",
                "duration_seconds": duration_seconds
            })
            device_manager.time_weighting = data.get("weighting", "Fast")
            return jsonify({"weighting": device_manager.time_weighting})
        
        @self.app.route("/calibrate", methods=["POST"])
        def calibrate():
            if not device_manager.is_recording:
                return jsonify({
                    "error": "Start measurement before calibration."
                }), 400

            data = request.get_json() or {}
            reference_db = float(data.get("reference_db", 94.0))

            result = device_manager.calibrate_microphone(reference_db)
            return jsonify(result)
        
        @self.app.route("/store_recording", methods=["POST"])
        def store_recording():
            data = request.get_json()
            device_manager.should_store_recording = bool(data.get("store", False))
            return jsonify({"store": device_manager.should_store_recording})

        @self.app.route("/stream")
        def stream():
            def event_generator():
                while device_manager.is_recording:
                    payload = json.dumps({
                        "spl_db":        device_manager.latest_spl_db,
                        "rms":           device_manager.latest_rms,
                        "peak":          device_manager.latest_peak,
                        "a_weighted":    device_manager.latest_a_weighted_spl_db,
                        "fast":          device_manager.latest_fast_state,
                        "slow":          device_manager.latest_slow_state,
                        "filterband_spl_db": device_manager.latest_filterband_spl_db,

                        # Leq values for the web UI
                        "leq_db":             device_manager.latest_leq_db,
                        "leq_is_complete":    device_manager.latest_leq_is_complete,
                        "leq_is_running":     device_manager.audio_processor.leq_is_running,
                    })
                    yield f"data: {payload}\n\n"
                    time.sleep(0.05)  # 20 Hz update rate
            return Response(event_generator(), mimetype="text/event-stream")
        
        @self.app.route("/export_json", methods=["GET"])
        def export_json():
            if hasattr(self, "leq_durations_seconds") and hasattr(self, "leq_duration_index"):
                leq_duration_seconds = self.leq_durations_seconds[self.leq_duration_index]
            else:
                leq_duration_seconds = None

            measurement_data = self.measurement_exporter.create_measurement_snapshot(
                device_manager,
                leq_duration_seconds=leq_duration_seconds
            )

            json_string = self.measurement_exporter.to_json_string(measurement_data)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"spl_measurement_{timestamp}.json"

            return Response(
                json_string,
                mimetype="application/json",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )

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
