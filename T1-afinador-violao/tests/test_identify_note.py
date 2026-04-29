"""Tests for identify() and cents()."""
import pytest
import main


class TestIdentify:
    def test_e2(self):  assert main.identify(82.41) == 0
    def test_a2(self):  assert main.identify(110.0) == 1
    def test_d3(self):  assert main.identify(146.83) == 2
    def test_g3(self):  assert main.identify(196.0) == 3
    def test_b3(self):  assert main.identify(246.94) == 4
    def test_e4(self):  assert main.identify(329.63) == 5
    def test_above_a2(self): assert main.identify(112.0) == 1
    def test_low(self):  assert main.identify(50.0) == 0
    def test_high(self): assert main.identify(500.0) == 5


class TestCents:
    def test_unison(self):
        assert main.cents(110.0, 110.0) == pytest.approx(0.0, abs=0.1)

    def test_octave(self):
        assert main.cents(220.0, 110.0) == pytest.approx(1200.0, abs=0.1)

    def test_flat(self):
        assert main.cents(108.0, 110.0) < 0

    def test_sharp(self):
        assert main.cents(112.0, 110.0) > 0

    def test_zero_ref(self):
        assert main.cents(110.0, 0.0) == 0.0
