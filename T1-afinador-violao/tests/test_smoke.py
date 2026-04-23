"""Smoke tests."""
import main


def test_imports():
    assert hasattr(main, "SAMPLE_RATE")
    assert hasattr(main, "N")
    assert hasattr(main, "TUNING")
    assert hasattr(main, "setup")
    assert hasattr(main, "fft")


def test_constants():
    assert main.SAMPLE_RATE == 4000
    assert main.N == 1024
    assert main.ALPHA == 0.386
    assert len(main.TUNING) == 6
    assert len(main.CORDAS) == 6


def test_setup_returns_tuple():
    result = main.setup()
    assert isinstance(result, tuple)
    assert len(result) == 12


def test_mock_adc(mock_adc):
    assert mock_adc.read_u16() == 32768
    mock_adc.set_values([100, 200])
    assert mock_adc.read_u16() == 100


def test_mock_pin(mock_pin):
    mock_pin.value(1)
    assert mock_pin.value() == 1


def test_sine_samples(sine_samples):
    s = sine_samples(frequency=110.0)
    assert len(s) == main.N
