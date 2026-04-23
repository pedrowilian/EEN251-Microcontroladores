"""Tests for identify_note() and cents_deviation()."""
import math
import pytest
import main


class TestIdentifyNote:
    def test_exact_e2(self):
        assert main.identify_note(82.41) == 0

    def test_exact_a2(self):
        assert main.identify_note(110.0) == 1

    def test_exact_d3(self):
        assert main.identify_note(146.83) == 2

    def test_exact_g3(self):
        assert main.identify_note(196.0) == 3

    def test_exact_b3(self):
        assert main.identify_note(246.94) == 4

    def test_exact_e4(self):
        assert main.identify_note(329.63) == 5

    def test_slightly_above_a2(self):
        assert main.identify_note(112.0) == 1

    def test_very_low(self):
        assert main.identify_note(50.0) == 0

    def test_very_high(self):
        assert main.identify_note(500.0) == 5


class TestCentsDeviation:
    def test_unison(self):
        assert main.cents_deviation(110.0, 110.0) == pytest.approx(0.0, abs=0.1)

    def test_octave(self):
        assert main.cents_deviation(220.0, 110.0) == pytest.approx(1200.0, abs=0.1)

    def test_semitone(self):
        assert main.cents_deviation(466.16, 440.0) == pytest.approx(100.0, abs=1.0)

    def test_flat_negative(self):
        assert main.cents_deviation(108.0, 110.0) < 0

    def test_sharp_positive(self):
        assert main.cents_deviation(112.0, 110.0) > 0

    def test_zero_ref(self):
        assert main.cents_deviation(110.0, 0.0) == 0.0

    def test_small_deviation(self):
        # 1 Hz above A2=110 should be about 15.7 cents
        c = main.cents_deviation(111.0, 110.0)
        assert 15.0 < c < 16.0
