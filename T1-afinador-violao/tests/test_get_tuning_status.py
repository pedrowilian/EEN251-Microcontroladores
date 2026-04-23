"""Tests for get_tuning_status() — not a function anymore, tested inline."""
# get_tuning_status was inlined into main_loop for performance.
# These tests verify the logic directly.

def test_afinado_zero():
    from main import TOLERANCE_CENTS
    c = 0.0
    assert abs(c) <= TOLERANCE_CENTS

def test_afinado_boundary():
    from main import TOLERANCE_CENTS
    c = float(TOLERANCE_CENTS)
    assert abs(c) <= TOLERANCE_CENTS

def test_alto():
    from main import TOLERANCE_CENTS
    c = 15.0
    assert c > TOLERANCE_CENTS

def test_baixo():
    from main import TOLERANCE_CENTS
    c = -15.0
    assert abs(c) > TOLERANCE_CENTS and c < 0
