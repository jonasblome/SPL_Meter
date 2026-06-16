import numpy as np

class AudioProcessor:
    # According to IEC61672:2014
    frequency_weights = {
        6.3: -85.4,
        8: -77.8,
        10: -70.4,
        12.5: -63.4,
        16: -56.7,
        20: -50.5,
        25: -44.7,
        31.5: -39.4,
        40: -34.6,
        50: -30.2,
        63: -26.2,
        80: -22.5,
        100: -19.1,
        125: -16.1,
        160: -13.4,
        200: -10.9,
        250: -8.6,
        315: -6.6,
        400: -4.8,
        500: -3.2,
        630: -1.9,
        800: -0.8,
        1000: 0.0,
        1250: 0.6,
        1600: 1.0,
        2000: 1.2,
        2500: 1.3,
        3150: 1.2,
        4000: 1.0,
        5000: 0.5,
        6300: -0.1,
        8000: -1.1,
        10000: -2.5,
        12500: -4.3,
        16000: -6.6,
        20000: -9.3
    }

    def __init__(self):
        print("AudioProcessor: Initializing")

    def compute_rms(self, audio_data):
        return np.sqrt(np.mean(audio_data**2))
    
    def compute_spl_db(self, audio_data, reference_pressure=20e-6):
        rms = self.compute_rms(audio_data)

        if rms == 0:
            return -np.inf # Return negative infinity if the signal is silent
        
        spl_db = 20 * np.log10(rms / reference_pressure)
        
        return spl_db
    
    def design_a_weighting(self, sample_rate):
        filter_coefficients = np.array([10**(gain / 20) for gain in self.frequency_weights.values()])
        
        return filter_coefficients
        
    def apply_a_weighting(self, audio_data, sample_rate):
        filter_coeffs = self.design_a_weighting(sample_rate)

        return np.convolve(audio_data, filter_coeffs, mode='same')
