"""Testes unitários para a função fft() — FFT Cooley-Tukey radix-2 DIT."""

import math
import pytest
from main import fft, precompute_twiddles


def _make_sine(freq, n, sample_rate):
    """Gera um sinal senoidal puro com frequência `freq` Hz."""
    return [math.sin(2 * math.pi * freq * i / sample_rate) for i in range(n)]


class TestFFTZeros:
    """FFT de sinal todo-zero deve produzir espectro todo-zero."""

    def test_all_zeros(self):
        n = 64
        data_re = [0.0] * n
        data_im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)

        fft(data_re, data_im, tw_re, tw_im, n)

        for k in range(n):
            assert data_re[k] == pytest.approx(0.0, abs=1e-12)
            assert data_im[k] == pytest.approx(0.0, abs=1e-12)


class TestFFTDCSignal:
    """FFT de sinal DC (constante) deve ter energia apenas no bin 0."""

    def test_dc_signal(self):
        n = 128
        dc_value = 3.5
        data_re = [dc_value] * n
        data_im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)

        fft(data_re, data_im, tw_re, tw_im, n)

        # Bin 0 deve conter n * dc_value
        assert data_re[0] == pytest.approx(n * dc_value, rel=1e-9)
        assert data_im[0] == pytest.approx(0.0, abs=1e-9)

        # Todos os outros bins devem ser ~zero
        for k in range(1, n):
            assert data_re[k] == pytest.approx(0.0, abs=1e-9)
            assert data_im[k] == pytest.approx(0.0, abs=1e-9)


class TestFFTPureSine:
    """FFT de senoide pura deve ter pico no bin correto."""

    def test_sine_peak_at_correct_bin(self):
        n = 256
        sample_rate = 1024
        freq = 128.0  # Deve cair exatamente no bin 32 (128 * 256 / 1024)
        expected_bin = int(freq * n / sample_rate)

        data_re = _make_sine(freq, n, sample_rate)
        data_im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)

        fft(data_re, data_im, tw_re, tw_im, n)

        # Calcular magnitudes
        magnitudes = [
            math.sqrt(data_re[k] ** 2 + data_im[k] ** 2) for k in range(n // 2)
        ]

        # O pico deve estar no bin esperado
        peak_bin = max(range(len(magnitudes)), key=lambda k: magnitudes[k])
        assert peak_bin == expected_bin

        # A magnitude do pico deve ser significativamente maior que os outros bins
        peak_mag = magnitudes[peak_bin]
        for k in range(len(magnitudes)):
            if k != peak_bin:
                assert magnitudes[k] < peak_mag * 0.1


class TestFFTParsevalTheorem:
    """Teorema de Parseval: sum(|X[k]|^2) == N * sum(|x[n]|^2)."""

    def test_parseval_sine(self):
        n = 256
        sample_rate = 1024
        freq = 100.0

        data_re = _make_sine(freq, n, sample_rate)
        data_im = [0.0] * n

        # Energia no domínio do tempo
        time_energy = sum(x ** 2 for x in data_re)

        tw_re, tw_im = precompute_twiddles(n)
        fft(data_re, data_im, tw_re, tw_im, n)

        # Energia no domínio da frequência
        freq_energy = sum(data_re[k] ** 2 + data_im[k] ** 2 for k in range(n))

        assert freq_energy == pytest.approx(n * time_energy, rel=1e-6)

    def test_parseval_dc(self):
        n = 64
        dc_value = 2.0
        data_re = [dc_value] * n
        data_im = [0.0] * n

        time_energy = sum(x ** 2 for x in data_re)

        tw_re, tw_im = precompute_twiddles(n)
        fft(data_re, data_im, tw_re, tw_im, n)

        freq_energy = sum(data_re[k] ** 2 + data_im[k] ** 2 for k in range(n))

        assert freq_energy == pytest.approx(n * time_energy, rel=1e-6)
