"""Unit tests for the low_pass_filter function."""

import math
import main


class TestLowPassFilter:
    """Tests for low_pass_filter(samples, filtered, alpha, n)."""

    def test_single_sample(self):
        """First element should be alpha * samples[0]."""
        samples = [1.0]
        filtered = [0.0]
        main.low_pass_filter(samples, filtered, 0.5, 1)
        assert filtered[0] == 0.5

    def test_iir_recurrence(self):
        """Verify the IIR recurrence y[i] = α·x[i] + (1-α)·y[i-1]."""
        alpha = 0.386
        samples = [10.0, 20.0, 30.0, 40.0]
        filtered = [0.0] * 4
        main.low_pass_filter(samples, filtered, alpha, 4)

        # Manual calculation
        y0 = alpha * 10.0
        y1 = alpha * 20.0 + (1 - alpha) * y0
        y2 = alpha * 30.0 + (1 - alpha) * y1
        y3 = alpha * 40.0 + (1 - alpha) * y2

        assert math.isclose(filtered[0], y0, rel_tol=1e-9)
        assert math.isclose(filtered[1], y1, rel_tol=1e-9)
        assert math.isclose(filtered[2], y2, rel_tol=1e-9)
        assert math.isclose(filtered[3], y3, rel_tol=1e-9)

    def test_all_zeros(self):
        """All-zero input should produce all-zero output."""
        samples = [0.0] * 10
        filtered = [999.0] * 10  # pre-filled with junk
        main.low_pass_filter(samples, filtered, 0.386, 10)
        assert all(v == 0.0 for v in filtered)

    def test_constant_signal_converges(self):
        """A constant input should converge to that constant value."""
        n = 200
        constant = 5.0
        samples = [constant] * n
        filtered = [0.0] * n
        main.low_pass_filter(samples, filtered, 0.386, n)
        # After many samples, filtered should be very close to the constant
        assert math.isclose(filtered[-1], constant, rel_tol=0.01)

    def test_operates_in_place(self):
        """Filter must write into the provided filtered array, not create a new one."""
        samples = [1.0, 2.0, 3.0]
        filtered = [0.0, 0.0, 0.0]
        original_id = id(filtered)
        result = main.low_pass_filter(samples, filtered, 0.5, 3)
        assert result is None  # function returns nothing
        assert id(filtered) == original_id
        assert filtered[0] != 0.0  # was modified in-place

    def test_high_freq_attenuation(self):
        """A high-frequency sine (above cutoff) should be attenuated."""
        sr = main.SAMPLE_RATE
        n = main.N
        freq = 800.0  # well above 400 Hz cutoff
        samples_dc = [math.sin(2 * math.pi * freq * i / sr) for i in range(n)]
        filtered = [0.0] * n
        main.low_pass_filter(samples_dc, filtered, main.ALPHA, n)

        # Compare RMS of input vs output (skip transient first 100 samples)
        rms_in = math.sqrt(sum(s * s for s in samples_dc[100:]) / (n - 100))
        rms_out = math.sqrt(sum(f * f for f in filtered[100:]) / (n - 100))
        assert rms_out < rms_in * 0.5  # at least 50% attenuation
