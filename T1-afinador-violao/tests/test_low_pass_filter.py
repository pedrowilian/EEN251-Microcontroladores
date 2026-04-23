"""Tests for low_pass_filter()."""
import math
import main


class TestLowPassFilter:
    def test_iir_recurrence(self):
        a = main.ALPHA
        oma = main.ONE_MINUS_ALPHA
        signal = [10.0, 20.0, 30.0, 40.0]
        filtered = [0.0] * 4
        main.low_pass_filter(signal, filtered, 4)
        y0 = a * 10.0
        y1 = a * 20.0 + oma * y0
        y2 = a * 30.0 + oma * y1
        y3 = a * 40.0 + oma * y2
        assert math.isclose(filtered[0], y0, rel_tol=1e-9)
        assert math.isclose(filtered[3], y3, rel_tol=1e-9)

    def test_all_zeros(self):
        signal = [0.0] * 10
        filtered = [999.0] * 10
        main.low_pass_filter(signal, filtered, 10)
        assert all(v == 0.0 for v in filtered)

    def test_constant_converges(self):
        signal = [5.0] * 200
        filtered = [0.0] * 200
        main.low_pass_filter(signal, filtered, 200)
        assert math.isclose(filtered[-1], 5.0, rel_tol=0.01)

    def test_high_freq_attenuation(self):
        sr = main.SAMPLE_RATE
        n = main.N
        signal = [math.sin(2 * math.pi * 800.0 * i / sr) for i in range(n)]
        filtered = [0.0] * n
        main.low_pass_filter(signal, filtered, n)
        rms_in = math.sqrt(sum(s * s for s in signal[100:]) / (n - 100))
        rms_out = math.sqrt(sum(f * f for f in filtered[100:]) / (n - 100))
        assert rms_out < rms_in * 0.5
