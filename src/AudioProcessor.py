import numpy as np
import helpers
from scipy import signal

class AudioProcessor:
    def __init__(self, sample_rate=48000):
        print("AudioProcessor: Initializing")

        self.sample_rate = sample_rate
        self.fast_state = 0.0
        self.slow_state = 0.0

        # State variables for fixed-duration Leq measurement.
        # Leq is calculated over a selected measurement duration.
        self.leq_sum_square = 0.0
        self.leq_sample_count = 0
        self.leq_target_sample_count = 0

        self.leq_duration_seconds = None
        self.leq_sample_rate = None

        self.leq_is_running = False
        self.leq_result_db = None
    
    def compute_peak(self, audio_data):
        return np.max(np.abs(audio_data))

    def compute_rms(self, audio_data):
        return np.sqrt(np.mean(audio_data**2))
    
    def compute_spl_db(self, audio_data, reference_pressure=20e-6):
        rms = self.compute_rms(audio_data)

        if rms == 0:
            return -np.inf # Return negative infinity if the signal is silent
        
        spl_db = 20 * np.log10(rms / reference_pressure)
        
        return spl_db
    #Calibrate
    def detect_level_db(self, audio_data):
        """Automatically detect the current microphone level in dB."""
        level_db = self.compute_spl_db(audio_data)

        # mute cant return-inf，UI 
        return float(max(-120.0, level_db))
    
    #Zeitbewertung in fast and slow
    def compute_time_weighting_factor(self, tau):
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
    

    def reset_leq_measurement(self):
        """Reset all internal values used for Leq measurement."""
        self.leq_sum_square = 0.0
        self.leq_sample_count = 0
        self.leq_target_sample_count = 0

        self.leq_duration_seconds = None
        self.leq_sample_rate = None

        self.leq_is_running = False
        self.leq_result_db = None

    def start_leq_measurement(self, duration_seconds, sample_rate):
        """
        Start a new fixed-duration Leq measurement.
        """
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than zero")

        if sample_rate <= 0:
            raise ValueError("sample_rate must be greater than zero")

        self.reset_leq_measurement()

        self.leq_duration_seconds = duration_seconds
        self.leq_sample_rate = sample_rate
        self.leq_target_sample_count = int(duration_seconds * sample_rate)

        self.leq_is_running = True
        self.leq_result_db = None

    
    def process_leq_measurement(self, audio_data, reference_pressure=20e-6):
        """
        Process one audio block for the running Leq measurement.
        """
        if not self.leq_is_running:
            raise RuntimeError("Leq measurement has not been started.")

        remaining_samples = self.leq_target_sample_count - self.leq_sample_count
        audio_data = audio_data[:remaining_samples]

        self.leq_sum_square += np.sum(audio_data**2)
        self.leq_sample_count += len(audio_data)

        if self.leq_sample_count < self.leq_target_sample_count:
            return None, False

        self.leq_is_running = False

        if self.leq_sample_count == 0 or self.leq_sum_square == 0:
            self.leq_result_db = -np.inf
        else:
            mean_square = self.leq_sum_square / self.leq_sample_count
            self.leq_result_db = 10 * np.log10(mean_square / reference_pressure**2)

        return self.leq_result_db, True
    
    def design_a_weighting_filterbank(self, sample_rate, is_octave=True):
        octave_ratio = 10**(3/10) if is_octave else 10**(1/10)
        frequency_weights = helpers.frequency_weights_octave if is_octave else helpers.frequency_weights_3rd_octave
        band_lower_freqs = np.array(list(frequency_weights.keys())) * octave_ratio**(-1/2)
        band_upper_freqs = np.array(list(frequency_weights.keys())) * octave_ratio**(1/2)

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
        
    def compute_a_weighting(self, filtered_signals, is_octave=True):
        frequency_weights = helpers.frequency_weights_octave if is_octave else helpers.frequency_weights_3rd_octave

        weighted_signal = np.zeros_like(filtered_signals[0])
        for i, filtered_signal in enumerate(filtered_signals):
            band_center_freq = list(frequency_weights.keys())[i]
            weight_db = frequency_weights[band_center_freq]
            weight_linear = 10 ** (weight_db / 20)
            weighted_signal += filtered_signal * weight_linear
        
        spl_db = self.compute_spl_db(weighted_signal)

        return spl_db
