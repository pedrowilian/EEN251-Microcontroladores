"""Unit tests for precompute_twiddles(n).

Validates: Requirement 4.2 — FFT implemented in pure MicroPython,
twiddle factors pre-computed for efficiency.
"""

import math
import pytest
import main


class TestPrecomputeTwiddles:
    """Tests for the precompute_twiddles function."""

    def test_returns_two_lists(self):
        """precompute_twiddles returns a tuple of two lists."""
        result = main.precompute_twiddles(8)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], list)

    def test_length_is_half_n(self):
        """Each returned list has length N/2."""
        for n in [8, 16, 64, 256, 1024, 2048]:
            tw_re, tw_im = main.precompute_twiddles(n)
            assert len(tw_re) == n // 2
            assert len(tw_im) == n // 2

    def test_values_for_n8(self):
        """Verify exact twiddle factor values for N=8 (small, easy to check)."""
        tw_re, tw_im = main.precompute_twiddles(8)
        # k=0..3, angle = 2*pi*k/8 = pi*k/4
        for k in range(4):
            angle = 2.0 * math.pi * k / 8
            assert tw_re[k] == pytest.approx(math.cos(angle), abs=1e-12)
            assert tw_im[k] == pytest.approx(math.sin(angle), abs=1e-12)

    def test_first_element_is_1_0(self):
        """k=0 → cos(0)=1, sin(0)=0 for any N."""
        for n in [8, 64, 2048]:
            tw_re, tw_im = main.precompute_twiddles(n)
            assert tw_re[0] == pytest.approx(1.0, abs=1e-12)
            assert tw_im[0] == pytest.approx(0.0, abs=1e-12)

    def test_quarter_point(self):
        """k=N/4 → cos(π/2)=0, sin(π/2)=1 for even N."""
        for n in [8, 16, 64, 256, 2048]:
            tw_re, tw_im = main.precompute_twiddles(n)
            quarter = n // 4
            assert tw_re[quarter] == pytest.approx(0.0, abs=1e-9)
            assert tw_im[quarter] == pytest.approx(1.0, abs=1e-9)

    def test_system_n(self):
        """Verify twiddle factors for the actual system N=2048."""
        tw_re, tw_im = main.precompute_twiddles(main.N)
        half = main.N // 2
        assert len(tw_re) == half
        assert len(tw_im) == half
        # Spot-check a few values
        for k in [0, 1, half // 4, half // 2, half - 1]:
            angle = 2.0 * math.pi * k / main.N
            assert tw_re[k] == pytest.approx(math.cos(angle), abs=1e-10)
            assert tw_im[k] == pytest.approx(math.sin(angle), abs=1e-10)

    def test_twiddle_unit_circle(self):
        """Each twiddle factor lies on the unit circle: cos²+sin²=1."""
        tw_re, tw_im = main.precompute_twiddles(256)
        for k in range(128):
            mag_sq = tw_re[k] ** 2 + tw_im[k] ** 2
            assert mag_sq == pytest.approx(1.0, abs=1e-12)
