"""Testes unitários para a função find_peak_frequency()."""

import math
import pytest
from main import (
    find_peak_frequency,
    compute_magnitudes,
    fft,
    precompute_twiddles,
    remove_dc_offset,
    low_pass_filter,
    apply_hanning_window,
    SAMPLE_RATE,
    N,
    ALPHA,
    BIN_MIN,
    BIN_MAX,
)


class TestFindPeakFrequencyExactBin:
    """Testes com pico exatamente em um bin da FFT."""

    def test_peak_at_known_bin(self):
        """Pico em bin exato deve retornar frequência exata do bin."""
        n = 256
        sr = 1024
        half = n // 2
        magnitudes = [0.0] * half

        # Place peak at bin 32 → freq = 32 * 1024 / 256 = 128 Hz
        target_bin = 32
        magnitudes[target_bin] = 10.0
        magnitudes[target_bin - 1] = 5.0
        magnitudes[target_bin + 1] = 5.0  # symmetric → p = 0

        freq = find_peak_frequency(magnitudes, sr, n, 10, 100)
        expected = target_bin * sr / n  # 128.0
        assert freq == pytest.approx(expected, abs=0.01)

    def test_peak_at_different_bin(self):
        """Pico em outro bin exato com vizinhos simétricos."""
        n = 512
        sr = 2000
        half = n // 2
        magnitudes = [0.0] * half

        target_bin = 50  # freq = 50 * 2000 / 512 ≈ 195.3125 Hz
        magnitudes[target_bin] = 20.0
        magnitudes[target_bin - 1] = 8.0
        magnitudes[target_bin + 1] = 8.0

        freq = find_peak_frequency(magnitudes, sr, n, 10, 200)
        expected = target_bin * sr / n
        assert freq == pytest.approx(expected, abs=0.01)


