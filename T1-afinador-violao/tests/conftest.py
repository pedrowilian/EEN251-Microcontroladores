"""
Shared test configuration and fixtures for the guitar tuner project.

Mocks the `machine` module (ADC, Pin) so that main.py can be imported
on a host PC without MicroPython hardware.
"""

import sys
import math
import array
import types
import time

# ---------------------------------------------------------------------------
# Mock MicroPython-specific time functions for host-side testing
# ---------------------------------------------------------------------------
if not hasattr(time, "sleep_us"):
    time.sleep_us = lambda us: None
if not hasattr(time, "sleep_ms"):
    time.sleep_ms = lambda ms: None

# ---------------------------------------------------------------------------
# Mock the `machine` module BEFORE any import of main.py
# ---------------------------------------------------------------------------

_machine_module = types.ModuleType("machine")


class MockPin:
    """Mock of machine.Pin for host-side testing."""

    OUT = 1
    IN = 0

    def __init__(self, pin_number, mode=None):
        self.pin_number = pin_number
        self.mode = mode
        self._value = 0

    def value(self, val=None):
        if val is None:
            return self._value
        self._value = val


class MockADC:
    """Mock of machine.ADC for host-side testing.

    By default returns the midpoint value (32768). Feed custom values
    via `set_values()` to simulate real ADC readings.
    """

    def __init__(self, pin=26):
        self.pin = pin
        self._values = []
        self._index = 0
        self._default_value = 32768  # midpoint of 16-bit range

    def set_values(self, values):
        """Load a sequence of values that read_u16() will return."""
        self._values = list(values)
        self._index = 0

    def read_u16(self):
        """Return the next value from the configured sequence, or default."""
        if self._values:
            val = self._values[self._index % len(self._values)]
            self._index += 1
            return val
        return self._default_value


# Patch sys.modules so `from machine import ADC, Pin` works on host
_machine_module.ADC = MockADC
_machine_module.Pin = MockPin
sys.modules["machine"] = _machine_module

# ---------------------------------------------------------------------------
# Now it is safe to import main
# ---------------------------------------------------------------------------
import main  # noqa: E402

# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------
import pytest


# -- Constants exposed as fixtures --

@pytest.fixture
def sample_rate():
    """System sample rate (Hz)."""
    return main.SAMPLE_RATE


@pytest.fixture
def n_samples():
    """Number of samples (must be power of 2)."""
    return main.N


@pytest.fixture
def alpha():
    """IIR low-pass filter coefficient."""
    return main.ALPHA


@pytest.fixture
def signal_threshold():
    """Peak-to-peak amplitude threshold for signal detection."""
    return main.SIGNAL_THRESHOLD


@pytest.fixture
def tuning_tolerance():
    """Tuning tolerance in Hz."""
    return main.TUNING_TOLERANCE


@pytest.fixture
def standard_tuning():
    """Standard guitar tuning table [(note, freq), ...]."""
    return list(main.STANDARD_TUNING)


@pytest.fixture
def bin_min():
    return main.BIN_MIN


@pytest.fixture
def bin_max():
    return main.BIN_MAX


# -- Array / signal helpers --

@pytest.fixture
def silent_samples():
    """Array of N samples at the ADC midpoint (no signal)."""
    return array.array("H", [32768] * main.N)


@pytest.fixture
def sine_samples():
    """Factory fixture: generate N 16-bit ADC samples of a pure sine wave.

    Usage in tests:
        samples = sine_samples(frequency=110.0, amplitude=5000)
    """

    def _make(frequency: float, amplitude: float = 10000.0):
        mid = 32768
        n = main.N
        sr = main.SAMPLE_RATE
        return array.array(
            "H",
            [
                max(0, min(65535, int(mid + amplitude * math.sin(2 * math.pi * frequency * i / sr))))
                for i in range(n)
            ],
        )

    return _make


@pytest.fixture
def mock_adc():
    """Return a fresh MockADC instance."""
    return MockADC()


@pytest.fixture
def mock_pin():
    """Return a fresh MockPin instance (output mode, pin 25)."""
    return MockPin(25, MockPin.OUT)
