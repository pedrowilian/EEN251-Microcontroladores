"""Unit tests for identify_note() — NoteIdentifier component."""

import main


class TestIdentifyNote:
    """Tests for identify_note(frequency)."""

    def test_exact_e2(self):
        """Exact E2 frequency returns E2."""
        note, ref = main.identify_note(82.41)
        assert note == "E2"
        assert ref == 82.41

    def test_exact_a2(self):
        """Exact A2 frequency returns A2."""
        note, ref = main.identify_note(110.00)
        assert note == "A2"
        assert ref == 110.00

    def test_exact_d3(self):
        """Exact D3 frequency returns D3."""
        note, ref = main.identify_note(146.83)
        assert note == "D3"
        assert ref == 146.83

    def test_exact_g3(self):
        """Exact G3 frequency returns G3."""
        note, ref = main.identify_note(196.00)
        assert note == "G3"
        assert ref == 196.00

    def test_exact_b3(self):
        """Exact B3 frequency returns B3."""
        note, ref = main.identify_note(246.94)
        assert note == "B3"
        assert ref == 246.94

    def test_exact_e4(self):
        """Exact E4 frequency returns E4."""
        note, ref = main.identify_note(329.63)
        assert note == "E4"
        assert ref == 329.63

    def test_slightly_above_a2(self):
        """Frequency slightly above A2 still returns A2."""
        note, ref = main.identify_note(112.0)
        assert note == "A2"
        assert ref == 110.00

    def test_slightly_below_a2(self):
        """Frequency slightly below A2 still returns A2."""
        note, ref = main.identify_note(108.0)
        assert note == "A2"
        assert ref == 110.00

    def test_midpoint_between_e2_and_a2(self):
        """Frequency at midpoint between E2 and A2 returns the closer one."""
        # Midpoint = (82.41 + 110.00) / 2 = 96.205
        # E2 diff = 96.205 - 82.41 = 13.795
        # A2 diff = 110.00 - 96.205 = 13.795
        # Equal distance — first found (E2) wins due to strict < comparison
        note, ref = main.identify_note(96.205)
        assert note == "E2"
        assert ref == 82.41

    def test_just_past_midpoint_toward_a2(self):
        """Frequency just past midpoint toward A2 returns A2."""
        note, ref = main.identify_note(96.21)
        assert note == "A2"
        assert ref == 110.00

    def test_very_low_frequency(self):
        """Frequency well below E2 still returns E2 (closest)."""
        note, ref = main.identify_note(50.0)
        assert note == "E2"
        assert ref == 82.41

    def test_very_high_frequency(self):
        """Frequency well above E4 still returns E4 (closest)."""
        note, ref = main.identify_note(500.0)
        assert note == "E4"
        assert ref == 329.63

    def test_returns_tuple(self):
        """identify_note returns a tuple of (str, float)."""
        result = main.identify_note(110.0)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], float)
