"""向量加法（Add）算子的 CPU 金标准实现。

用途：
    在没有昇腾 NPU 的环境中，先验证赛题算法本身的正确性，并为后续
    Kernel 输出提供逐元素比对基准。

说明：
    - 纯 Python 实现，不依赖 NumPy，任何 Python 3.8+ 环境均可运行。
    - add_tiled 模拟了 Kernel 侧“按核切分 + 按 tile 切分”的数据划分方式，
      用于检查分块边界是否覆盖完整、是否有元素遗漏或重复。
"""

from typing import List


def add_naive(x: List[float], y: List[float]) -> List[float]:
    """逐元素相加，作为最直观的参考实现。"""
    if len(x) != len(y):
        raise ValueError(f"输入长度不一致: len(x)={len(x)}, len(y)={len(y)}")
    return [a + b for a, b in zip(x, y)]


def add_tiled(x: List[float], y: List[float], block_dim: int = 8,
              tile_num: int = 8) -> List[float]:
    """按 Kernel 的数据划分方式模拟计算。

    划分规则与 add_custom.cpp 保持一致：
        per_core   = total_length / block_dim
        tile_length = per_core / tile_num / 2   （BUFFER_NUM = 2）
    每个核处理连续的一段，段内按 tile 顺序处理。
    """
    if len(x) != len(y):
        raise ValueError(f"输入长度不一致: len(x)={len(x)}, len(y)={len(y)}")
    total = len(x)
    if block_dim <= 0 or tile_num <= 0:
        raise ValueError("block_dim 与 tile_num 必须为正整数")
    if total % block_dim != 0:
        raise ValueError(f"总长度 {total} 不能被 block_dim={block_dim} 整除")

    per_core = total // block_dim
    tile_length = per_core // tile_num // 2
    if tile_length == 0:
        raise ValueError("tile_length 为 0，请增大数据量或减小分块数")

    result = [0.0] * total
    for block in range(block_dim):
        core_offset = block * per_core
        progress = 0
        # 与 Kernel 一致：每个 tile 处理 tile_length 个元素
        for _ in range(tile_num * 2):
            start = core_offset + progress * tile_length
            end = min(start + tile_length, core_offset + per_core)
            for i in range(start, end):
                result[i] = x[i] + y[i]
            progress += 1
    return result


def max_abs_diff(a: List[float], b: List[float]) -> float:
    """返回两个等长序列的最大绝对误差。"""
    if len(a) != len(b):
        raise ValueError("序列长度不一致，无法比较")
    return max((abs(x - y) for x, y in zip(a, b)), default=0.0)


if __name__ == "__main__":
    xs = [float(i) for i in range(32)]
    ys = [float(i) * 2 for i in range(32)]
    print("naive:", add_naive(xs, ys)[:8], "...")
    print("tiled:", add_tiled(xs, ys, block_dim=4, tile_num=2)[:8], "...")
