"""Unit tests for capture_samples() function."""

import array
import math
import main
from tests.conftest import MockADC


class TestCaptureSamples:
    """Tests for main.capture_samples()."""

    def test_silent_signal_returns_false(self):
        """Constant ADC values (no signal) should return False."""
        adc = MockADC()
        adc.set_values([32768] * 64)
        samples = array.array("H", [0] * 64)

        result = main.capture_samples(adc, samples, main.SAMPLE_RATE, 64)

        assert result is False

    def test_loud_signal_returns_true(self):
        """Signal with amplitude >= SIGNAL_THRESHOLD should return True."""
        n = 64
        adc = MockADC()
        # Create values with peak-to-peak = 600 (> 500 threshold)
        values = [32768 - 300 if i % 2 == 0 else 32768 + 300 for i in range(n)]
        adc.set_values(values)
        samples = array.array("H", [0] * n)

        result = main.capture_samples(adc, samples, main.SAMPLE_RATE, n)

        assert result is True

    def test_exactly_at_threshold_returns_true(self):
        """Signal with amplitude exactly equal to SIGNAL_THRESHOLD returns True."""
        n = 64
        adc = MockADC()
        mid = 32768
        half = main.SIGNAL_THRESHOLD // 2  # 250
        values = [mid - half] * (n // 2) + [mid + half] * (n // 2)
        adc.set_values(values)
        samples = array.array("H", [0] * n)

        result = main.capture_samples(adc, samples, main.SAMPLE_RATE, n)

        assert result is True

    def test_just_below_threshold_returns_false(self):
        """Signal with amplitude just below SIGNAL_THRESHOLD returns False."""
        n = 64
        adc = MockADC()
        mid = 32768
        # peak-to-peak = 499 < 500
        values = [mid] * (n // 2) + [mid + 499] * (n // 2)
        adc.set_values(values)
        samples = array.array("H", [0] * n)

        result = main.capture_samples(adc, samples, main.SAMPLE_RATE, n)

        assert result is False

    def test_samples_array_is_filled(self):
        """capture_samples should fill the samples array with ADC readings."""
        n = 8
        adc = MockADC()
        expected = [100, 200, 300, 400, 500, 600, 700, 800]
        adc.set_values(expected)
        samples = array.array("H", [0] * n)

        main.capture_samples(adc, samples, main.SAMPLE_RATE, n)

        for i in range(n):
            assert samples[i] == expected[i]

    def test_sine_wave_above_threshold(self, sine_samples):
        """A sine wave with sufficient amplitude should return True."""
        n = 128
        adc = MockADC()
        # Generate sine wave with amplitude 5000 (peak-to-peak ~10000 >> 500)
        mid = 32768
        sr = main.SAMPLE_RATE
        freq = 110.0
        amplitude = 5000
        values = [
            max(0, min(65535, int(mid + amplitude * math.sin(2 * math.pi * freq * i / sr))))
            for i in range(n)
        ]
        adc.set_values(values)
        samples = array.array("H", [0] * n)

        result = main.capture_samples(adc, samples, sr, n)

        assert result is True
