"""Tests for the full DSP pipeline via process()."""
import math
import array
import pytest
from main import (process, precompute_twiddles, precompute_br,
                   SAMPLE_RATE, N, BIN_MIN, BIN_MAX, TWO_PI)


def _make_pipeline_arrays(n):
    signal = [0.0] * n
    filtered = [0.0] * n
    re = [0.0] * n
    im = [0.0] * n
    mag = [0.0] * (n >> 1)
    tw_re, tw_im = precompute_twiddles(n)
    br = precompute_br(n)
    han = [0.5 * (1.0 - math.cos(TWO_PI * i / (n - 1))) for i in range(n)]
    return signal, filtered, re, im, mag, tw_re, tw_im, br, han


class TestFullPipeline:
    def _run(self, freq_hz):
        n = N
        sr = SAMPLE_RATE
        mid = 32768
        amp = 10000.0
        samples = array.array("H", [
            max(0, min(65535, int(mid + amp * math.sin(TWO_PI * freq_hz * i / sr))))
            for i in range(n)
        ])
        signal, filtered, re, im, mag, tw_re, tw_im, br, han = _make_pipeline_arrays(n)
        return process(samples, signal, filtered, han, re, im, mag, tw_re, tw_im, br, n)

    def test_a2(self):
        assert abs(self._run(110.0) - 110.0) <= 5.0

    def test_e2(self):
        assert abs(self._run(82.41) - 82.41) <= 5.0

    def test_d3(self):
        assert abs(self._run(146.83) - 146.83) <= 5.0

    def test_g3(self):
        assert abs(self._run(196.0) - 196.0) <= 5.0

    def test_e4(self):
        assert abs(self._run(329.63) - 329.63) <= 5.0

    def test_430hz(self):
        """Testa 430 Hz (frequencia que o usuario esta testando do YouTube)."""
        detected = self._run(430.0)
        assert abs(detected - 430.0) <= 5.0
