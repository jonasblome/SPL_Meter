import json
from datetime import datetime
import helpers


class MeasurementExporter:
    """Creates export files from the latest SPL meter measurement values."""

    def create_measurement_snapshot(self, device_manager, leq_duration_seconds=None):
        """
        Create a dictionary containing the current measurement state.

        This snapshot can be serialized as JSON and downloaded from the web UI.
        """

        return {
            "schema_version": "1.0",
            "exported_at": datetime.now().isoformat(timespec="seconds"),

            "measurement_setup": {
                "sample_rate_hz": getattr(device_manager, "sample_rate", None),
                "chunk_size": getattr(device_manager, "chunk_size", None),
                "leq_duration_seconds": leq_duration_seconds,
                "history_interval_seconds": getattr(
                    device_manager,
                    "measurement_history_interval_seconds",
                    None
                ),
            },

            "results": {
                "spl_db": self._safe_float(getattr(device_manager, "latest_spl_db", None)),
                "rms": self._safe_float(getattr(device_manager, "latest_rms", None)),
                "peak": self._safe_float(getattr(device_manager, "latest_peak", None)),
                "a_weighted_spl_db": self._safe_float(getattr(device_manager, "latest_a_weighted_spl_db", None)),
                "fast_db": self._safe_float(getattr(device_manager, "latest_fast_state", None)),
                "slow_db": self._safe_float(getattr(device_manager, "latest_slow_state", None)),
                "leq_db": self._safe_float(getattr(device_manager, "latest_leq_db", None)),
                "leq_is_complete": bool(getattr(device_manager, "latest_leq_is_complete", False)),
            },

            "filterbands": self._safe_filterbands(
            getattr(device_manager, "latest_filterband_spl_db", [])
            ),
            
            "time_series": list(getattr(device_manager, "measurement_history", [])),
        }

    def to_json_string(self, measurement_data):
        """Convert a measurement dictionary to a formatted JSON string."""
        return json.dumps(measurement_data, indent=4)

    def _safe_float(self, value):
        """Convert NumPy/Python numeric values to normal float values for JSON."""
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _safe_list(self, values):
        """Convert a list of numeric values to JSON-safe floats."""
        if values is None:
            return []

        return [self._safe_float(value) for value in values]
    
    def _safe_filterbands(self, values):
            """Return filterband center frequencies and SPL values in a compact table-like structure."""
            if values is None:
                values = []

            frequencies = list(helpers.frequency_weights_octave.keys())

            return {
                "center_frequency_hz": [
                    float(frequency)
                    for frequency, _ in zip(frequencies, values)
                ],
                "spl_db": [
                    self._round_float(value)
                    for value in values[:len(frequencies)]
                ]
            }
    
    def _round_float(self, value, decimals=2):
        """Convert numeric values to rounded Python floats for readable JSON export."""
        safe_value = self._safe_float(value)

        if safe_value is None:
            return None

        return round(safe_value, decimals)