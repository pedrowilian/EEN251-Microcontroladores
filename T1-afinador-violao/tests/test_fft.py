"""Tests for fft()."""
import math
import pytest
from main import fft, precompute_twiddles, precompute_br


class TestFFT:
    def test_all_zeros(self):
        n = 64
        re = [0.0] * n
        im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_br(n)
        fft(re, im, tw_re, tw_im, br, n)
        for k in range(n):
            assert re[k] == pytest.approx(0.0, abs=1e-12)

    def test_dc_signal(self):
        n = 128
        dc = 3.5
        re = [dc] * n
        im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_br(n)
        fft(re, im, tw_re, tw_im, br, n)
        assert re[0] == pytest.approx(n * dc, rel=1e-9)

    def test_sine_peak(self):
        n = 256
        sr = 1024
        freq = 128.0
        expected_bin = int(freq * n / sr)
        re = [math.sin(2 * math.pi * freq * i / sr) for i in range(n)]
        im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_br(n)
        fft(re, im, tw_re, tw_im, br, n)
        mags = [math.sqrt(re[k]**2 + im[k]**2) for k in range(n // 2)]
        peak = max(range(len(mags)), key=lambda k: mags[k])
        assert peak == expected_bin

    def test_parseval(self):
        n = 256
        sr = 1024
        re = [math.sin(2 * math.pi * 100.0 * i / sr) for i in range(n)]
        im = [0.0] * n
        te = sum(x**2 for x in re)
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_br(n)
        fft(re, im, tw_re, tw_im, br, n)
        fe = sum(re[k]**2 + im[k]**2 for k in range(n))
        assert fe == pytest.approx(n * te, rel=1e-6)
