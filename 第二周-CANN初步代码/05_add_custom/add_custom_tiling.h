/**
 * Add 算子的 Tiling 数据结构。
 *
 * 该头文件同时被 Kernel 侧与 Host 侧包含：
 *   - Kernel 侧通过 GET_TILING_DATA 解析；
 *   - Host 侧通过 set_totalLength / set_tileNum 填充。
 */

#ifndef ADD_CUSTOM_TILING_H
#define ADD_CUSTOM_TILING_H

#include "register/tilingdata_base.h"

namespace optiling {

BEGIN_TILING_DATA_DEF(AddCustomTilingData)
TILING_DATA_FIELD_DEF(uint32_t, totalLength);
TILING_DATA_FIELD_DEF(uint32_t, tileNum);
END_TILING_DATA_DEF;

REGISTER_TILING_DATA_CLASS(AddCustom, AddCustomTilingData)

}  // namespace optiling

#endif  // ADD_CUSTOM_TILING_H
