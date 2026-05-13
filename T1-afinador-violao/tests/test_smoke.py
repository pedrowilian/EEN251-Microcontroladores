"""Smoke tests."""
import main


def test_imports():
    assert hasattr(main, "SAMPLE_RATE")
    assert hasattr(main, "N")
    assert hasattr(main, "TUNING")
    assert hasattr(main, "fft")
    assert hasattr(main, "main")


def test_constants():
    assert main.SAMPLE_RATE == 4000
    assert main.N == 2048
    assert main.HISTORY_SIZE == 5
    assert len(main.TUNING) == 6


def test_mock_adc(mock_adc):
    assert mock_adc.read_u16() == 32768


def test_sine_samples(sine_samples):
    s = sine_samples(frequency=110.0)
    assert len(s) == main.N
