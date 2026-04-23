"""
Shared test configuration and fixtures for the guitar tuner project.

Mocks the `machine` module so main.py can be imported on a host PC.
"""

import sys
import math
import array
import types
import time

# ---------------------------------------------------------------------------
# Mock MicroPython-specific time functions
# ---------------------------------------------------------------------------
if not hasattr(time, "sleep_us"):
    time.sleep_us = lambda us: None
if not hasattr(time, "sleep_ms"):
    time.sleep_ms = lambda ms: None

# ---------------------------------------------------------------------------
# Mock the `machine` module
# ---------------------------------------------------------------------------
_machine_module = types.ModuleType("machine")


class MockPin:
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
    def __init__(self, pin=26):
        self.pin = pin
        self._values = []
        self._index = 0
        self._default_value = 32768

    def set_values(self, values):
        self._values = list(values)
        self._index = 0

    def read_u16(self):
        if self._values:
            val = self._values[self._index % len(self._values)]
            self._index += 1
            return val
        return self._default_value


_machine_module.ADC = MockADC
_machine_module.Pin = MockPin
sys.modules["machine"] = _machine_module

# ---------------------------------------------------------------------------
# Now safe to import main
# ---------------------------------------------------------------------------
import main  # noqa: E402
import pytest  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_rate():
    return main.SAMPLE_RATE


@pytest.fixture
def n_samples():
    return main.N


@pytest.fixture
def alpha():
    return main.ALPHA


@pytest.fixture
def signal_threshold():
    return main.SIGNAL_THRESHOLD


@pytest.fixture
def standard_tuning():
    return list(main.STANDARD_TUNING)


@pytest.fixture
def bin_min():
    return main.BIN_MIN


@pytest.fixture
def bin_max():
    return main.BIN_MAX


@pytest.fixture
def silent_samples():
    return array.array("H", [32768] * main.N)


@pytest.fixture
def sine_samples():
    """Factory: generate N 16-bit ADC samples of a pure sine wave."""
    def _make(frequency, amplitude=10000.0):
        mid = 32768
        n = main.N
        sr = main.SAMPLE_RATE
        return array.array(
            "H",
            [max(0, min(65535, int(mid + amplitude * math.sin(2 * math.pi * frequency * i / sr))))
             for i in range(n)],
        )
    return _make


@pytest.fixture
def mock_adc():
    return MockADC()


@pytest.fixture
def mock_pin():
    return MockPin(25, MockPin.OUT)
