"""Unit tests for remove_dc_offset() function (in-place version)."""

import array
import math
import main


class TestRemoveDcOffset:
    """Tests for main.remove_dc_offset(samples, signal, n)."""

    def test_constant_signal_returns_zeros(self):
        """A constant signal should produce all zeros after DC removal."""
        n = 8
        samples = array.array("H", [32768] * n)
        signal = [0.0] * n
        main.remove_dc_offset(samples, signal, n)

        for val in signal:
            assert abs(val) < 1e-9

    def test_result_centered_at_zero(self):
        """The mean of the output should be zero (or very close)."""
        n = 16
        samples = array.array("H", [100, 200, 300, 400] * 4)
        signal = [0.0] * n
        main.remove_dc_offset(samples, signal, n)

        mean_result = sum(signal) / n
        assert abs(mean_result) < 1e-9

    def test_preserves_relative_differences(self):
        """Relative differences between samples should be preserved."""
        n = 4
        samples = [1000, 2000, 3000, 4000]
        signal = [0.0] * n
        main.remove_dc_offset(samples, signal, n)

        for i in range(1, n):
            original_diff = samples[i] - samples[i - 1]
            result_diff = signal[i] - signal[i - 1]
            assert abs(original_diff - result_diff) < 1e-9

    def test_writes_floats_in_place(self):
        """Output should write floats into the signal array."""
        n = 4
        samples = array.array("H", [100, 200, 300, 400])
        signal = [0.0] * n
        main.remove_dc_offset(samples, signal, n)

        for val in signal:
            assert isinstance(val, float)

    def test_sine_wave_centered(self, sine_samples):
        """A sine wave with DC offset should be centered around zero."""
        samples = sine_samples(frequency=110.0, amplitude=5000)
        n = len(samples)
        signal = [0.0] * n
        main.remove_dc_offset(samples, signal, n)

        mean_result = sum(signal) / n
        assert abs(mean_result) < 1e-9

    def test_correct_length(self):
        """Output length should match n."""
        n = 64
        samples = array.array("H", [32768] * n)
        signal = [0.0] * n
        main.remove_dc_offset(samples, signal, n)

        assert len(signal) == n
