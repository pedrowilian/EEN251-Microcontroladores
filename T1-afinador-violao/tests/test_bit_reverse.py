"""Tests for the bit_reverse function (FFT Engine — Task 5.2)."""

import math
import main


class TestBitReverse:
    """Unit tests for bit_reverse in-place permutation."""

    def test_identity_for_n1(self):
        """Single element should remain unchanged."""
        re = [42.0]
        im = [7.0]
        main.bit_reverse(re, im, 1)
        assert re == [42.0]
        assert im == [7.0]

    def test_n2_no_change(self):
        """For n=2, index 0 stays at 0 and index 1 stays at 1."""
        re = [1.0, 2.0]
        im = [3.0, 4.0]
        main.bit_reverse(re, im, 2)
        assert re == [1.0, 2.0]
        assert im == [3.0, 4.0]

    def test_n4_known_permutation(self):
        """For n=4 (2 bits), bit-reversal maps: 0->0, 1->2, 2->1, 3->3."""
        re = [0.0, 1.0, 2.0, 3.0]
        im = [10.0, 11.0, 12.0, 13.0]
        main.bit_reverse(re, im, 4)
        assert re == [0.0, 2.0, 1.0, 3.0]
        assert im == [10.0, 12.0, 11.0, 13.0]

    def test_n8_known_permutation(self):
        """For n=8 (3 bits), verify the standard bit-reversal order."""
        # Bit-reversal for 3 bits: 0->0, 1->4, 2->2, 3->6, 4->1, 5->5, 6->3, 7->7
        re = list(range(8, dtype=None)) if False else [float(i) for i in range(8)]
        im = [0.0] * 8
        main.bit_reverse(re, im, 8)
        expected = [0.0, 4.0, 2.0, 6.0, 1.0, 5.0, 3.0, 7.0]
        assert re == expected

    def test_involution_property(self):
        """Applying bit_reverse twice should restore the original order."""
        n = 16
        re_orig = [float(i) for i in range(n)]
        im_orig = [float(i + 100) for i in range(n)]
        re = list(re_orig)
        im = list(im_orig)
        main.bit_reverse(re, im, n)
        main.bit_reverse(re, im, n)
        assert re == re_orig
        assert im == im_orig

    def test_preserves_set_of_values(self):
        """Bit-reversal is a permutation — the set of values must be unchanged."""
        n = 32
        re = [float(i) for i in range(n)]
        im = [float(i * 2) for i in range(n)]
        re_set_before = set(re)
        im_set_before = set(im)
        main.bit_reverse(re, im, n)
        assert set(re) == re_set_before
        assert set(im) == im_set_before

    def test_real_and_imag_swapped_together(self):
        """Real and imaginary parts at the same index must move together."""
        n = 8
        re = [float(i) for i in range(n)]
        im = [float(i + 100) for i in range(n)]
        main.bit_reverse(re, im, n)
        # After bit-reversal, for each position k, re[k] and im[k]
        # should correspond to the same original index
        for k in range(n):
            assert im[k] == re[k] + 100.0

    def test_n2048_involution(self):
        """Bit-reversal on the actual FFT size (N=2048) is an involution."""
        n = 2048
        re = [float(i) for i in range(n)]
        im = [0.0] * n
        re_orig = list(re)
        main.bit_reverse(re, im, n)
        main.bit_reverse(re, im, n)
        assert re == re_orig
