import time
import json
import threading
from flask import Flask
from flask_socketio import SocketIO, emit

HTML_PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SPL Meter</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js" integrity="sha384-2huaBFvYPvCuWLvM02RqGbpjwWn3pYlG1Ti+rkxHQakxD5PR5y4y8M0ZdMprD2yD" crossorigin="anonymous"></script>
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
        .framerate { font-size: 14px; color: #666; margin: 4px 0; }
        .band-count-control { display: flex; align-items: center; gap: 10px; margin: 12px 0; flex-wrap: wrap; }
        .band-count-control select { padding: 6px 12px; font-size: 15px; border-radius: 4px; border: 1px solid #ccc; }
        .band-count-hint { font-size: 13px; color: #888; font-style: italic; }
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
        .filterband-bar-fill { background: #ff4b4b; border-radius: 0 0 4px 4px; width: 100%; transition: height 0.05s linear; will-change: height; }
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
        <strong>Leq Duration:</strong>
        <select id="leq-duration" onchange="setLeqDuration(this.value)">
            <option value="0">5 s</option>
            <option value="1" selected>10 s</option>
            <option value="2">15 s</option>
            <option value="3">30 s</option>
            <option value="4">60 s</option>
            <option value="5">300 s</option>
        </select>
        <button onclick="startLeqMeasurement()">Start Leq</button>
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
    <div class="framerate" id="framerate">Target: 50 FPS | Actual: -- FPS</div>
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
        <div class="band-count-control">
            <label for="band-count"><strong>Filterbänder:</strong></label>
            <select id="band-count" onchange="setBandCount(this.value)">
                <option value="4">4 Bänder</option>
                <option value="6">6 Bänder</option>
                <option value="8">8 Bänder</option>
                <option value="10">10 Bänder</option>
                <option value="12" selected>12 Bänder</option>
            </select>
            <span class="band-count-hint">Mehr Bänder = mehr Rechenaufwand (langsamere Anzeige)</span>
        </div>
        <h3>Filterband SPL Levels (dB)</h3>
        <div class="filterband-grid" id="filterband-grid">
        </div>
"""

HTML_PAGE_TAIL = """
        </div>
    </div>
    <script>
        const socket = io();
        const TARGET_FPS = 60;
        let fpsHistory = [];
        let currentBandCount = 12;

        function updateFramerate() {
            const now = performance.now();
            fpsHistory.push(now);
            const cutoff = now - 1000;
            fpsHistory = fpsHistory.filter(t => t >= cutoff);
            const actualFps = fpsHistory.length;
            document.getElementById('framerate').textContent =
                `Target: ${TARGET_FPS} FPS | Actual: ${actualFps} FPS`;
        }

        function renderBandGrid(frequencies) {
            const grid = document.getElementById('filterband-grid');
            grid.innerHTML = '';
            frequencies.forEach((freq, i) => {
                const box = document.createElement('div');
                box.className = 'filterband-box';
                box.id = 'band-' + i;
                box.innerHTML =
                    '<div class="filterband-value" id="band-' + i + '-value">--</div>' +
                    '<div class="filterband-bar-container">' +
                    '<div class="filterband-bar-fill" id="band-' + i + '-fill" style="height: 0%;"></div>' +
                    '</div>' +
                    '<div class="filterband-freq">' + freq + ' Hz</div>';
                grid.appendChild(box);
            });
        }

        function startMeasurement() {
            socket.emit('start_measurement');
        }

        function stopMeasurement() {
            socket.emit('stop_measurement');
        }

        function setWeighting(value) {
            socket.emit('set_weighting', {weighting: value});
        }

        function setLeqDuration(index) {
            socket.emit('set_leq_duration', {index: Number(index)});
        }

        function startLeqMeasurement() {
            socket.emit('start_leq');
        }

        function calibrateMicrophone() {
            const referenceDb = Number(document.getElementById('reference-db').value);
            socket.emit('calibrate', {reference_db: referenceDb});
        }

        function setStoreAudio(checked) {
            socket.emit('set_store_recording', {store: checked});
        }

        function setBandCount(count) {
            currentBandCount = Number(count);
            socket.emit('set_band_count', {count: currentBandCount});
        }

        socket.on('connect', () => {
            console.log('WebSocket connected');
        });

        socket.on('status', (data) => {
            const s = document.getElementById('status');
            if (data.running) {
                s.textContent = 'Status: Running';
                s.className = 'status running';
                document.getElementById('btn-start').disabled = true;
                document.getElementById('btn-stop').disabled = false;
            } else {
                s.textContent = 'Status: Stopped';
                s.className = 'status stopped';
                document.getElementById('btn-start').disabled = false;
                document.getElementById('btn-stop').disabled = true;
                document.getElementById('framerate').textContent =
                    'Target: ' + TARGET_FPS + ' FPS | Actual: -- FPS';
                fpsHistory = [];
            }
        });

        socket.on('audio_data', (d) => {
            updateFramerate();
            document.getElementById('a-weighted').textContent = d.a_weighted.toFixed(2) + ' dB';
            document.getElementById('spl').textContent  = d.spl_db.toFixed(2) + ' dB';
            document.getElementById('rms').textContent  = d.rms.toFixed(2);
            document.getElementById('peak').textContent = d.peak.toFixed(2);
            document.getElementById('fast').textContent = d.fast.toFixed(2);
            document.getElementById('slow').textContent = d.slow.toFixed(2);
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
        });

        socket.on('band_config', (data) => {
            renderBandGrid(data.frequencies);
        });

        socket.on('calibration_result', (data) => {
            document.getElementById('calibration-status').textContent =
                'Offset: ' + data.offset_db.toFixed(2) + ' dB';
        });

        socket.on('error_message', (data) => {
            console.error('Server error:', data.message);
            alert('Fehler: ' + data.message);
        });
    </script>
</body>
</html>"""


class UIHandler:
    def __init__(self, audio_device_manager=None, host="0.0.0.0", port=8501):
        print("UIHandler: Initializing")

        # Available Leq measurement durations in seconds.
        self.leq_durations_seconds = [5, 10, 15, 30, 60, 300]
        self.leq_duration_index = 0

        self.audio_device_manager = audio_device_manager
        self.recording_thread = None
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading")
        self._register_routes()
        self._register_socket_events()
        self.host = host
        self.port = port
        self.emit_thread_started = False

    def get_leq_duration_seconds(self):
        """Return the currently selected Leq measurement duration in seconds."""
        return self.leq_durations_seconds[self.leq_duration_index]

    def cycle_leq_duration(self):
        self.leq_duration_index += 1
        self.leq_duration_index %= len(self.leq_durations_seconds)
        return self.get_leq_duration_seconds()

    def set_leq_duration_index(self, index):
        if index < 0 or index >= len(self.leq_durations_seconds):
            raise ValueError("Invalid Leq duration index")
        self.leq_duration_index = index
        return self.get_leq_duration_seconds()

    def _get_html_page(self):
        return HTML_PAGE_HEAD + HTML_PAGE_TAIL

    def _register_routes(self):
        @self.app.route("/")
        def index():
            return self._get_html_page()

    def _register_socket_events(self):
        device_manager = self.audio_device_manager

        @self.socketio.on("connect")
        def handle_connect():
            print("Client connected")
            emit("band_config", {"frequencies": device_manager.get_band_frequencies()})
            emit("status", {"running": device_manager.is_recording})

        @self.socketio.on("disconnect")
        def handle_disconnect():
            print("Client disconnected")

        @self.socketio.on("start_measurement")
        def handle_start_measurement():
            self._start_recording_thread()
            if not self.emit_thread_started:
                self.emit_thread_started = True
                self.socketio.start_background_task(self._emit_audio_data_loop)
            emit("status", {"running": True}, broadcast=True)

        @self.socketio.on("stop_measurement")
        def handle_stop_measurement():
            self._stop_recording_thread()
            emit("status", {"running": False}, broadcast=True)

        @self.socketio.on("set_weighting")
        def handle_set_weighting(data):
            weighting = data.get("weighting", "Fast")
            device_manager.time_weighting = weighting
            print(f"Weighting set to {weighting}")

        @self.socketio.on("set_leq_duration")
        def handle_set_leq_duration(data):
            index = int(data.get("index", 0))
            duration_seconds = self.set_leq_duration_index(index)
            print(f"Leq duration set to {duration_seconds} s")

        @self.socketio.on("start_leq")
        def handle_start_leq():
            duration_seconds = self.get_leq_duration_seconds()
            if not device_manager.is_recording:
                self._start_recording_thread()
                if not self.emit_thread_started:
                    self.emit_thread_started = True
                    self.socketio.start_background_task(self._emit_audio_data_loop)
                emit("status", {"running": True}, broadcast=True)

            device_manager.latest_leq_db = None
            device_manager.latest_leq_is_complete = False
            device_manager.audio_processor.start_leq_measurement(
                duration_seconds=duration_seconds,
                sample_rate=device_manager.sample_rate
            )
            print(f"Leq measurement started for {duration_seconds} s")

        @self.socketio.on("calibrate")
        def handle_calibrate(data):
            if not device_manager.is_recording:
                emit("error_message", {"message": "Start measurement before calibration."})
                return
            reference_db = float(data.get("reference_db", 94.0))
            result = device_manager.calibrate_microphone(reference_db)
            emit("calibration_result", result)

        @self.socketio.on("set_store_recording")
        def handle_set_store_recording(data):
            device_manager.should_store_recording = bool(data.get("store", False))
            print(f"Store recording set to {device_manager.should_store_recording}")

        @self.socketio.on("set_band_count")
        def handle_set_band_count(data):
            count = int(data.get("count", 12))
            device_manager.set_band_count(count)
            emit("band_config", {"frequencies": device_manager.get_band_frequencies()}, broadcast=True)

    def _emit_audio_data_loop(self):
        device_manager = self.audio_device_manager
        while True:
            if device_manager.is_recording:
                payload = {
                    "spl_db":        device_manager.latest_spl_db,
                    "rms":           device_manager.latest_rms,
                    "peak":          device_manager.latest_peak,
                    "a_weighted":    device_manager.latest_a_weighted_spl_db,
                    "fast":          device_manager.latest_fast_state,
                    "slow":          device_manager.latest_slow_state,
                    "filterband_spl_db": device_manager.latest_filterband_spl_db,
                    "leq_db":             device_manager.latest_leq_db,
                    "leq_is_complete":    device_manager.latest_leq_is_complete,
                    "leq_is_running":     device_manager.audio_processor.leq_is_running,
                }
                self.socketio.emit("audio_data", payload)
                time.sleep(0.0167)  # ~60 Hz
            else:
                time.sleep(0.1)

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
        print(f"UIHandler: Starting Flask-SocketIO server on http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port)
