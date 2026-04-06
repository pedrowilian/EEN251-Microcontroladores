"""Testes unitários para apply_hanning_window (versão com janela pré-calculada)."""

import math
import pytest
from main import apply_hanning_window


def _make_hanning(n):
    """Helper: cria janela de Hanning para testes."""
    return [0.5 * (1 - math.cos(2 * math.pi * i / (n - 1))) for i in range(n)]


class TestApplyHanningWindow:
    """Testes para a função apply_hanning_window."""

    def test_endpoints_are_zero(self):
        n = 64
        hanning = _make_hanning(n)
        filtered = [1.0] * n
        apply_hanning_window(filtered, hanning, n)
        assert filtered[0] == pytest.approx(0.0, abs=1e-10)
        assert filtered[n - 1] == pytest.approx(0.0, abs=1e-10)

    def test_center_is_preserved(self):
        n = 65
        mid = n // 2
        hanning = _make_hanning(n)
        filtered = [2.0] * n
        apply_hanning_window(filtered, hanning, n)
        assert filtered[mid] == pytest.approx(2.0, abs=1e-10)

    def test_in_place_modification(self):
        n = 16
        hanning = _make_hanning(n)
        filtered = [1.0] * n
        result = apply_hanning_window(filtered, hanning, n)
        assert result is None
        assert filtered[0] == pytest.approx(0.0, abs=1e-10)

    def test_known_values(self):
        n = 5
        hanning = _make_hanning(n)
        filtered = [1.0] * n
        apply_hanning_window(filtered, hanning, n)
        for i in range(n):
            expected = 0.5 * (1 - math.cos(2 * math.pi * i / (n - 1)))
            assert filtered[i] == pytest.approx(expected, abs=1e-10)

    def test_symmetry(self):
        n = 128
        hanning = _make_hanning(n)
        filtered = [1.0] * n
        apply_hanning_window(filtered, hanning, n)
        for i in range(n // 2):
            assert filtered[i] == pytest.approx(filtered[n - 1 - i], abs=1e-10)

    def test_all_values_non_negative(self):
        n = 256
        hanning = _make_hanning(n)
        filtered = [1.0] * n
        apply_hanning_window(filtered, hanning, n)
        for val in filtered:
            assert val >= 0.0

    def test_with_n_equals_2(self):
        hanning = _make_hanning(2)
        filtered = [5.0, 5.0]
        apply_hanning_window(filtered, hanning, 2)
        assert filtered[0] == pytest.approx(0.0, abs=1e-10)
        assert filtered[1] == pytest.approx(0.0, abs=1e-10)
