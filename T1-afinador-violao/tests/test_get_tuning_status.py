"""Testes unitários para get_tuning_status()."""
from main import get_tuning_status, TUNING_TOLERANCE


class TestGetTuningStatus:
    """Testes para classificação do status de afinação."""

    def test_in_tune_exact(self):
        """Frequência exatamente igual à referência → Afinado."""
        status, deviation = get_tuning_status(110.0, 110.0)
        assert status == "Afinado"
        assert deviation == 0.0

    def test_in_tune_within_positive_tolerance(self):
        """Desvio positivo dentro da tolerância → Afinado."""
        status, deviation = get_tuning_status(110.5, 110.0)
        assert status == "Afinado"
        assert abs(deviation - 0.5) < 1e-9

    def test_in_tune_within_negative_tolerance(self):
        """Desvio negativo dentro da tolerância → Afinado."""
        status, deviation = get_tuning_status(109.5, 110.0)
        assert status == "Afinado"
        assert abs(deviation - (-0.5)) < 1e-9

    def test_in_tune_at_positive_boundary(self):
        """Desvio exatamente +1.0 Hz → Afinado (|d| ≤ 1.0)."""
        status, deviation = get_tuning_status(111.0, 110.0)
        assert status == "Afinado"
        assert abs(deviation - 1.0) < 1e-9

    def test_in_tune_at_negative_boundary(self):
        """Desvio exatamente -1.0 Hz → Afinado (|d| ≤ 1.0)."""
        status, deviation = get_tuning_status(109.0, 110.0)
        assert status == "Afinado"
        assert abs(deviation - (-1.0)) < 1e-9

    def test_sharp_above_tolerance(self):
        """Desvio > +1.0 Hz → Sustenido (Sharp)."""
        status, deviation = get_tuning_status(112.0, 110.0)
        assert status == "Sustenido (Sharp)"
        assert abs(deviation - 2.0) < 1e-9

    def test_flat_below_tolerance(self):
        """Desvio < -1.0 Hz → Bemol (Flat)."""
        status, deviation = get_tuning_status(108.0, 110.0)
        assert status == "Bemol (Flat)"
        assert abs(deviation - (-2.0)) < 1e-9

    def test_sharp_just_above_boundary(self):
        """Desvio ligeiramente acima de +1.0 Hz → Sustenido (Sharp)."""
        status, deviation = get_tuning_status(111.01, 110.0)
        assert status == "Sustenido (Sharp)"
        assert deviation > TUNING_TOLERANCE

    def test_flat_just_below_boundary(self):
        """Desvio ligeiramente abaixo de -1.0 Hz → Bemol (Flat)."""
        status, deviation = get_tuning_status(108.99, 110.0)
        assert status == "Bemol (Flat)"
        assert deviation < -TUNING_TOLERANCE

    def test_returns_correct_deviation_value(self):
        """Verifica que o desvio retornado é frequency - ref_frequency."""
        _, deviation = get_tuning_status(115.5, 110.0)
        assert abs(deviation - 5.5) < 1e-9

        _, deviation = get_tuning_status(105.0, 110.0)
        assert abs(deviation - (-5.0)) < 1e-9
