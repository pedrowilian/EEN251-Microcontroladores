"""Smoke tests to verify test infrastructure and main.py import."""

import main


def test_main_imports_successfully():
    """main.py can be imported on host via machine mock."""
    assert hasattr(main, "SAMPLE_RATE")
    assert hasattr(main, "N")
    assert hasattr(main, "STANDARD_TUNING")
    assert hasattr(main, "setup")


def test_constants_valid():
    """System constants have expected values."""
    assert main.SAMPLE_RATE == 4000
    assert main.N == 1024
    assert main.ALPHA == 0.386
    assert main.SIGNAL_THRESHOLD == 500
    assert main.TUNING_TOLERANCE == 1.0
    assert len(main.STANDARD_TUNING) == 6


def test_setup_returns_dict():
    """setup() returns a dict with all pre-allocated resources."""
    ctx = main.setup()
    assert isinstance(ctx, dict)
    assert "adc" in ctx
    assert "led" in ctx
    assert "samples" in ctx
    assert "filtered" in ctx
    assert "re" in ctx
    assert "im" in ctx
    assert "magnitudes" in ctx
    assert "twiddle_re" in ctx
    assert "twiddle_im" in ctx
    assert "signal" in ctx
    assert "hanning" in ctx


def test_mock_adc(mock_adc):
    """MockADC returns default midpoint and supports custom values."""
    assert mock_adc.read_u16() == 32768
    mock_adc.set_values([100, 200, 300])
    assert mock_adc.read_u16() == 100
    assert mock_adc.read_u16() == 200
    assert mock_adc.read_u16() == 300


def test_mock_pin(mock_pin):
    """MockPin tracks value correctly."""
    assert mock_pin.value() == 0
    mock_pin.value(1)
    assert mock_pin.value() == 1


def test_sine_samples_fixture(sine_samples):
    """sine_samples factory produces correct-length arrays."""
    samples = sine_samples(frequency=110.0, amplitude=5000)
    assert len(samples) == main.N
    assert all(0 <= s <= 65535 for s in samples)
