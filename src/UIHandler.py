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
        #calibration-div  { margin: 20px 0px; }
        #leq-div  { margin: 20px 0px; }
        #leq-result { width: 100px }
        .store-toggle { display: flex; align-items: center; gap: 8px; margin: 12px 0; font-size: 16px; cursor: pointer; }
        .status { font-size: 18px; font-weight: bold; margin: 16px 0; }
        .status.running { color: #4CAF50; }
        .status.stopped { color: #f44336; }
        .framerate { font-size: 14px; color: #666; margin: 4px 0; }
        .hint { font-size: 13px; color: #888; margin-left: 8px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 16px; margin-top: 24px; }
        .metric-box { background: white; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-label { font-size: 13px; color: #666; margin-bottom: 8px; }
        .metric-value { font-size: 28px; font-weight: bold; color: #333; }
        .level-meter {
            margin-top: 12px; }
        .level-bar {
            width: 100%;
            height: 16px;
            background: #ddd;
            border-radius: 8px;
            overflow: hidden; }
        .level-bar-fill {
            height: 100%;
            width: 0%;
            background: #4CAF50;
            transition: width 0.2s ease;}
        .level-ticks {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: #666;
            margin-top: 4px;}
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
        .filterband-bar-fill { background: #ff4b4b; border-radius: 0 0 4px 4px; width: 100%; transition: height 0.05s linear; will-change: height; }
        .filterband-freq { font-size: 12px; color: #666; margin-top: 4px; }
        hr { border: none; border-top: 1px solid #ddd; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>🎙️ SPL Meter Web UI</h1>
    <p>Simple web interface for the Raspberry Pi SPL Meter.</p>
    
    <hr>
    
    <h3>Prepare Measurement:</h3>

    <hr>

    <label class="store-toggle">
        <input type="checkbox" id="store-audio" onchange="setStoreAudio(this.checked)">
        Store Audio
    </label>
    
    <hr>

    <div class="num-bands">
        <strong>Number of Bands:</strong>
        <select id="num-bands" onchange="setNumBands(this.value)">
            <option value="4">4</option>
            <option value="6">6</option>
            <option value="8">8</option>
            <option value="10" selected>10</option>
        </select>
        <span class="hint">More bands look nicer but need more processing power.</span>
    </div>
    
    <hr>

    <div class="calibration">
        <strong id="calibration-div">Calibration:</strong>
        <div id="calibration-div">
            <span>Reference:</span>
            <input id="reference-db" type="number" value="94" min="40" max="140" step="0.1">
            <span>dB</span>
        </div>
        <div id="calibration-div">
            <span>Threshold:</span>
            <input id="threshold-db" type="number" value="50" min="0" max="140" step="0.1">
            <span>dB</span>
        </div>
        <div id="calibration-div">
            <button onclick="calibrateMicrophone()">Calibrate Microphone</button>
        </div>
        <div id="calibration-div">
            <span id="calibration-status">Not calibrated</span>
        </div>
    </div>

    <hr>
    
    <div class="controls">
        <button id="btn-start" onclick="startMeasurement()">Start Measurement</button>
        <button id="btn-stop"  onclick="stopMeasurement()" disabled>Stop Measurement</button>
    </div>
    <div class="status stopped" id="status">Status: Stopped</div>

    <hr>

    <div class="export">
        <button onclick="downloadJson()">Export to JSON</button>
    </div>
    
    <hr>
    
    <div class="Leq" id="leq-div">
        <strong>Leq Duration:</strong>
        <select id="leq-duration" onchange="setLeqDuration(this.value)">
            <option value="0" selected>5 s</option>
            <option value="1">10 s</option>
            <option value="2">15 s</option>
            <option value="3">30 s</option>
            <option value="4">60 s</option>
            <option value="5">300 s</option>
        </select>
    </div>
    <div id="leq-div">
        <button onclick="startLeqMeasurement()">Start Leq</button>
    </div>
    <div class="metric-box" id="leq-result">
        <div class="metric-label">Leq</div><div class="metric-value" id="leq">--</div>
    </div>
    
    <hr>
    
    <div class="framerate" id="framerate">Target: 60 FPS | Actual: -- FPS</div>
    <div class="metrics">
        <div class="metric-box"><div class="metric-label">Peak</div><div class="metric-value" id="peak">--</div></div>
        <div class="metric-box"><div class="metric-label">RMS</div><div class="metric-value" id="rms">--</div></div>

        <div class="metric-box">
            <div class="metric-label">SPL</div>
            <div class="metric-value" id="spl_db">-- dB</div>
            <div class="level-meter">
                <div class="level-bar">
                    <div class="level-bar-fill" id="spl-db-bar"></div>
                </div>
                <div class="level-ticks">
                    <span>30</span>
                    <span>50</span>
                    <span>70</span>
                    <span>90</span>
                    <span>110 dB</span>
                </div>
            </div>
        </div>

        <div class="metric-box">
            <div class="metric-label">A-Weighted</div>
            <div class="metric-value" id="a_weighted">-- dB</div>
            <div class="level-meter">
                <div class="level-bar">
                    <div class="level-bar-fill" id="a-weighted-bar"></div>
                </div>
                <div class="level-ticks">
                    <span>30</span>
                    <span>50</span>
                    <span>70</span>
                    <span>90</span>
                    <span>110 dB</span>
                </div>
            </div>
        </div>

        <div class="metric-box">
            <div class="metric-label">Fast</div>
            <div class="metric-value" id="fast">-- dB</div>
            <div class="level-meter">
                <div class="level-bar">
                    <div class="level-bar-fill" id="fast-bar"></div>
                </div>
                <div class="level-ticks">
                    <span>30</span>
                    <span>50</span>
                    <span>70</span>
                    <span>90</span>
                    <span>110 dB</span>
                </div>
            </div>
        </div>

        <div class="metric-box">
            <div class="metric-label">Slow</div>
            <div class="metric-value" id="slow">-- dB</div>
            <div class="level-meter">
                <div class="level-bar">
                    <div class="level-bar-fill" id="slow-bar"></div>
                </div>
                <div class="level-ticks">
                    <span>30</span>
                    <span>50</span>
                    <span>70</span>
                    <span>90</span>
                    <span>110 dB</span>
                </div>
            </div>
        </div>
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
        const TARGET_FPS = 60;
        let fpsHistory = [];

        function updateFramerate() {
            const now = performance.now();
            fpsHistory.push(now);
            // Keep only timestamps from the last second
            const cutoff = now - 1000;
            fpsHistory = fpsHistory.filter(t => t >= cutoff);
            const actualFps = fpsHistory.length;
            document.getElementById('framerate').textContent =
                `Target: ${TARGET_FPS} FPS | Actual: ${actualFps} FPS`;
        }

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
                document.getElementById('framerate').textContent = 'Target: ' + TARGET_FPS + ' FPS | Actual: -- FPS';
                fpsHistory = [];
                if (evtSource) { evtSource.close(); evtSource = null; }
            });
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
            const thresholdDb = Number(
                document.getElementById('threshold-db').value
            );

            document.getElementById('calibration-status').textContent =
                'Starting calibration...';

            fetch('/calibrate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    reference_db: referenceDb,
                    threshold_db: thresholdDb
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('calibration-status').textContent =
                    data.message || data.error || 'Calibration started';
                startSSE();
            });
        }

        function setStoreAudio(checked) {
            fetch('/store_recording', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({store: checked})});
        }

        function setNumBands(value) {
            const numBands = Number(value);
            fetch('/num_bands', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({num_bands: numBands})
            });
            updateBandVisibility(numBands);
        }

        function updateBandVisibility(numBands) {
            for (let i = 0; i < 12; i++) {
                const box = document.getElementById('band-' + i);
                if (box) {
                    box.style.display = i < numBands ? 'flex' : 'none';
                }
            }
        }

        // Apply initial visibility on page load
        updateBandVisibility(Number(document.getElementById('num-bands').value));
        function downloadJson() {
            window.location.href = '/export_json';
        }

        function dbToPercent(db, minDb = 20, maxDb = 130) {
            if (typeof db !== 'number' || !Number.isFinite(db)) {
                return 0;
            }

            const clamped = Math.max(minDb, Math.min(maxDb, db));
            return ((clamped - minDb) / (maxDb - minDb)) * 100;
        }

        function updateLevelBar(barId, db) {
            const bar = document.getElementById(barId);

            if (!bar) {
                return;
            }

            bar.style.width = dbToPercent(db).toFixed(1) + '%';
        }

        function startSSE() {
            if (evtSource) evtSource.close();
            evtSource = new EventSource('/stream');
            evtSource.onmessage = function(e) {
                updateFramerate();
                const d = JSON.parse(e.data);
                document.getElementById('peak').textContent = d.peak.toFixed(2);
                document.getElementById('rms').textContent  = d.rms.toFixed(2);

                if (d.spl_db !== null && d.spl_db !== undefined) {
                    document.getElementById('spl_db').textContent = d.spl_db.toFixed(2) + ' dB';
                    updateLevelBar('spl-db-bar', d.spl_db);
                } else {
                    document.getElementById('spl_db').textContent = '-- dB';
                    updateLevelBar('spl-db-bar', null);
                }

                if (d.a_weighted !== null && d.a_weighted !== undefined) {
                    document.getElementById('a_weighted').textContent = d.a_weighted.toFixed(2) + ' dB';
                    updateLevelBar('a-weighted-bar', d.a_weighted);
                } else {
                    document.getElementById('a_weighted').textContent = '-- dB';
                    updateLevelBar('a-weighted-bar', null);
                }

                if (d.fast !== null && d.fast !== undefined) {
                    document.getElementById('fast').textContent = d.fast.toFixed(2) + ' dB';
                    updateLevelBar('fast-bar', d.fast);
                } else {
                    document.getElementById('fast').textContent = '-- dB';
                    updateLevelBar('fast-bar', null);
                }

                if (d.slow !== null && d.slow !== undefined) {
                    document.getElementById('slow').textContent = d.slow.toFixed(2) + ' dB';
                    updateLevelBar('slow-bar', d.slow);
                } else {
                    document.getElementById('slow').textContent = '-- dB';
                    updateLevelBar('slow-bar', null);
                }

                if (d.leq_is_running) {
                    document.getElementById('leq').textContent = 'running...';
                } else if (d.leq_db !== null) {
                    document.getElementById('leq').textContent = d.leq_db.toFixed(2) + ' dB';
                }
                if (d.calibration) {
                    let calibrationText = d.calibration.status;

                    if (d.calibration.active) {
                        calibrationText +=
                            ' | 1 kHz: ' + d.calibration.band_spl_db.toFixed(2) + ' dB';
                    }

                    document.getElementById('calibration-status').textContent = calibrationText;
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
        
        @self.app.route("/calibrate", methods=["POST"])
        def calibrate():
            if not device_manager.is_recording:
                return jsonify({
                    "error": "Start measurement before calibration."
                }), 400

            data = request.get_json() or {}
            reference_db = float(data.get("reference_db", 94.0))
            threshold_db = float(data.get("threshold_db", 50.0))

            result = device_manager.calibrate_microphone(reference_db, threshold_db)
            return jsonify(result)
        
        @self.app.route("/store_recording", methods=["POST"])
        def store_recording():
            data = request.get_json()
            device_manager.should_store_recording = bool(data.get("store", False))
            return jsonify({"store": device_manager.should_store_recording})

        @self.app.route("/num_bands", methods=["POST"])
        def num_bands():
            data = request.get_json()
            num_bands = int(data.get("num_bands", 10))
            device_manager.set_num_bands(num_bands)
            print(f"Number of bands set to {num_bands}")
            return jsonify({"num_bands": num_bands})

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
                        "calibration": {
                        "active": device_manager.is_calibrating,
                        "status": device_manager.calibration_status,
                        "reference_db": device_manager.calibration_reference_db,
                        "threshold_db": device_manager.calibration_threshold_db,
                        "band_spl_db": device_manager.latest_calibration_band_spl_db,
                        "measured_db": device_manager.calibration_measured_db,
                        "offset_db": device_manager.calibration_offset_db,
                    },
                    })
                    yield f"data: {payload}\n\n"
                    time.sleep(0.0167)  # ~60 Hz update rate
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
