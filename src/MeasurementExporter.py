import json
from datetime import datetime


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
                "time_weighting": getattr(device_manager, "time_weighting", None),
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
                "a_weighted_spl_db": self._safe_float(
                    getattr(device_manager, "latest_a_weighted_spl_db", None)
                ),
                "fast_db": self._safe_float(getattr(device_manager, "latest_fast_state", None)),
                "slow_db": self._safe_float(getattr(device_manager, "latest_slow_state", None)),
                "time_weighted_db": self._safe_float(
                    getattr(device_manager, "latest_time_weighted_value", None)
                ),
                "leq_db": self._safe_float(getattr(device_manager, "latest_leq_db", None)),
                "leq_is_complete": bool(getattr(device_manager, "latest_leq_is_complete", False)),
            },

            "filterband_spl_db": self._safe_list(
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