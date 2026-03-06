"""
Peak Volume Manager - Compressor / Limiter Logic
Calculates gain reduction based on audio levels and compressor parameters.
"""

import numpy as np


class Compressor:
    """
    Software dynamics compressor/limiter.
    
    Analyzes audio levels and computes how much the system volume
    should be reduced to keep output within the desired range.
    """

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

        # Parameters (set via update_params)
        self.threshold = -24.0   # dB
        self.ratio = 4.0         # :1
        self.attack = 3.0        # ms
        self.release = 250.0     # ms
        self.knee = 20.0         # dB
        self.ceiling = -3.0      # dB
        self.output_gain = 0.0   # dB

        # Internal state
        self._envelope_db = -60.0  # current smoothed level
        self._gain_reduction_db = 0.0
        self._attack_coeff = 0.0
        self._release_coeff = 0.0
        self._update_coefficients()

    def update_params(self, **kwargs):
        """Update compressor parameters."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._update_coefficients()

    def _update_coefficients(self):
        """Recalculate attack/release smoothing coefficients."""
        # Time constants for exponential smoothing
        # coefficient = 1 - exp(-1 / (time_ms * sample_rate / 1000 / block_size))
        # Using a block-rate update (e.g., ~60 Hz GUI rate or audio callback rate)
        update_rate = 60.0  # approximate updates per second
        if self.attack > 0:
            self._attack_coeff = 1.0 - np.exp(-1.0 / (self.attack * update_rate / 1000.0))
        else:
            self._attack_coeff = 1.0
        if self.release > 0:
            self._release_coeff = 1.0 - np.exp(-1.0 / (self.release * update_rate / 1000.0))
        else:
            self._release_coeff = 1.0

    def _compute_static_curve(self, input_db: float) -> float:
        """
        Compute the compressor's static transfer curve with soft knee.
        Returns the desired output level in dB for a given input level.
        """
        T = self.threshold
        R = self.ratio
        W = self.knee

        if W <= 0:
            # Hard knee
            if input_db <= T:
                return input_db
            else:
                return T + (input_db - T) / R
        else:
            # Soft knee
            half_knee = W / 2.0
            if input_db < (T - half_knee):
                return input_db
            elif input_db > (T + half_knee):
                return T + (input_db - T) / R
            else:
                # Quadratic interpolation in the knee region
                x = input_db - T + half_knee
                return input_db + ((1.0 / R) - 1.0) * (x * x) / (2.0 * W)

    def process(self, audio_block: np.ndarray) -> dict:
        """
        Process an audio block and compute gain reduction.
        
        Args:
            audio_block: numpy array of audio samples (float, -1.0 to 1.0)
            
        Returns:
            dict with:
                - input_rms_db: measured input RMS level
                - input_peak_db: measured input peak level
                - gain_reduction_db: how much to reduce volume (negative value)
                - output_db: estimated output level after reduction
                - target_volume_scalar: multiplier for system volume (0.0 to 1.0+)
        """
        if len(audio_block) == 0:
            return {
                "input_rms_db": -60.0,
                "input_peak_db": -60.0,
                "gain_reduction_db": 0.0,
                "output_db": -60.0,
                "target_volume_scalar": 1.0,
            }

        # Calculate RMS and peak
        rms = np.sqrt(np.mean(audio_block ** 2))
        peak = np.max(np.abs(audio_block))

        # Convert to dB (with floor to avoid log(0))
        input_rms_db = 20.0 * np.log10(max(rms, 1e-10))
        input_peak_db = 20.0 * np.log10(max(peak, 1e-10))

        # Use peak level for detection (catches transients better)
        detect_db = input_peak_db

        # Envelope follower with attack/release
        if detect_db > self._envelope_db:
            # Attack (level rising)
            self._envelope_db += self._attack_coeff * (detect_db - self._envelope_db)
        else:
            # Release (level falling)
            self._envelope_db += self._release_coeff * (detect_db - self._envelope_db)

        # Compute desired output from static curve
        desired_db = self._compute_static_curve(self._envelope_db)

        # Gain reduction = difference between input envelope and desired output
        gain_reduction = desired_db - self._envelope_db  # will be <= 0

        # Apply ceiling (hard limiter)
        if desired_db > self.ceiling:
            ceiling_reduction = self.ceiling - desired_db
            gain_reduction += ceiling_reduction

        # Apply output gain offset
        gain_reduction += self.output_gain

        # Smooth the gain reduction to avoid clicks
        self._gain_reduction_db = gain_reduction

        # Convert to scalar for volume control
        # This is the multiplier to apply to the system volume
        target_scalar = 10.0 ** (gain_reduction / 20.0)
        target_scalar = np.clip(target_scalar, 0.0, 2.0)  # safety clamp

        output_db = self._envelope_db + gain_reduction

        return {
            "input_rms_db": float(input_rms_db),
            "input_peak_db": float(input_peak_db),
            "gain_reduction_db": float(gain_reduction),
            "output_db": float(output_db),
            "target_volume_scalar": float(target_scalar),
        }

    def reset(self):
        """Reset internal state."""
        self._envelope_db = -60.0
        self._gain_reduction_db = 0.0
