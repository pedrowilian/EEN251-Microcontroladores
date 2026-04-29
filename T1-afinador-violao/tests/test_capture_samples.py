"""Tests for capture() and get_pp()."""
import array
import main
from tests.conftest import MockADC


class TestCapture:
    def test_fills_array(self):
        adc = MockADC()
        adc.set_values([100, 200, 300, 400])
        samples = array.array("H", [0] * 4)
        main.capture(adc, samples, 4)
        assert list(samples) == [100, 200, 300, 400]


class TestGetPP:
    def test_silent(self):
        samples = array.array("H", [32768] * 64)
        mn, mx, pp = main.get_pp(samples, 64)
        assert pp == 0

    def test_loud(self):
        samples = array.array("H", [32000] * 32 + [33500] * 32)
        mn, mx, pp = main.get_pp(samples, 64)
        assert pp == 1500

    def test_values(self):
        samples = array.array("H", [100, 600, 300])
        mn, mx, pp = main.get_pp(samples, 3)
        assert mn == 100
        assert mx == 600
        assert pp == 500
