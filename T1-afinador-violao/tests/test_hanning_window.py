"""Tests for apply_hanning()."""
import math
import pytest
from main import apply_hanning


def _make_hanning(n):
    return [0.5 * (1 - math.cos(6.283185307179586 * i / (n - 1))) for i in range(n)]


class TestApplyHanning:
    def test_endpoints_zero(self):
        n = 64
        han = _make_hanning(n)
        f = [1.0] * n
        apply_hanning(f, han, n)
        assert f[0] == pytest.approx(0.0, abs=1e-10)
        assert f[n - 1] == pytest.approx(0.0, abs=1e-10)

    def test_center_preserved(self):
        n = 65
        han = _make_hanning(n)
        f = [2.0] * n
        apply_hanning(f, han, n)
        assert f[n // 2] == pytest.approx(2.0, abs=1e-10)

    def test_in_place(self):
        n = 16
        han = _make_hanning(n)
        f = [1.0] * n
        assert apply_hanning(f, han, n) is None
        assert f[0] == pytest.approx(0.0, abs=1e-10)

    def test_symmetry(self):
        n = 128
        han = _make_hanning(n)
        f = [1.0] * n
        apply_hanning(f, han, n)
        for i in range(n // 2):
            assert f[i] == pytest.approx(f[n - 1 - i], abs=1e-10)

    def test_non_negative(self):
        n = 256
        han = _make_hanning(n)
        f = [1.0] * n
        apply_hanning(f, han, n)
        assert all(v >= 0.0 for v in f)
