import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np

import AudioProcessor
import UIHandler


def process_audio_in_blocks(processor, audio_data, block_size=1024):
    is_complete = False
    leq_db = None

    for start_index in range(0, len(audio_data), block_size):
        audio_block = audio_data[start_index:start_index + block_size]

        leq_db, is_complete = processor.process_leq_measurement(audio_block)

        if is_complete:
            break

    return leq_db, is_complete


def test_leq_duration_index_returns_10_seconds():
    ui_handler = UIHandler.UIHandler()

    duration_seconds = ui_handler.set_leq_duration_index(1)

    assert duration_seconds == 10


def test_leq_measurement_10_seconds_reference_pressure():
    processor = AudioProcessor.AudioProcessor()
    ui_handler = UIHandler.UIHandler()

    reference_pressure = 20e-6
    sample_rate = 1000

    duration_seconds = ui_handler.set_leq_duration_index(1)

    processor.start_leq_measurement(
        duration_seconds=duration_seconds,
        sample_rate=sample_rate
    )

    audio_data = np.ones(duration_seconds * sample_rate) * reference_pressure

    leq_db, is_complete = process_audio_in_blocks(processor, audio_data)

    print(f"Leq duration: {duration_seconds} s")
    print(f"Computed Leq: {leq_db:.2f} dB")
    print(f"Samples processed: {processor.leq_sample_count}")

    assert is_complete is True
    assert processor.leq_sample_count == duration_seconds * sample_rate
    assert processor.leq_is_running is False
    assert np.isclose(leq_db, 0.0, atol=1e-9)
