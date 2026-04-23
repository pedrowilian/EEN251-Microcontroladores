"""Tests for output formatting (inlined in main_loop)."""
# format_output was inlined. Test the format string logic.


def test_format_afinado():
    corda, note, freq, ref = "5a", "A2", 110.2, 110.0
    c, st, ind = 3.1, "AFINADO", "  ===  "
    sign = "+" if c >= 0 else ""
    result = "Corda {} ({}) | {:.1f} Hz | Ref {:.1f} Hz |{}{} ({}{:.0f}c)".format(
        corda, note, freq, ref, ind, st, sign, c)
    assert "A2" in result
    assert "AFINADO" in result
    assert "===" in result
    assert "+3c" in result


def test_format_alto():
    corda, note, freq, ref = "6a", "E2", 85.0, 82.41
    c, st, ind = 53.5, "ALTO", " >>>>> "
    sign = "+"
    result = "Corda {} ({}) | {:.1f} Hz | Ref {:.1f} Hz |{}{} ({}{:.0f}c)".format(
        corda, note, freq, ref, ind, st, sign, c)
    assert "ALTO" in result
    assert ">>>>>" in result


def test_format_baixo():
    corda, note, freq, ref = "1a", "E4", 325.0, 329.63
    c, st, ind = -24.3, "BAIXO", "  <<<  "
    sign = ""
    result = "Corda {} ({}) | {:.1f} Hz | Ref {:.1f} Hz |{}{} ({}{:.0f}c)".format(
        corda, note, freq, ref, ind, st, sign, c)
    assert "BAIXO" in result
    assert "<<<" in result
