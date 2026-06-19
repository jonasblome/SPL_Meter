import numpy as np

class AudioProcessor:
    def __init__(self, sample_rate=48000):
        print("AudioProcessor: Initializing")

        self.sample_rate = sample_rate

        self.fast_state = 0.0
        self.slow_state = 0.0

    def compute_rms(self, audio_data):
        return np.sqrt(np.mean(audio_data**2))
    
    def compute_spl_db(self, audio_data, reference_pressure=20e-6):
        rms = self.compute_rms(audio_data)

        if rms == 0:
            return -np.inf # Return negative infinity if the signal is silent
        
        spl_db = 20 * np.log10(rms / reference_pressure)
        
        return spl_db
    

    #Zeitbewertung in fast and slow
    def compute_time_weighted_factor(self, tau):
        return np.exp(-1.0 / (self.sample_rate * tau))
    
    def update_time_weighting_state(self, sample, old_state, tau):
        a = self.compute_time_weighting_factor(tau)

        current_squared_pressure = sample ** 2

        new_state = a * old_state + (1 - a) * current_squared_pressure

        return new_state
    
    def process_time_weighting_block(self, audio_data, old_state, tau):
        state = old_state

        for sample in audio_data:
            state = self.update_time_weighting_state(sample, state, tau)

        return state
    
    def compute_fast_state(self, audio_data):
        self.fast_state = self.process_time_weighting_block(
            audio_data,
            self.fast_state,
            tau=0.125
        )

        return self.fast_state

    def compute_slow_state(self, audio_data):
        self.slow_state = self.process_time_weighting_block(
            audio_data,
            self.slow_state,
            tau=1.0
        )

        return self.slow_state
