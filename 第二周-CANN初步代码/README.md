# 第二周作业：CANN 报名、卡时领取与赛题初步代码

对应课程仓库《卓越班每周作业汇总》第二周（2026-09-24）要求：完成 CANN 报名，领取卡时，利用大模型基于赛题做一个初步代码，上传 GitHub 仓库。

## 一、任务拆解与完成情况

| 任务 | 交付物 | 状态 |
| --- | --- | --- |
| 了解 2026 CANN 挑战赛与赛题方向 | `docs/CANN报名与卡时记录.md` | 已完成 |
| 完成 CANN 报名 | 报名回执截图（需本人账号） | 待本人操作，流程与登记表已准备 |
| 领取免费卡时 | 卡时/代金券截图（需本人账号） | 待本人操作，流程与登记表已准备 |
| 用大模型生成赛题初步代码 | `05_add_custom/`、`python/` | 已完成 |
| 代码上传 GitHub | 本目录 | 已完成 |

> 报名、实名认证、领取卡时均需使用学生本人的华为账号，并可能涉及人脸/证件核验。为避免造假，本仓库不放置任何伪造截图；完成平台操作后，请按 `docs/CANN报名与卡时记录.md` 的登记表补充截图路径。

## 二、赛题理解

CANN 挑战赛的核心是“算子开发”：使用 Ascend C 编写在 AI Core 上运行的算子，完成从需求分析、算子设计、Kernel 实现、Tiling 设计到精度与性能验证的完整流程。

本次初步代码选择最基础的**向量加法（Add）**作为切入：

- 输入：两个长度为 `N` 的 `float32` 向量 `x`、`y`；
- 输出：`z[i] = x[i] + y[i]`；
- 并行策略：按 `block_dim` 个 AI Core 切分数据，每个核内再按 `tile` 切分；
- 流水结构：Double Buffer，`CopyIn -> Compute -> CopyOut`；
- 约束：`DataCopy` 要求 32B 对齐，因此每个 tile 的长度需为 8 个 `float` 的整数倍。

## 三、代码结构

```text
第二周-CANN初步代码/
├── 05_add_custom/
│   ├── add_custom.cpp        # Ascend C Kernel 实现（Add）
│   ├── add_custom_tiling.h   # Tiling 数据结构（Kernel/Host 共用）
│   └── main.cpp              # ACL Host 侧调用与结果比对
├── python/
│   ├── golden_add.py         # CPU 金标准 + 分块模拟
│   └── test_golden_add.py    # 9 个单元测试
├── docs/
│   ├── CANN报名与卡时记录.md
│   ├── 大模型辅助生成记录.md
│   └── evidence/README.md    # 平台截图放置说明
├── results/
│   └── cpu_verification.txt  # 真实执行的测试输出
└── README.md
```

## 四、已完成的验证

在没有 NPU 的开发机上，先验证与硬件无关的部分：

```bash
cd 第二周-CANN初步代码/python
python3 -m unittest -v test_golden_add.py
```

实际结果：**9 个测试全部通过**，输出见 `results/cpu_verification.txt`。覆盖：

1. 正数、正负混合、空输入；
2. 长度不一致时抛出异常；
3. 浮点精度；
4. 与 Kernel 相同形状（8192 元素、8 核、每核 8 tile）时分块结果与朴素实现完全一致；
5. 分块覆盖性（无遗漏、无重复）；
6. 非对齐长度、非法 tile 数的异常处理。

## 五、在昇腾环境编译（待有 NPU 时执行）

本目录代码以 CANN 官方 `AddCustom` 样例的 KernelLaunch 结构为模板编写。由于不同 CANN 版本的自定义算子工程目录与 CMake 宏可能不同，建议按以下方式接入，而不是直接套用某个固定版本的构建脚本：

1. 安装 CANN Toolkit（建议 8.0.RC2 及以上），执行 `source ${ASCEND_HOME_PATH}/set_env.sh`；
2. 使用 `msopgen` 创建自定义算子工程，算子类型命名为 `AddCustom`，输入输出均为 `float32`；
3. 将 `add_custom.cpp` 放入 Kernel 实现目录，将 `add_custom_tiling.h` 放入 Tiling 目录；
4. 在 Host 侧按 `main.cpp` 的方式构造 Tiling、申请 Device 内存并调用 `add_custom_do`；
5. 依次执行 `bash build.sh`、算子包部署、`./add_custom`，预期输出 `[PASS] add_custom 结果与 CPU 结果一致`。

> 尚未执行的步骤：CANN 安装、算子工程生成、Kernel 编译、NPU 实机运行与性能测试。当前环境不具备昇腾硬件与工具链，代码仅完成静态编写与 CPU 侧算法验证，未声称已通过 NPU 测试。

## 六、后续计划

1. 领取卡时后，在云端 CANN 环境完成首次编译，记录编译日志与报错；
2. 使用 `msprof` 或 Profiling 工具采集性能数据，对比不同 `tile_num` 与 `block_dim` 的耗时；
3. 将算子扩展到 `float16`、`int32`，并补充非对齐长度的 `DataCopyPad` 实现；
4. 输出精度对比报告（最大绝对误差、相对误差、通过率）。

## 七、真实性声明

- `results/cpu_verification.txt` 为本机真实执行输出，未修改；
- CANN 报名与卡时领取需本人账号操作，仓库不伪造截图；
- Ascend C 代码未在 NPU 上编译运行，相关结论均标注为“待验证”。

---

完成日期：2026-11-25
