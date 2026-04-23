"""Tests for fft() — Cooley-Tukey radix-2 DIT."""
import math
import pytest
from main import fft, precompute_twiddles, precompute_bit_reverse_table


def _make_sine(freq, n, sample_rate):
    return [math.sin(2 * math.pi * freq * i / sample_rate) for i in range(n)]


class TestFFTZeros:
    def test_all_zeros(self):
        n = 64
        re = [0.0] * n
        im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_bit_reverse_table(n)
        fft(re, im, tw_re, tw_im, br, n)
        for k in range(n):
            assert re[k] == pytest.approx(0.0, abs=1e-12)
            assert im[k] == pytest.approx(0.0, abs=1e-12)


class TestFFTDCSignal:
    def test_dc_signal(self):
        n = 128
        dc = 3.5
        re = [dc] * n
        im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_bit_reverse_table(n)
        fft(re, im, tw_re, tw_im, br, n)
        assert re[0] == pytest.approx(n * dc, rel=1e-9)
        for k in range(1, n):
            assert re[k] == pytest.approx(0.0, abs=1e-9)


class TestFFTPureSine:
    def test_sine_peak_at_correct_bin(self):
        n = 256
        sr = 1024
        freq = 128.0
        expected_bin = int(freq * n / sr)
        re = _make_sine(freq, n, sr)
        im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_bit_reverse_table(n)
        fft(re, im, tw_re, tw_im, br, n)
        magnitudes = [math.sqrt(re[k]**2 + im[k]**2) for k in range(n // 2)]
        peak_bin = max(range(len(magnitudes)), key=lambda k: magnitudes[k])
        assert peak_bin == expected_bin


class TestFFTParsevalTheorem:
    def test_parseval_sine(self):
        n = 256
        sr = 1024
        freq = 100.0
        re = _make_sine(freq, n, sr)
        im = [0.0] * n
        time_energy = sum(x**2 for x in re)
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_bit_reverse_table(n)
        fft(re, im, tw_re, tw_im, br, n)
        freq_energy = sum(re[k]**2 + im[k]**2 for k in range(n))
        assert freq_energy == pytest.approx(n * time_energy, rel=1e-6)

    def test_parseval_dc(self):
        n = 64
        dc = 2.0
        re = [dc] * n
        im = [0.0] * n
        time_energy = sum(x**2 for x in re)
        tw_re, tw_im = precompute_twiddles(n)
        br = precompute_bit_reverse_table(n)
        fft(re, im, tw_re, tw_im, br, n)
        freq_energy = sum(re[k]**2 + im[k]**2 for k in range(n))
        assert freq_energy == pytest.approx(n * time_energy, rel=1e-6)
