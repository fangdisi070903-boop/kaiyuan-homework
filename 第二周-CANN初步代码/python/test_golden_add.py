"""Add 算子金标准单元测试（CPU，无需 NPU / CANN）。

运行：
    python3 -m unittest -v test_golden_add.py
"""

import random
import unittest

from golden_add import add_naive, add_tiled, max_abs_diff


class TestAddNaive(unittest.TestCase):
    def test_positive_numbers(self):
        self.assertEqual(add_naive([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]),
                         [5.0, 7.0, 9.0])

    def test_mixed_sign_numbers(self):
        self.assertEqual(add_naive([-1.5, 0.0, 2.5], [1.5, -0.0, -2.5]),
                         [0.0, 0.0, 0.0])

    def test_empty_input(self):
        self.assertEqual(add_naive([], []), [])

    def test_length_mismatch_raises(self):
        with self.assertRaises(ValueError):
            add_naive([1.0, 2.0], [1.0])

    def test_float_precision(self):
        result = add_naive([0.1, 0.2], [0.2, 0.3])
        self.assertLess(max_abs_diff(result, [0.3, 0.5]), 1e-9)


class TestAddTiled(unittest.TestCase):
    def test_tiled_equals_naive_on_kernel_shape(self):
        """使用与 Kernel 相同的形状：8192 元素、8 核、每核 8 tile。"""
        total = 8 * 1024
        random.seed(20261125)
        x = [random.uniform(-100, 100) for _ in range(total)]
        y = [random.uniform(-100, 100) for _ in range(total)]

        expected = add_naive(x, y)
        actual = add_tiled(x, y, block_dim=8, tile_num=8)

        self.assertEqual(len(actual), total)
        self.assertEqual(actual, expected)

    def test_tiled_covers_every_element(self):
        """用“每个位置加不同偏移”的方式检查是否有遗漏或重复写入。"""
        total = 64
        x = [float(i) for i in range(total)]
        y = [0.0] * total
        result = add_tiled(x, y, block_dim=4, tile_num=2)
        self.assertEqual(result, x)

    def test_tiled_rejects_unaligned_length(self):
        with self.assertRaises(ValueError):
            add_tiled([0.0] * 10, [0.0] * 10, block_dim=4, tile_num=2)

    def test_tiled_rejects_zero_tile(self):
        with self.assertRaises(ValueError):
            add_tiled([0.0] * 32, [0.0] * 32, block_dim=4, tile_num=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
