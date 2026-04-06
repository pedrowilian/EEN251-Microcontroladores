"""Testes unitários para a função compute_magnitudes()."""

import math
import pytest
from main import compute_magnitudes, fft, precompute_twiddles


class TestComputeMagnitudesBasic:
    """Testes básicos de cálculo de magnitudes."""

    def test_all_zeros(self):
        """Magnitudes de espectro todo-zero devem ser zero."""
        n = 16
        re = [0.0] * n
        im = [0.0] * n
        magnitudes = [999.0] * (n // 2)

        compute_magnitudes(re, im, magnitudes, n)

        for k in range(n // 2):
            assert magnitudes[k] == pytest.approx(0.0, abs=1e-12)

    def test_real_only(self):
        """Quando im=0, magnitude deve ser |re[k]|."""
        n = 8
        re = [3.0, -4.0, 5.0, -6.0, 7.0, -8.0, 9.0, -10.0]
        im = [0.0] * n
        magnitudes = [0.0] * (n // 2)

        compute_magnitudes(re, im, magnitudes, n)

        for k in range(n // 2):
            assert magnitudes[k] == pytest.approx(abs(re[k]), rel=1e-9)

    def test_imaginary_only(self):
        """Quando re=0, magnitude deve ser |im[k]|."""
        n = 8
        re = [0.0] * n
        im = [2.0, -3.0, 4.0, -5.0, 6.0, -7.0, 8.0, -9.0]
        magnitudes = [0.0] * (n // 2)

        compute_magnitudes(re, im, magnitudes, n)

        for k in range(n // 2):
            assert magnitudes[k] == pytest.approx(abs(im[k]), rel=1e-9)

    def test_known_values(self):
        """Verifica magnitudes com valores conhecidos (3,4 → 5)."""
        n = 4
        re = [3.0, 0.0, 6.0, 0.0]
        im = [4.0, 0.0, 8.0, 0.0]
        magnitudes = [0.0] * (n // 2)

        compute_magnitudes(re, im, magnitudes, n)

        assert magnitudes[0] == pytest.approx(5.0, rel=1e-9)
        assert magnitudes[1] == pytest.approx(0.0, abs=1e-12)


class TestComputeMagnitudesHalfSpectrum:
    """Verifica que apenas a primeira metade do espectro é processada."""

    def test_only_first_half_written(self):
        """Apenas N/2 posições do array magnitudes devem ser escritas."""
        n = 16
        re = [float(i) for i in range(n)]
        im = [float(i) for i in range(n)]
        sentinel = -1.0
        magnitudes = [sentinel] * (n // 2)

        compute_magnitudes(re, im, magnitudes, n)

        for k in range(n // 2):
            expected = math.sqrt(re[k] ** 2 + im[k] ** 2)
            assert magnitudes[k] == pytest.approx(expected, rel=1e-9)


class TestComputeMagnitudesWithFFT:
    """Testa compute_magnitudes integrado com a FFT."""

    def test_sine_peak_magnitude(self):
        """Magnitude do pico de uma senoide pura deve ser dominante."""
        n = 256
        sample_rate = 1024
        freq = 128.0
        expected_bin = int(freq * n / sample_rate)

        data_re = [math.sin(2 * math.pi * freq * i / sample_rate) for i in range(n)]
        data_im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)

        fft(data_re, data_im, tw_re, tw_im, n)

        magnitudes = [0.0] * (n // 2)
        compute_magnitudes(data_re, data_im, magnitudes, n)

        peak_bin = max(range(len(magnitudes)), key=lambda k: magnitudes[k])
        assert peak_bin == expected_bin
        assert magnitudes[peak_bin] > 0
