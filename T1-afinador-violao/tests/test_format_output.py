"""Testes unitários para format_output."""

from main import format_output


class TestFormatOutput:
    """Testes para a função format_output."""

    def test_sharp_positive_deviation(self):
        result = format_output("A2", 111.5, 110.0, "Sustenido (Sharp)", 1.5)
        assert result == "Nota: A2 | Freq: 111.5 Hz | Ref: 110.0 Hz | Status: Sustenido (Sharp) (+1.5 Hz)"

    def test_flat_negative_deviation(self):
        result = format_output("E2", 80.0, 82.41, "Bemol (Flat)", -2.41)
        assert result == "Nota: E2 | Freq: 80.0 Hz | Ref: 82.4 Hz | Status: Bemol (Flat) (-2.4 Hz)"

    def test_tuned_zero_deviation(self):
        result = format_output("D3", 146.83, 146.83, "Afinado", 0.0)
        assert result == "Nota: D3 | Freq: 146.8 Hz | Ref: 146.8 Hz | Status: Afinado (+0.0 Hz)"

    def test_tuned_small_positive_deviation(self):
        result = format_output("G3", 196.5, 196.0, "Afinado", 0.5)
        assert result == "Nota: G3 | Freq: 196.5 Hz | Ref: 196.0 Hz | Status: Afinado (+0.5 Hz)"

    def test_output_contains_all_fields(self):
        result = format_output("B3", 248.0, 246.94, "Sustenido (Sharp)", 1.06)
        assert "B3" in result
        assert "248.0" in result
        assert "246.9" in result
        assert "Sustenido (Sharp)" in result
        assert "1.1" in result  # 1.06 rounded to 1 decimal
