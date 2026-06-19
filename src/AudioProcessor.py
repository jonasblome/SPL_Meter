import numpy as np
from scipy import signal

class AudioProcessor:
    # According to IEC61672:2014
    frequency_weights_3rd_octave = {
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

    frequency_weights_octave = {
        8: -77.8,
        16: -56.7,
        31.5: -39.4,
        63: -26.2,
        125: -16.1,
        250: -8.6,
        500: -3.2,
        1000: 0.0,
        2000: 1.2,
        4000: 1.0,
        8000: -1.1,
        16000: -6.6
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
    
    def design_a_weighting_filterbank(self, sample_rate):
        octave_ratio = 10**(3/10) # 3 dB pro Oktave entspricht einem Faktor von 10^(3/10)
        band_lower_freqs = np.array(list(self.frequency_weights_octave.keys())) * octave_ratio**(-1/2)
        band_upper_freqs = np.array(list(self.frequency_weights_octave.keys())) * octave_ratio**(1/2)

        # nyquist_freq = sample_rate / 2 - 1
        # band_upper_freqs = np.minimum(band_upper_freqs, nyquist_freq)
        for lower_freq, upper_freq in zip(band_lower_freqs, band_upper_freqs):
            if upper_freq >= sample_rate / 2:
                raise ValueError(f"Sample rate {sample_rate} Hz is too low for the designed A-weighting filterbank. Please use a higher sample rate.")

        a_weighting_filterbank = []
        for lower_freq, upper_freq in zip(band_lower_freqs, band_upper_freqs):
            sos_sections = signal.butter(
                10,
                [lower_freq, upper_freq],
                btype='bandpass',
                fs=sample_rate,
                output='sos'
            )
            a_weighting_filterbank.append(sos_sections)
        
        return a_weighting_filterbank
    
    def apply_filterbank(self, audio_data, filterbank):
        filtered_signals = []
        for sos in filterbank:
            filtered_signal = signal.sosfilt(sos, audio_data)
            filtered_signals.append(filtered_signal)
        
        return filtered_signals
        
    def compute_a_weighting(self, filtered_signals):
        weighted_signal = np.zeros_like(filtered_signals[0])
        for i, filtered_signal in enumerate(filtered_signals):
            band_center_freq = list(self.frequency_weights_octave.keys())[i]
            weight_db = self.frequency_weights_octave[band_center_freq]
            weight_linear = 10 ** (weight_db / 20)
            weighted_signal += filtered_signal * weight_linear
        
        spl_db = self.compute_spl_db(weighted_signal)

        return spl_db
