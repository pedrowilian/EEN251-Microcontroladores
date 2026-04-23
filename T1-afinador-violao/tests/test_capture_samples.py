"""Tests for capture_samples() and check_signal()."""
import array
import math
import main
from tests.conftest import MockADC


class TestCaptureSamples:
    def test_fills_array(self):
        adc = MockADC()
        adc.set_values([100, 200, 300, 400])
        samples = array.array("H", [0] * 4)
        main.capture_samples(adc, samples, 4)
        assert list(samples) == [100, 200, 300, 400]


class TestCheckSignal:
    def test_silent_below_threshold(self):
        n = 64
        samples = array.array("H", [32768] * n)
        pp = main.check_signal(samples, n, 500)
        assert pp == 0

    def test_loud_above_threshold(self):
        n = 64
        samples = array.array("H", [32000] * 32 + [33000] * 32)
        pp = main.check_signal(samples, n, 500)
        assert pp == 1000

    def test_returns_peak_to_peak(self):
        samples = array.array("H", [100, 600, 300, 200])
        pp = main.check_signal(samples, 4, 0)
        assert pp == 500
