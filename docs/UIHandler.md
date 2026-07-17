# UIHandler

## Responsibility
UIHandler provides the Flask web interface for the SPL meter.
It serves the dashboard, receives user commands, and streams live
measurement data to the browser through Server-Sent Events.

## Main routes
- `GET /`: Returns the SPL meter web page.
- `POST /start`: Starts normal audio measurement.
- `POST /stop`: Stops normal audio measurement.
- `POST /calibrate`: Starts microphone calibration. It automatically
  starts audio processing when normal measurement is not active.
- `POST /leq_start`: Starts a fixed-duration Leq measurement.
- `POST /leq_duration`: Selects the Leq duration.
- `POST /store_recording`: Enables or disables WAV recording.
- `POST /num_bands`: Selects the displayed number of filter bands.
- `GET /stream`: Streams live data through SSE.
- `GET /export_json`: Downloads a JSON measurement snapshot.

## Standalone calibration lifecycle
1. The user presses Calibrate Microphone.
2. UIHandler starts recording only when required.
3. AudioDeviceManager waits for a valid 1 kHz signal.
4. AudioDeviceManager calculates the calibration offset.
5. UIHandler stops recording only if it started recording for calibration.