import numpy as np
import wave

with wave.open(r"C:\Users\Lars\Downloads\test.wav", "rb") as wf:
    frames = wf.readframes(wf.getnframes())
    arr = np.frombuffer(frames, dtype=np.int32)
    print(f"Samples: {len(arr)}, Min: {arr.min()}, Max: {arr.max()}, Nonzero: {np.count_nonzero(arr)}")
    print("First 16:", arr[:16])
    print("First 16 hex:", [hex(v & 0xFFFFFFFF) for v in arr[:16]])