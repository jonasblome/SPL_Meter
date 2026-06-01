import numpy as np

class AudioProcessor:
    def __init__(self):
        print("AudioProcessor: Initializing")

    def compute_rms(self, audio_data):
        return np.sqrt(np.mean(audio_data**2))
    
    def compute_spl_db(self, audio_data, reference_pressure=20e-6):
        rms = self.compute_rms(audio_data)

        if rms == 0:
            return -np.inf  # Return negative infinity if the signal is silent
        
        spl_db = 20 * np.log10(rms / reference_pressure)
        
        return spl_db