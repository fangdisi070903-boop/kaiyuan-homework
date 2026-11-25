/**
 * Add 算子 Host 侧调用示例（ACL）。
 *
 * 流程：
 *   1. 初始化 ACL、申请 Device、创建 Stream；
 *   2. 准备输入数据并拷贝到 Device；
 *   3. 构造 Tiling 数据并拷贝到 Device；
 *   4. 调用 add_custom_do 启动 Kernel；
 *   5. 将结果拷贝回 Host，与 CPU 结果逐元素比对；
 *   6. 释放资源。
 *
 * 注意：本文件是课程作业的初步代码，未在昇腾环境编译验证。
 *       add_custom_do 由 CANN 自定义算子构建流程生成，签名以实际版本为准。
 */

#include <acl/acl.h>

#include <cmath>
#include <cstdio>
#include <vector>

#include "add_custom_tiling.h"

extern "C" void add_custom_do(uint32_t blockDim, void *stream, uint8_t *x,
                              uint8_t *y, uint8_t *z, uint8_t *tiling);

constexpr uint32_t TOTAL_LENGTH = 8 * 1024;  // 8192 个 float
constexpr uint32_t TILE_NUM = 8;             // 每个核切 8 个 tile
constexpr uint32_t BLOCK_DIM = 8;            // 使用 8 个 AI Core
constexpr size_t DATA_BYTES = TOTAL_LENGTH * sizeof(float);
constexpr float EPS = 1e-5f;

#define ACL_CHECK(expr)                                                     \
    do {                                                                    \
        aclError ret = (expr);                                              \
        if (ret != ACL_SUCCESS) {                                           \
            printf("[FAIL] %s -> aclError=%d (%s:%d)\n", #expr, ret,        \
                   __FILE__, __LINE__);                                     \
            return -1;                                                      \
        }                                                                   \
    } while (0)

int main()
{
    // 对齐检查：每个 tile 必须是 32B（8 个 float）的整数倍
    const uint32_t perCore = TOTAL_LENGTH / BLOCK_DIM;
    const uint32_t tileLength = perCore / TILE_NUM / 2;
    if (perCore * BLOCK_DIM != TOTAL_LENGTH || tileLength % 8 != 0) {
        printf("[FAIL] 长度不满足对齐要求: total=%u, perCore=%u, tileLength=%u\n",
               TOTAL_LENGTH, perCore, tileLength);
        return -1;
    }

    std::vector<float> xHost(TOTAL_LENGTH);
    std::vector<float> yHost(TOTAL_LENGTH);
    std::vector<float> zHost(TOTAL_LENGTH, 0.0f);
    for (uint32_t i = 0; i < TOTAL_LENGTH; ++i) {
        xHost[i] = static_cast<float>(i % 100) * 0.5f;
        yHost[i] = static_cast<float>(i % 37) * 0.25f;
    }

    ACL_CHECK(aclInit(nullptr));
    ACL_CHECK(aclrtSetDevice(0));

    aclrtStream stream = nullptr;
    ACL_CHECK(aclrtCreateStream(&stream));

    void *xDevice = nullptr;
    void *yDevice = nullptr;
    void *zDevice = nullptr;
    void *tilingDevice = nullptr;

    ACL_CHECK(aclrtMalloc(&xDevice, DATA_BYTES, ACL_MEM_MALLOC_HUGE_FIRST));
    ACL_CHECK(aclrtMalloc(&yDevice, DATA_BYTES, ACL_MEM_MALLOC_HUGE_FIRST));
    ACL_CHECK(aclrtMalloc(&zDevice, DATA_BYTES, ACL_MEM_MALLOC_HUGE_FIRST));

    ACL_CHECK(aclrtMemcpy(xDevice, DATA_BYTES, xHost.data(), DATA_BYTES,
                          ACL_MEMCPY_HOST_TO_DEVICE));
    ACL_CHECK(aclrtMemcpy(yDevice, DATA_BYTES, yHost.data(), DATA_BYTES,
                          ACL_MEMCPY_HOST_TO_DEVICE));

    optiling::AddCustomTilingData tiling;
    tiling.set_totalLength(TOTAL_LENGTH);
    tiling.set_tileNum(TILE_NUM);

    ACL_CHECK(aclrtMalloc(&tilingDevice, tiling.GetDataSize(),
                          ACL_MEM_MALLOC_HUGE_FIRST));
    ACL_CHECK(aclrtMemcpy(tilingDevice, tiling.GetDataSize(), &tiling,
                          tiling.GetDataSize(), ACL_MEMCPY_HOST_TO_DEVICE));

    add_custom_do(BLOCK_DIM, stream, static_cast<uint8_t *>(xDevice),
                  static_cast<uint8_t *>(yDevice),
                  static_cast<uint8_t *>(zDevice),
                  static_cast<uint8_t *>(tilingDevice));

    ACL_CHECK(aclrtSynchronizeStream(stream));
    ACL_CHECK(aclrtMemcpy(zHost.data(), DATA_BYTES, zDevice, DATA_BYTES,
                          ACL_MEMCPY_DEVICE_TO_HOST));

    uint32_t mismatches = 0;
    for (uint32_t i = 0; i < TOTAL_LENGTH; ++i) {
        const float expect = xHost[i] + yHost[i];
        if (std::fabs(zHost[i] - expect) > EPS) {
            if (mismatches < 5) {
                printf("[MISMATCH] index=%u, got=%f, expect=%f\n", i, zHost[i],
                       expect);
            }
            ++mismatches;
        }
    }

    printf("total=%u, mismatches=%u\n", TOTAL_LENGTH, mismatches);

    ACL_CHECK(aclrtFree(xDevice));
    ACL_CHECK(aclrtFree(yDevice));
    ACL_CHECK(aclrtFree(zDevice));
    ACL_CHECK(aclrtFree(tilingDevice));
    ACL_CHECK(aclrtDestroyStream(stream));
    ACL_CHECK(aclrtResetDevice(0));
    ACL_CHECK(aclFinalize());

    if (mismatches == 0) {
        printf("[PASS] add_custom 结果与 CPU 结果一致\n");
        return 0;
    }
    printf("[FAIL] add_custom 结果存在偏差\n");
    return 1;
}
