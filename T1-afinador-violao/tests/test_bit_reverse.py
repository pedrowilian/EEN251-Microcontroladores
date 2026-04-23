"""Tests for bit_reverse() with pre-computed table."""
import main


class TestBitReverse:
    def test_identity_for_n1(self):
        re = [42.0]
        im = [7.0]
        table = main.precompute_bit_reverse_table(1)
        main.bit_reverse(re, im, table, 1)
        assert re == [42.0]
        assert im == [7.0]

    def test_n2_no_change(self):
        re = [1.0, 2.0]
        im = [3.0, 4.0]
        table = main.precompute_bit_reverse_table(2)
        main.bit_reverse(re, im, table, 2)
        assert re == [1.0, 2.0]
        assert im == [3.0, 4.0]

    def test_n4_known_permutation(self):
        re = [0.0, 1.0, 2.0, 3.0]
        im = [10.0, 11.0, 12.0, 13.0]
        table = main.precompute_bit_reverse_table(4)
        main.bit_reverse(re, im, table, 4)
        assert re == [0.0, 2.0, 1.0, 3.0]
        assert im == [10.0, 12.0, 11.0, 13.0]

    def test_n8_known_permutation(self):
        re = [float(i) for i in range(8)]
        im = [0.0] * 8
        table = main.precompute_bit_reverse_table(8)
        main.bit_reverse(re, im, table, 8)
        assert re == [0.0, 4.0, 2.0, 6.0, 1.0, 5.0, 3.0, 7.0]

    def test_involution_property(self):
        n = 16
        re_orig = [float(i) for i in range(n)]
        im_orig = [float(i + 100) for i in range(n)]
        re = list(re_orig)
        im = list(im_orig)
        table = main.precompute_bit_reverse_table(n)
        main.bit_reverse(re, im, table, n)
        main.bit_reverse(re, im, table, n)
        assert re == re_orig
        assert im == im_orig

    def test_preserves_set_of_values(self):
        n = 32
        re = [float(i) for i in range(n)]
        im = [float(i * 2) for i in range(n)]
        re_set = set(re)
        im_set = set(im)
        table = main.precompute_bit_reverse_table(n)
        main.bit_reverse(re, im, table, n)
        assert set(re) == re_set
        assert set(im) == im_set

    def test_real_and_imag_swapped_together(self):
        n = 8
        re = [float(i) for i in range(n)]
        im = [float(i + 100) for i in range(n)]
        table = main.precompute_bit_reverse_table(n)
        main.bit_reverse(re, im, table, n)
        for k in range(n):
            assert im[k] == re[k] + 100.0

    def test_n1024_involution(self):
        n = 1024
        re = [float(i) for i in range(n)]
        im = [0.0] * n
        re_orig = list(re)
        table = main.precompute_bit_reverse_table(n)
        main.bit_reverse(re, im, table, n)
        main.bit_reverse(re, im, table, n)
        assert re == re_orig