class TestFindPeakFrequencyParabolicInterpolation:
    """Testes de interpolação parabólica para frequências entre bins."""

    def test_interpolation_shifts_frequency_up(self):
        """Vizinho direito maior que esquerdo deve deslocar frequência para cima."""
        n = 256
        sr = 1024
        half = n // 2
        magnitudes = [0.0] * half

        target_bin = 32
        magnitudes[target_bin] = 10.0
        magnitudes[target_bin - 1] = 3.0
        magnitudes[target_bin + 1] = 7.0  # right > left → shift up

        freq = find_peak_frequency(magnitudes, sr, n, 10, 100)
        bin_freq = target_bin * sr / n
        assert freq > bin_freq  # interpolation shifts up

    def test_interpolation_shifts_frequency_down(self):
        """Vizinho esquerdo maior que direito deve deslocar frequência para baixo."""
        n = 256
        sr = 1024
        half = n // 2
        magnitudes = [0.0] * half

        target_bin = 32
        magnitudes[target_bin] = 10.0
        magnitudes[target_bin - 1] = 7.0
        magnitudes[target_bin + 1] = 3.0  # left > right → shift down

        freq = find_peak_frequency(magnitudes, sr, n, 10, 100)
        bin_freq = target_bin * sr / n
        assert freq < bin_freq  # interpolation shifts down

    def test_interpolation_improves_accuracy(self):
        """Interpolação parabólica deve melhorar precisão para frequências off-bin."""
        # Generate a sine at a frequency that falls between bins
        n = 256
        sr = 1024
        target_freq = 130.0  # between bins 32 (128 Hz) and 33 (132 Hz)

        data_re = [math.sin(2 * math.pi * target_freq * i / sr) for i in range(n)]
        data_im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        fft(data_re, data_im, tw_re, tw_im, n)

        magnitudes = [0.0] * (n // 2)
        compute_magnitudes(data_re, data_im, magnitudes, n)

        freq = find_peak_frequency(magnitudes, sr, n, 10, 100)
        assert abs(freq - target_freq) < 2.0  # within 2 Hz


class TestFindPeakFrequencyEdgeCases:
    """Testes de casos de borda."""

    def test_peak_at_bin_min(self):
        """Pico no bin_min não deve aplicar interpolação (sem vizinho esquerdo)."""
        n = 256
        sr = 1024
        half = n // 2
        magnitudes = [0.0] * half

        bin_min = 10
        magnitudes[bin_min] = 15.0
        magnitudes[bin_min + 1] = 5.0

        freq = find_peak_frequency(magnitudes, sr, n, bin_min, 100)
        expected = bin_min * sr / n
        assert freq == pytest.approx(expected, abs=0.01)

    def test_peak_at_bin_max(self):
        """Pico no bin_max não deve aplicar interpolação (sem vizinho direito)."""
        n = 256
        sr = 1024
        half = n // 2
        magnitudes = [0.0] * half

        bin_max = 50
        magnitudes[bin_max] = 15.0
        magnitudes[bin_max - 1] = 5.0

        freq = find_peak_frequency(magnitudes, sr, n, 10, bin_max)
        expected = bin_max * sr / n
        assert freq == pytest.approx(expected, abs=0.01)

    def test_all_magnitudes_zero(self):
        """Todas as magnitudes zero devem retornar 0.0."""
        n = 256
        sr = 1024
        half = n // 2
        magnitudes = [0.0] * half

        freq = find_peak_frequency(magnitudes, sr, n, 10, 100)
        assert freq == 0.0

    def test_single_bin_range(self):
        """Faixa com um único bin (bin_min == bin_max)."""
        n = 256
        sr = 1024
        half = n // 2
        magnitudes = [0.0] * half

        target_bin = 32
        magnitudes[target_bin] = 10.0

        freq = find_peak_frequency(magnitudes, sr, n, target_bin, target_bin)
        expected = target_bin * sr / n
        assert freq == pytest.approx(expected, abs=0.01)


class TestFindPeakFrequencyIntegration:
    """Testes de integração com o pipeline FFT completo."""

    def _run_pipeline(self, freq_hz, n=N, sr=SAMPLE_RATE):
        """Executa o pipeline completo: senoide → DC offset → filtro → Hanning → FFT → pico."""
        import array as arr

        amplitude = 10000.0
        mid = 32768
        samples = arr.array(
            "H",
            [
                max(0, min(65535, int(mid + amplitude * math.sin(2 * math.pi * freq_hz * i / sr))))
                for i in range(n)
            ],
        )

        signal = [0.0] * n
        remove_dc_offset(samples, signal, n)
        filtered = [0.0] * n
        low_pass_filter(signal, filtered, ALPHA, n)
        hanning = [0.5 * (1 - math.cos(2 * math.pi * i / (n - 1))) for i in range(n)]
        apply_hanning_window(filtered, hanning, n)

        re = list(filtered)
        im = [0.0] * n
        tw_re, tw_im = precompute_twiddles(n)
        fft(re, im, tw_re, tw_im, n)

        magnitudes = [0.0] * (n // 2)
        compute_magnitudes(re, im, magnitudes, n)

        bin_min = int(70 * n / sr)
        bin_max = int(350 * n / sr)
        return find_peak_frequency(magnitudes, sr, n, bin_min, bin_max)

    def test_a2_110hz(self):
        """Pipeline completo com senoide de 110 Hz (A2) deve detectar ~110 Hz."""
        detected = self._run_pipeline(110.0)
        assert abs(detected - 110.0) <= 2.0

    def test_e4_329hz(self):
        """Pipeline completo com senoide de 329.63 Hz (E4) deve detectar ~329.63 Hz."""
        detected = self._run_pipeline(329.63)
        assert abs(detected - 329.63) <= 2.0

    def test_e2_82hz(self):
        """Pipeline completo com senoide de 82.41 Hz (E2) deve detectar ~82.41 Hz."""
        detected = self._run_pipeline(82.41)
        assert abs(detected - 82.41) <= 2.0

    def test_d3_146hz(self):
        """Pipeline completo com senoide de 146.83 Hz (D3) deve detectar ~146.83 Hz."""
        detected = self._run_pipeline(146.83)
        assert abs(detected - 146.83) <= 2.0
