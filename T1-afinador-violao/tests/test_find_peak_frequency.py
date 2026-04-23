"""Tests for find_peak_frequency()."""
import math
import pytest
from main import (
    find_peak_frequency, compute_magnitudes, fft,
    precompute_twiddles, precompute_bit_reverse_table,
    remove_dc_offset, low_pass_filter, apply_hanning,
    SAMPLE_RATE, N, BIN_MIN, BIN_MAX, FREQ_RES, ALPHA,
)


class TestPeakDetection:
    def test_symmetric_no_shift(self):
        mag = [0.0] * (N >> 1)
        mag[50] = 10.0
        mag[49] = 5.0
        mag[51] = 5.0
        freq = find_peak_frequency(mag, BIN_MIN, BIN_MAX)
        assert freq == pytest.approx(50 * FREQ_RES, abs=0.1)

    def test_shifts_up(self):
        mag = [0.0] * (N >> 1)
        mag[50] = 10.0
        mag[49] = 3.0
        mag[51] = 7.0
        assert find_peak_frequency(mag, BIN_MIN, BIN_MAX) > 50 * FREQ_RES

    def test_shifts_down(self):
        mag = [0.0] * (N >> 1)
        mag[50] = 10.0
        mag[49] = 7.0
        mag[51] = 3.0
        assert find_peak_frequency(mag, BIN_MIN, BIN_MAX) < 50 * FREQ_RES

    def test_all_zeros(self):
        mag = [0.0] * (N >> 1)
        assert find_peak_frequency(mag, BIN_MIN, BIN_MAX) == 0.0

    def test_peak_at_bin_min(self):
        mag = [0.0] * (N >> 1)
        mag[BIN_MIN] = 15.0
        freq = find_peak_frequency(mag, BIN_MIN, BIN_MAX)
        assert freq == pytest.approx(BIN_MIN * FREQ_RES, abs=0.1)


class TestFullPipeline:
    def _run(self, freq_hz):
        import array as arr
        mid = 32768
        amp = 10000.0
        n = N
        sr = SAMPLE_RATE
        samples = arr.array("H", [
            max(0, min(65535, int(mid + amp * math.sin(6.283185307179586 * freq_hz * i / sr))))
            for i in range(n)
        ])
        signal = [0.0] * n
        remove_dc_offset(samples, signal, n)
        filtered = [0.0] * n
        low_pass_filter(signal, filtered, n)
        han = [0.5 * (1.0 - math.cos(6.283185307179586 * i / (n - 1))) for i in range(n)]
        apply_hanning(filtered, han, n)
        re = list(filtered)
        im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_bit_reverse_table(n)
        fft(re, im, tw_re, tw_im, br, n)
        mag = [0.0] * (n >> 1)
        compute_magnitudes(re, im, mag, n)
        return find_peak_frequency(mag, BIN_MIN, BIN_MAX)

    def test_e2(self):
        assert abs(self._run(82.41) - 82.41) <= 4.0

    def test_a2(self):
        assert abs(self._run(110.0) - 110.0) <= 4.0

    def test_d3(self):
        assert abs(self._run(146.83) - 146.83) <= 4.0

    def test_g3(self):
        assert abs(self._run(196.0) - 196.0) <= 4.0

    def test_b3(self):
        assert abs(self._run(246.94) - 246.94) <= 4.0

    def test_e4(self):
        assert abs(self._run(329.63) - 329.63) <= 4.0
