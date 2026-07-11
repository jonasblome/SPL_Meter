import os
import sys
import numpy as np
import pytest

# Allow tests to import files from src/
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, SRC_DIR)

from AudioProcessor import AudioProcessor


def test_compute_rms():
    processor = AudioProcessor(sample_rate=48000)

    audio = np.array([1.0, -1.0, 1.0, -1.0])

    assert processor.compute_rms(audio) == pytest.approx(1.0)


def test_compute_peak():
    processor = AudioProcessor(sample_rate=48000)

    audio = np.array([-0.2, 0.5, -0.9, 0.1])

    assert processor.compute_peak(audio) == pytest.approx(0.9)


def test_compute_spl_db_for_reference_pressure():
    processor = AudioProcessor(sample_rate=48000)

    # RMS = 20 µPa should be 0 dB SPL
    audio = np.array([20e-6, -20e-6, 20e-6, -20e-6])

    assert processor.compute_spl_db(audio) == pytest.approx(0.0, abs=1e-6)


def test_compute_spl_db_for_silence():
    processor = AudioProcessor(sample_rate=48000)

    audio = np.zeros(100)

    assert processor.compute_spl_db(audio) == -np.inf


def test_detect_level_db_limits_silence_to_minus_120():
    processor = AudioProcessor(sample_rate=48000)

    audio = np.zeros(100)

    assert processor.detect_level_db(audio) == pytest.approx(-120.0)


def test_start_leq_measurement_sets_state():
    processor = AudioProcessor(sample_rate=1000)

    processor.start_leq_measurement(duration_seconds=1, sample_rate=1000)

    assert processor.leq_is_running is True
    assert processor.leq_target_sample_count == 1000
    assert processor.leq_sample_count == 0


def test_start_leq_measurement_rejects_invalid_duration():
    processor = AudioProcessor(sample_rate=1000)

    with pytest.raises(ValueError):
        processor.start_leq_measurement(duration_seconds=0, sample_rate=1000)


def test_process_leq_measurement_returns_result_after_duration():
    processor = AudioProcessor(sample_rate=1000)

    processor.start_leq_measurement(duration_seconds=1, sample_rate=1000)

    # Constant pressure for 60 dB SPL
    pressure = 20e-6 * 10 ** (60 / 20)
    audio = np.ones(1000) * pressure

    leq_db, is_complete = processor.process_leq_measurement(audio)

    assert is_complete is True
    assert leq_db == pytest.approx(60.0, abs=1e-6)
    assert processor.leq_is_running is False


def test_process_leq_measurement_requires_start():
    processor = AudioProcessor(sample_rate=1000)

    audio = np.ones(100)

    with pytest.raises(RuntimeError):
        processor.process_leq_measurement(audio)


def test_fast_and_slow_states_are_positive_for_signal():
    processor = AudioProcessor(sample_rate=48000)

    audio = np.ones(1024) * 0.1

    fast = processor.compute_fast_state(audio)
    slow = processor.compute_slow_state(audio)

    assert fast > 0
    assert slow > 0


def test_filterbank_creation_returns_filters():
    processor = AudioProcessor(sample_rate=48000)

    filterbank = processor.design_a_weighting_filterbank(
        sample_rate=48000,
        is_octave=True
    )

    assert len(filterbank) > 0