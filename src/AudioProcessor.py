import numpy as np
import helpers
from scipy import signal

class AudioProcessor:
    def __init__(self, sample_rate=48000):
        """
        Contains the main signal-processing functions for the SPL meter.

        The class provides basic sound metrics such as RMS, Peak and SPL,
        time-weighted levels such as Fast and Slow, equivalent sound levels
        such as Leq and LAeq, and helper functions for filterbank-based
        A-weighting.
        """
        print("AudioProcessor: Initializing")

        self.sample_rate = sample_rate
        self.fast_state = 0.0
        self.slow_state = 0.0

        # State variables for a fixed-duration Leq measurement.
        # Leq is calculated over a defined measurement time, e.g. 10 seconds.
        # During the measurement, squared pressure samples are accumulated block by block.
        self.leq_sum_square = 0.0
        self.leq_sample_count = 0
        self.leq_target_sample_count = 0

        self.leq_duration_seconds = None
        self.leq_sample_rate = None

        self.leq_is_running = False
        self.leq_result_db = None

        # State variables for a fixed-duration LAeq measurement.
        # LAeq is calculated like Leq, but from an A-weighted audio signal.
        # This means the frequency weighting is applied before the energetic average.
        self.laeq_sum_square = 0.0
        self.laeq_sample_count = 0
        self.laeq_target_sample_count = 0

        self.laeq_duration_seconds = None
        self.laeq_sample_rate = None

        self.laeq_is_running = False
        self.laeq_result_db = None
    
    def compute_peak(self, audio_data):
        return np.max(np.abs(audio_data))

    def reset_leq_measurement(self):
        # Reset all internal values used for Leq measurement.
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

        duration_seconds defines the measurement time selected by the user.
        sample_rate is needed to convert this time into the required number of samples.
        """
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than zero")
        
        if sample_rate <= 0:
            raise ValueError("sample_rate must be greater than zero")

        # Make sure no values from a previous Leq measurement are reused.
        self.reset_leq_measurement()

        self.leq_duration_seconds = duration_seconds
        self.leq_sample_rate = sample_rate

        # Number of samples required to cover the selected measurement time.
        # Example: 10 s * 48000 samples/s = 480000 samples.
        self.leq_target_sample_count = int(duration_seconds * sample_rate)

        self.leq_is_running = True
        self.leq_result_db = None

    def process_leq_measurement(self, audio_data, reference_pressure=20e-6):
        """
        Process one audio block for the running Leq measurement.

        The function returns:
        - (None, False) while the measurement is still running
        - (leq_result_db, True) when the selected measurement duration is complete
        """
        if not self.leq_is_running:
            raise RuntimeError("Leq measurement has not been started.")
        
        # Only process the number of samples that are still needed.
        # This prevents the last block from exceeding the selected measurement time.
        remaining_samples = self.leq_target_sample_count - self.leq_sample_count
        audio_data = audio_data[:remaining_samples]

        # Leq is an energetic average, so pressure values are squared before averaging.
        self.leq_sum_square += np.sum(audio_data**2)
        self.leq_sample_count += len(audio_data)

        # No final Leq value is returned until the selected measurement duration is complete.
        if self.leq_sample_count < self.leq_target_sample_count:
            return None, False

        self.leq_is_running = False

        if self.leq_sample_count == 0 or self.leq_sum_square == 0:
            self.leq_result_db = -np.inf
        else:
            mean_square = self.leq_sum_square / self.leq_sample_count

            # Leq formula:
            # Leq = 10 * log10(mean_square_pressure / reference_pressure^2)
            self.leq_result_db = 10 * np.log10(mean_square / reference_pressure**2)

        return self.leq_result_db, True

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
    def compute_filtered_band_spl_db(self, audio_data, sos):
        """Filter audio with one octave-band filter and return filtered signal + SPL."""
        filtered_signal = signal.sosfilt(sos, audio_data)
        spl_db = self.compute_spl_db(filtered_signal)

        return filtered_signal, float(max(-120.0, spl_db))
    # for 1 kHz octave band SPL

    def mean_square_to_spl_db(self, mean_square, reference_pressure=20e-6):
        """Convert mean square pressure to SPL dB."""
        if mean_square <= 0:
            return -120.0

        return float(10 * np.log10(mean_square / (reference_pressure ** 2)))
        #Zeitbewertung in fast and slow
    def compute_time_weighting_factor(self, tau):
        return np.exp(-1.0 / (self.sample_rate * tau))
    
    def update_time_weighting_state(self, sample, old_state, tau):
        a = self.compute_time_weighting_factor(tau)

        current_squared_pressure = sample ** 2

        new_state = a * old_state + (1 - a) * current_squared_pressure

        return new_state
    
    def process_time_weighting_block(self, audio_data, old_state, tau):
        # Fully vectorized exponential moving average over the block.
        # y[n] = a * y[n-1] + (1-a) * x[n]^2
        # After N samples: y[N-1] = a^N * y[-1] + (1-a) * sum_i a^(N-1-i) * x[i]^2
        a = self.compute_time_weighting_factor(tau)
        audio_squared = audio_data ** 2
        n = len(audio_squared)
        weights = (1.0 - a) * (a ** np.arange(n - 1, -1, -1))
        new_state = (a ** n) * old_state + np.dot(weights, audio_squared)
        return new_state
    
    def compute_time_weighted_db(self, mean_square_pressure, reference_pressure=20e-6):
        """
        Convert a time-weighted mean-square pressure value to dB SPL.

        Fast and Slow weighting smooth squared pressure values first.
        The smoothed value then has to be converted to dB.
        """
        if mean_square_pressure <= 0:
            return -np.inf

        return 10 * np.log10(mean_square_pressure / reference_pressure**2)

    def compute_fast_state(self, audio_data):
        """
        Compute Fast time-weighted SPL in dB.

        The internal fast_state stores the smoothed squared pressure.
        The returned value is converted to dB for UI/export usage.
        """
        self.fast_state = self.process_time_weighting_block(
            audio_data,
            self.fast_state,
            tau=0.125
        )

        return self.compute_time_weighted_db(self.fast_state)
    
    def compute_slow_state(self, audio_data):
        """
        Compute Slow time-weighted SPL in dB.

        The internal slow_state stores the smoothed squared pressure.
        The returned value is converted to dB for UI/export usage.
        """
        self.slow_state = self.process_time_weighting_block(
            audio_data,
            self.slow_state,
            tau=1.0
        )

        return self.compute_time_weighted_db(self.slow_state)

    
    def reset_laeq_measurement(self):
        """Reset all internal values used for LAeq measurement."""
        self.laeq_sum_square = 0.0
        self.laeq_sample_count = 0
        self.laeq_target_sample_count = 0

        self.laeq_duration_seconds = None
        self.laeq_sample_rate = None

        self.laeq_is_running = False
        self.laeq_result_db = None


    def start_laeq_measurement(self, duration_seconds, sample_rate):
        """
        Start a new fixed-duration LAeq measurement.

        LAeq uses the same measurement duration logic as Leq, but it must receive
        an A-weighted audio signal in process_laeq_measurement().
        """
        if duration_seconds <= 0:
            raise ValueError("duration_seconds must be greater than zero")

        if sample_rate <= 0:
            raise ValueError("sample_rate must be greater than zero")

        self.reset_laeq_measurement()

        self.laeq_duration_seconds = duration_seconds
        self.laeq_sample_rate = sample_rate

        # Required number of samples for the selected measurement duration.
        # Example: 5 s * 48000 samples/s = 240000 samples.
        self.laeq_target_sample_count = int(duration_seconds * sample_rate)

        self.laeq_is_running = True
        self.laeq_result_db = None


    def process_laeq_measurement(self, a_weighted_audio_data, reference_pressure=20e-6):
        """
        Process one A-weighted audio block for the running LAeq measurement.

        LAeq is calculated like Leq, but the input signal is A-weighted before
        the energetic average is calculated. The function does not average
        A-weighted dB values directly.

        Returns:
            tuple: (None, False) while running, or (laeq_result_db, True)
            when the selected duration is complete.
        """
        if not self.laeq_is_running:
            raise RuntimeError("LAeq measurement has not been started.")

        # Only process the number of samples that are still needed.
        # This keeps the measurement duration exact even if the last block is longer.
        remaining_samples = self.laeq_target_sample_count - self.laeq_sample_count
        a_weighted_audio_data = a_weighted_audio_data[:remaining_samples]

        # LAeq is an energetic average of the A-weighted signal.
        self.laeq_sum_square += np.sum(a_weighted_audio_data**2)
        self.laeq_sample_count += len(a_weighted_audio_data)

        if self.laeq_sample_count < self.laeq_target_sample_count:
            return None, False

        self.laeq_is_running = False

        if self.laeq_sample_count == 0 or self.laeq_sum_square == 0:
            self.laeq_result_db = -np.inf
        else:
            mean_square = self.laeq_sum_square / self.laeq_sample_count
            self.laeq_result_db = 10 * np.log10(mean_square / reference_pressure**2)

        return self.laeq_result_db, True
    
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
    
    def compute_a_weighted_signal(self, filtered_signals, is_octave=True):
        """
        Build an A-weighted time-domain signal from filtered frequency-band signals.

        LAeq must be calculated from A-weighted signal energy.
        Therefore this function returns the weighted signal itself instead of a dB value.
        """
        if filtered_signals is None or len(filtered_signals) == 0:
            return np.array([], dtype=float)

        frequency_weights = (
            helpers.frequency_weights_octave
            if is_octave
            else helpers.frequency_weights_3rd_octave
        )

        weighted_signal = np.zeros_like(filtered_signals[0], dtype=float)

        for filtered_signal, (_, weight_db) in zip(filtered_signals, frequency_weights.items()):
            weight_linear = 10 ** (weight_db / 20.0)
            weighted_signal += filtered_signal * weight_linear

        return weighted_signal
        
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
