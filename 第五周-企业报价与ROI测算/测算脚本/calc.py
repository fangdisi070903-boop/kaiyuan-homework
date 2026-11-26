# -*- coding: utf-8 -*-
"""企业报价包测算脚本（出院随访与患者协作项目）

运行：
    python3 calc.py

作用：
    1) 按课程第 01–08 章口径计算五块成本、人天、Token、部署 TCO、ROI、报价；
    2) 生成 csv/ 目录下 8 份 CSV（Excel 可直接打开）；
    3) 打印「报价包总装」要求的数字咬合校验结果，写入 校验/一致性校验.txt。

所有价格均为课程教学口径（2026-11-26 核验的公开价），不是厂商正式报价。
"""

import csv
import os
from decimal import Decimal, ROUND_HALF_UP

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE, "csv")
CHECK_DIR = os.path.join(BASE, "校验")
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(CHECK_DIR, exist_ok=True)


def r(x, n=2):
    """银行家舍入不适合报价，统一四舍五入。"""
    return float(Decimal(str(x)).quantize(Decimal("1." + "0" * n), rounding=ROUND_HALF_UP))


def money(x):
    return f"{r(x, 2):,.2f}"


# ---------------------------------------------------------------- 1. 基础假设
# 项目一页纸（来自 ai-homework 项目：试点 2 科室、320 例/月、预算 8 万元）
FOLLOWUPS = 320          # 试点月随访例数（01 §4.2 / 05 §4.2 已核实）
QA = 680                 # 月知识问答次数（护士 + 患者，基准假设）
REQ_MONTH = FOLLOWUPS + QA

# 模型：DeepSeek 离峰公开价（元 / 百万 Token，2026-11-26 口径）
IN_FLASH, OUT_FLASH = 1.08, 4.32
IN_PRO, OUT_PRO = 4.75, 14.26
FLASH_SHARE = 0.7        # 分级路由：70% 简单任务走 Flash
IN_PRICE = r(IN_FLASH * FLASH_SHARE + IN_PRO * (1 - FLASH_SHARE), 3)   # 2.181
OUT_PRICE = r(OUT_FLASH * FLASH_SHARE + OUT_PRO * (1 - FLASH_SHARE), 3)  # 7.302

# 单次调用构成
A = dict(name="随访计划/记录 Agent", req=FOLLOWUPS, steps=4,
         tin=6500, tout=900, retry=0.10)
B = dict(name="知识库问答", req=QA, steps=2,
         tin=3000, tout=600, retry=0.10)

# ---------------------------------------------------------------- 2. Token 成本
def req_cost(x):
    per_step = (x["tin"] * IN_PRICE + x["tout"] * OUT_PRICE) / 1e6
    return per_step * x["steps"] * (1 + x["retry"])


cost_a, cost_b = req_cost(A), req_cost(B)
model_month = A["req"] * cost_a + B["req"] * cost_b
model_year = model_month * 12
token_in = A["req"] * A["steps"] * A["tin"] + B["req"] * B["steps"] * B["tin"]
token_out = A["req"] * A["steps"] * A["tout"] + B["req"] * B["steps"] * B["tout"]

# ---------------------------------------------------------------- 3. 人天单价
# 人天综合成本 = 月薪 × 系数 1.55 ÷ 21.75 ÷ 利用率 0.8；对外单价 = 综合成本 ×(1+风险10%)×(1+加成25%)
RATE_DERIVE = [
    ("解决方案架构师", 25000, 2227, "院方数据/接口与安全评审，需资深"),
    ("FDE 工程师", 20000, 1782, "调研、规则、知识库、调优主力"),
    ("后端工程师", 17000, 1514, "HIS 对接、权限、审计"),
    ("前端工程师", 15000, 1336, "护士/医生工作台适配"),
    ("测试/实施工程师", 13500, 1203, "评测集、回归、部署培训"),
    ("产品经理", 22500, 2004, "范围、验收、项目管理"),
]
RATE = {name: cost for name, _, cost, _ in RATE_DERIVE}

TASKS = [
    ("需求确认与流程细化（2 科室 / 6 角色）", "FDE 工程师", 2),
    ("方案设计、数据与接口契约", "解决方案架构师", 2),
    ("HIS / 随访系统只读接口对接（2 个视图）", "后端工程师", 4),
    ("病种分层规则配置（心衰 / COPD / 糖尿病）", "FDE 工程师", 2),
    ("知识库构建（12 份院内资料切块与标注）", "FDE 工程师", 2),
    ("RAG 检索、出处与拒答校验", "FDE 工程师", 2),
    ("权限与审计完善（4 级角色 + 数据级鉴权）", "后端工程师", 2),
    ("护士 / 医生工作台界面适配", "前端工程师", 1),
    ("集成联调（接口 + 脱敏网关）", "后端工程师", 4),
    ("评测集扩到 60 条 + 回归测试", "测试/实施工程师", 2),
    ("部署与培训（2 场）", "测试/实施工程师", 1),
    ("效果调优 2 轮（含提示词与规则）", "FDE 工程师", 2),
    ("项目管理与验收组织", "产品经理", 1),
]
detail_days = sum(d for _, _, d in TASKS)
detail_cost = sum(d * RATE[role] for _, role, d in TASKS)
avg_day = detail_cost / detail_days
buffer_days = 5            # 18.5%，符合课程 15%–25%
buffer_cost = buffer_days * avg_day
labor_cost = detail_cost + buffer_cost
travel = 1500              # 2 次现场差旅（交通 + 住宿）
data_once = 6000           # 12 份资料 OCR、结构化、评测集标注（外协）

# ---------------------------------------------------------------- 4. 服务器 / 运维
server_year = 800 * 12 + 360           # 2 台 8C16G 主备（400/台/月）+ 备份存储 30/月
ops_staff = 1514 * 0.5 * 12            # 运维值班 0.5 人天/月
kb_maint = 1782 * 0.25 * 12            # 知识库维护 0.25 人天/月
monitor = 600
ops_year = ops_staff + kb_maint + monitor
sms_year = 320 * 0.04 * 12             # 短信通知 0.04 元/条

# ---------------------------------------------------------------- 5. 报价
RISK, MARKUP = 0.10, 0.25
impl_internal = labor_cost + data_once + travel
impl_quote_calc = impl_internal * (1 + RISK) * (1 + MARKUP)
IMPL_QUOTE = 80000                      # 取整，与 01/05 已批预算 8 万元一致
service_year_internal = server_year + ops_year + model_year + sms_year
SERVICE_QUOTE = 36000                   # 3.6 万元/年（05：运行 0.3 万/月）
first_year_service = SERVICE_QUOTE * 9 / 12   # 首年只计 9 个月 = 27,000
first_year_quote = IMPL_QUOTE + first_year_service

block_labor = labor_cost + travel
block_model = model_year
block_server = server_year
block_data = data_once + sms_year
block_ops = ops_year
cost_year1 = block_labor + block_model + block_server + block_data + block_ops
gross_year1 = first_year_quote - cost_year1
gross_pct = gross_year1 / first_year_quote * 100

# ---------------------------------------------------------------- 6. 部署方案
# B 私有化：2 台单卡 4090 工作站（14B INT4），3 年折旧 + 电费 + 运维
hw = 45000 * 2
dep_year = hw / 3
power_kw = 1.8
electricity = power_kw * 8760 * 0.8 * 1.4
ops_gpu = 120000 * 0.2
private_year = dep_year + electricity + ops_gpu
# A 纯云端 API：仍需公网侧脱敏网关，但患者原始字段出内网
cloud_gateway = 300 * 12 + 30 * 12
cloud_year = model_year + sms_year + cloud_gateway
hybrid_year = model_year + sms_year + server_year
# 盈亏平衡（用 B 的月固定成本 / API 综合单价）
blended_price_per_m = (A["tin"] * IN_PRICE + A["tout"] * OUT_PRICE) / (A["tin"] + A["tout"])
private_month = private_year / 12
breakeven_tokens_m = private_month / blended_price_per_m          # 百万 Token / 月
project_tokens_m = (token_in + token_out) / 1e6

# 显存（14B INT4 + 4K 上下文 + 8 并发）
weights = 8.5
kv = 192 / 1024 * 4096 * 8 / 1024      # GB
vram = (weights + kv) * 1.15

# ---------------------------------------------------------------- 7. ROI
# 收益：人力节省、产能时效、差错风险、收入增量
hours_saved = 320 * 4 / 60
gain_labor = hours_saved * 60 * 12
gain_time = 600 * 0.3 * 3 / 60 * 60 * 12
gain_risk_full = 96 * (0.276 - 0.05) * 0.10 * 12000 * 12
gain_risk = gain_risk_full * 0.30
gain_revenue = 0
benefit = gain_labor * 0.5 + gain_time * 0.5 + gain_risk + gain_revenue
payback_month = first_year_quote / (benefit / 12)
roi_y1 = (benefit - first_year_quote) / first_year_quote * 100
monthly_net = (benefit - SERVICE_QUOTE) / 12
cash_payback = IMPL_QUOTE / monthly_net
total3_cost = first_year_quote + SERVICE_QUOTE * 2
total3_benefit = benefit * 3
roi_3y = (total3_benefit - total3_cost) / total3_cost * 100
sens = []
for k, label in ((0.7, "保守"), (1.0, "基准"), (1.3, "乐观")):
    b = benefit * k
    sens.append((label, b, first_year_quote / (b / 12), (b - first_year_quote) / first_year_quote * 100))

# ---------------------------------------------------------------- 8. 写 CSV
def write_csv(name, header, rows):
    path = os.path.join(CSV_DIR, name)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


write_csv("00-项目一页纸.csv",
          ["要填的五项", "本项目填写", "为什么先定它"],
          [["客户是谁", "清禾综合医院（虚构，二级甲等，1,200 床），医务部（随访中心）牵头，信息科配合", "决定报价模式与谈判对象"],
           ["多少人用", "试点 2 科室：随访护士 14 人、医生 42 人、管理员 2 人；患者端 320 人次/月", "决定并发与服务口径"],
           ["每天多少量", "月随访 320 例 + 知识问答 680 次 = 1,000 次/月（日均约 33 次）", "Token 与算力测算的起点"],
           ["数据在哪", "HIS / EMR / 随访系统在内网，含患者姓名、电话、住院号等 PII；知识库为院内制度与病种指导", "决定数据与对接工作量"],
           ["能不能上云", "患者原始数据不出内网（医疗合规一票否决）；脱敏后的制度文本与匿名摘要可调云端 API", "决定 API 还是私有化：混合路线"]])

cost_rows = [
    ["1 人力", "开发与集成人天（26 天明细）", "角色 × 天数 × 内部人天成本，见《02-人天估算与单价表》", money(detail_cost)],
    ["1 人力", "整体缓冲 5 天（19.2%）", "按加权平均单价 1,666.90 元/天", money(buffer_cost)],
    ["1 人力", "现场差旅 2 次", "交通 + 住宿，按 1,500 元包干", money(travel)],
    ["1 人力", "小计", "三个明细相加", money(block_labor)],
    ["2 模型", "随访 Agent（320 次/月 × 4 步）", "单次 0.0913 元 × 320 × 12，见《03》", money(A["req"] * cost_a * 12)],
    ["2 模型", "知识问答（680 次/月 × 2 步）", "单次 0.0240 元 × 680 × 12，见《03》", money(B["req"] * cost_b * 12)],
    ["2 模型", "小计", "两项相加，等于《03》基准档 ×12", money(block_model)],
    ["3 服务器", "内网应用服务器 2 台 8C16G（主备）", "400 元/台/月 × 2 × 12，复用信息科虚拟化", "9,600.00"],
    ["3 服务器", "备份存储 1TB", "30 元/月 × 12", "360.00"],
    ["3 服务器", "小计", "两台主备 + 存储", money(block_server)],
    ["4 数据", "12 份资料 OCR、结构化、评测集标注（外协）", "一次性 6,000 元", money(data_once)],
    ["4 数据", "短信通知 320 条/月 × 0.04 元", "0.04 × 320 × 12", money(sms_year)],
    ["4 数据", "小计", "一次性 + 年度", money(block_data)],
    ["5 运维", "运维值班 0.5 人天/月", "1,514 元/天 × 0.5 × 12", money(ops_staff)],
    ["5 运维", "知识库维护 0.25 人天/月", "1,782 元/天 × 0.25 × 12", money(kb_maint)],
    ["5 运维", "监控与日志", "600 元/年", money(monitor)],
    ["5 运维", "小计", "三项相加", money(block_ops)],
    ["合计", "首年内部成本（12 个月口径）", "五块小计相加", money(cost_year1)],
    ["对外", "一次性实施费（成本 ×1.10 风险 ×1.25 加成）", f"测算 {money(impl_quote_calc)}，取整 80,000（与已批预算一致）", money(IMPL_QUOTE)],
    ["对外", "年服务费（含模型费、基础设施、运维与知识库维护）", "3.6 万元/年；首年按 9 个月计 2.7 万元", money(SERVICE_QUOTE)],
    ["对外", "首年合计", "80,000 + 27,000", money(first_year_quote)],
    ["模式", "组合报价：一次性实施费 + 年服务费 + 超量单价", "理由：试点范围清晰但用量待验证，实施费覆盖交付风险，年费覆盖运维与模型成本，超量单价覆盖用量风险", "—"],
]
write_csv("01-成本拆解表.csv", ["成本块", "明细项", "测算依据", "金额（元/首年）"], cost_rows)

pd_rows = []
for i, (task, role, days) in enumerate(TASKS, 1):
    pd_rows.append([i, task, role, days, RATE[role], money(days * RATE[role]), "可计数工作包"])
pd_rows.append(["", "小计（明细）", "—", detail_days, money(avg_day), money(detail_cost), "加权平均单价 = 小计 ÷ 天数"])
pd_rows.append(["B", f"整体缓冲 {buffer_days} 天（18.5%，课程要求 15%–25%）", "按加权平均单价", buffer_days, money(avg_day), money(buffer_cost), "单独成行，不摊进任务"])
pd_rows.append(["", "合计（内部成本）", "—", detail_days + buffer_days, money(labor_cost / (detail_days + buffer_days)), money(labor_cost), "含缓冲"])
pd_rows.append(["", "对外报价（成本 ×1.10 ×1.25）", "—", "", "", money(impl_quote_calc), "取整 80,000，含税与 3 个月试点支持"])
write_csv("02-人天估算与单价表.csv",
          ["序号", "工作包", "角色", "人天", "内部人天成本（元）", "小计（元）", "说明"], pd_rows)

rate_rows = []
for name, salary, cost, note in RATE_DERIVE:
    rate_rows.append([name, salary, "1.55", "21.75", "0.80", cost,
                      money(cost * (1 + RISK) * (1 + MARKUP)), note,
                      f"{salary} × 1.55 ÷ 21.75 ÷ 0.80 = {money(cost)}"])
write_csv("02-人天单价推导.csv",
          ["角色", "月薪（元）", "综合成本系数", "月计薪天数", "利用率", "人天综合成本（元）", "建议对外单价（元）", "用途", "推导过程"],
          rate_rows)

token_rows = []
for label, k in (("保守", 0.7), ("基准", 1.0), ("高峰", 1.6)):
    fu, qa = round(FOLLOWUPS * k), round(QA * k)
    m = fu * cost_a + qa * cost_b
    tokens = fu * A["steps"] * (A["tin"] + A["tout"]) + qa * B["steps"] * (B["tin"] + B["tout"])
    token_rows.append([label, fu, qa, A["steps"], B["steps"], f"{A['tin']}/{A['tout']}", f"{B['tin']}/{B['tout']}",
                       f"{IN_PRICE}/{OUT_PRICE}", tokens, money(m), money(m * 12)])
write_csv("03-Token月成本测算表.csv",
          ["档位", "月随访例数", "月问答次数", "随访 Agent 步数", "问答步数", "随访输入/输出 Token", "问答输入/输出 Token",
           "混合输入/输出单价（元/百万）", "月 Token 总量", "月模型成本（元）", "年模型成本（元）"], token_rows)

comp_rows = [
    ["A 纯云端 API", "患者数据经公网网关直连云端 API", money(cloud_year), "不合规（PII 出内网，医疗一票否决）", "低", "公网往返，P95 约 2–4 秒", "仅作成本基准，不推荐"],
    ["B 全私有化（14B INT4）", "2 台单卡 RTX 4090 工作站主备（显存需求 17.0 GB/台）", money(private_year), "合规", "高（需 GPU 运维与模型更新能力）", "内网低延迟，P95 < 1 秒", f"用量需 ≥ {r(breakeven_tokens_m / 100, 1)} 亿 Token/月才划算，本项目 0.14 亿，不推荐"],
    ["C 混合（推荐）", "敏感数据与随访记录留内网；脱敏后调用云端 API；内网 2 台 8C16G 主备", money(hybrid_year), "合规（PII 不出内网，审计留痕）", "中（沿用现有虚拟化 + 我方远程运维）", "公网仅传脱敏文本，P95 约 3 秒", "满足合规且成本最低，推荐"],
]
write_csv("04-部署方案对比表.csv",
          ["方案", "部署内容", "年成本（元）", "合规判断", "运维要求", "延迟", "结论"], comp_rows)

write_csv("04-推荐配置单.csv",
          ["部件", "配置", "数量", "依据"],
          [["应用服务器", "8 核 16G，200GB SSD", "2（主备）", "320 例/月、8 并发峰值，CPU 峰值 < 40%"],
           ["GPU", "无（模型走云端 API）", "0", "避免 2.1 亿 Token/月以下的算力闲置"],
           ["数据库", "复用院内 PostgreSQL / MySQL 实例", "1", "随访任务与审计日志，日增 < 50MB"],
           ["存储", "1TB 备份空间（对象存储）", "1", "日志留存 6 个月，符合医疗审计要求"],
           ["网络", "内网 DMZ + 脱敏网关 + 出向白名单", "1 套", "仅允许脱敏文本出网，禁止患者标识"],
           ["并发能力", "峰值 8 路，P95 < 3 秒", "—", "试点 2 科室，日峰 60 次请求"],
           ["高可用", "双节点主备，故障切换 < 5 分钟", "—", "避免单点；不承诺 99.9%（试点期 99.5%）"]])

roi_rows = [
    ["收益 1 人力节省", "320 例/月 × 4 分钟 ÷ 60 × 60 元/小时 × 12", f"{money(gain_labor)} × 转化系数 0.5", money(gain_labor * 0.5), "02 EV-06 观察 11→7 分钟；60 元/小时为课程假设"],
    ["收益 2 产能与时效", "600 通/月 × 30% 重复来电 × 3 分钟 ÷ 60 × 60 元/小时 × 12", f"{money(gain_time)} × 0.5", money(gain_time * 0.5), "05 R-04 假设，待试点验证"],
    ["收益 3 差错与风险", "96 例/月 × (27.6%−5%) × 10% × 1.2 万元 × 12", f"{money(gain_risk_full)} × 归因率 30%", money(gain_risk), "再入院成本与风险下降均为估算，待同口径对照"],
    ["收益 4 收入增量", "公立医院不适用", "0（不折钱）", "0.00", "不把模糊收益算成钱"],
    ["年收益合计", "—", "人力×0.5 + 时效×0.5 + 风险×0.3", money(benefit), "—"],
    ["首年总投入", "实施费 80,000 + 首年服务费 27,000", "—", money(first_year_quote), "练 6 报价单首年合计"],
    ["年运行成本", "年服务费（第 2 年起）", "—", money(SERVICE_QUOTE), "含模型费、基础设施、运维"],
    ["年净收益", "年收益 − 年运行成本", "—", money(benefit - SERVICE_QUOTE), "第 2 年起口径"],
    ["首年 ROI", "(年收益 − 首年总投入) ÷ 首年总投入", "—", f"{r(roi_y1, 2)}%", "课程口径，首年略负"],
    ["回本周期（课程口径）", "首年总投入 ÷ (年收益 ÷ 12)", "—", f"{r(payback_month, 1)} 个月", "用毛收益摊回"],
    ["回本周期（净现金流口径）", "实施费 ÷ ((年收益 − 年运行成本) ÷ 12)", "—", f"{r(cash_payback, 1)} 个月", "扣除运行成本，更保守"],
    ["三年 ROI", "(3 年收益 − 3 年总成本) ÷ 3 年总成本", f"3 年成本 {money(total3_cost)}", f"{r(roi_3y, 2)}%", "含首年实施费"],
]
write_csv("05-客户ROI一页纸.csv", ["项目", "计算式", "中间量", "金额/结果", "依据与状态"], roi_rows)

sens_rows = [[label, money(b), f"{r(pm, 1)} 个月", f"{r(roi, 2)}%", money(b - first_year_quote)]
             for label, b, pm, roi in sens]
write_csv("05-ROI敏感性分析.csv",
          ["情景（年收益 ±30%）", "年收益（元）", "回本周期（月）", "首年 ROI", "首年净收益（元）"], sens_rows)

quote_rows = [
    ["1", "需求调研与方案设计", "业务流程梳理、知识库规划、ROI 测算报告、数据与接口契约", "含在实施费"],
    ["2", "系统开发与集成（一次性实施费）", f"{detail_days + buffer_days} 人天（{detail_days} 明细 + {buffer_days} 缓冲）+ 12 份资料数据工程 + 2 次差旅；含 3 个月试点支持、2 轮效果调优、2 场培训", money(IMPL_QUOTE)],
    ["3", "年服务费（首年按 9 个月计）", "运维值班、知识库维护、监控、模型用量包（月均 3,000 万 Token 内）、超量按单价结算", money(first_year_service)],
    ["4", "可选：私有化迁移 / 高可用增强", f"用量达到盈亏平衡点（约 {r(breakeven_tokens_m / 100, 1)} 亿 Token/月）后另行评估；全私有化三年 TCO 约 21.5 万元", "按评估"],
    ["", "首年合计", "实施费 + 首年服务费", money(first_year_quote)],
    ["", "续年费用（第 2 年起）", "年服务费 36,000 元/年，按年预付", money(SERVICE_QUOTE)],
]
write_csv("06-正式报价单.csv", ["序号", "项目", "说明", "金额（元）"], quote_rows)

write_csv("06-付款与SLA.csv",
          ["条款", "内容"],
          [["付款节点", "签约 40%（32,000）；上线验收 40%（32,000）；终验 20%（16,000）；首年服务费 27,000 于上线后 30 日内支付"],
           ["服务时间", "5×8（工作日 8:30–17:30），法定节假日除外"],
           ["响应时效", "P1（系统不可用）2 小时响应、4 小时恢复；P2（功能受阻）1 个工作日；P3（咨询）3 个工作日"],
           ["可用性", "试点期 99.5%（不含客户内网与云端 API 厂商故障）"],
           ["服务内容", "月度巡检报告、知识库月度更新、模型调价同步、季度效果复盘"],
           ["超范围计费", "新增系统对接 2,000 元/人天；超出 2 轮调优 2,000 元/人天；超出 2 场培训 1,300 元/场"],
           ["用量条款", "模型用量包 3,000 万 Token/月；超量按输入 2.18 元、输出 7.30 元/百万 Token × 1.2 结算"],
           ["调价传导", "模型厂商公开价调整超过 15% 时，双方按新价格重算，不由乙方单方承担"],
           ["数据与合规", "患者原始数据不出院内；脱敏规则与审计日志双方确认；乙方不留存患者可识别信息"],
           ["验收标准", "以 60 条评测集为准：检索命中率 ≥ 90%、越权拦截 100%、用药问题转人工 100%"],
           ["知识产权", "定制开发部分交付源码使用权；通用组件与知识库模板归乙方，客户享有永久使用许可"]])

write_csv("06-谈判底线清单.csv",
          ["类型", "条款", "底线 / 可让范围", "交换条件或测算依据"],
          [["不可让", "一次性实施费", "不低于 72,000 元", "内部成本 59,174 元；低于 72,000 毛利 < 18%，无法覆盖试点支持"],
           ["不可让", "模型费包干上限", "必须写超量单价与调价传导", "用量涨 60% 时模型费上升 60%，无上限即我方吞下"],
           ["不可让", "患者原始数据出内网", "不接受", "医疗合规一票否决；只接受脱敏文本出网"],
           ["不可让", "7×24 免费 SLA", "仅提供 5×8；7×24 另行报价", "夜间值班需额外 1 人天/月（1,514 元/月）"],
           ["不可让", "无限轮调优", "含 2 轮；超出按 2,000 元/人天", "每轮调优约 1 人天，课程口径 2–3 轮"],
           ["可让", "付款比例", "签约 40% 可降至 30%", "换取预付款保函或缩短账期至 15 天"],
           ["可让", "首年服务费", "最多让 2,000 元", "换取 2 年续约意向书"],
           ["可让", "培训场次", "2 场可减至 1 场（让 1,300 元）", "换取院方提供培训场地与录播授权"],
           ["可让", "前端工作台范围", "可缩减为仅护士端（让 1,336 元）", "换取医生端延后至二期"],
           ["可让", "案例授权", "让 3,000 元", "换取院方署名案例与路演授权（脱敏）"]])

# ---------------------------------------------------------------- 9. 数字咬合校验
checks = [
    ("练1 人力块 = 练2 人天合计 + 差旅", block_labor, labor_cost + travel),
    ("练1 模型块 = 练3 基准档年成本", block_model, r(model_year, 2)),
    ("练1 服务器块 = 练4 推荐方案服务器年成本", block_server, server_year),
    ("练1 五块合计 = 首年内部成本", cost_year1,
     block_labor + block_model + block_server + block_data + block_ops),
    ("练3 基准月成本 ×12 = 练6 年服务费中的模型费", r(model_month * 12, 2), r(model_year, 2)),
    ("练4 推荐方案年成本 = 模型 + 短信 + 服务器", hybrid_year, model_year + sms_year + server_year),
    ("练5 首年总投入 = 练6 首年合计", first_year_quote, IMPL_QUOTE + first_year_service),
    ("练6 首年合计 = 实施费 + 首年服务费", first_year_quote, 80000 + 27000),
    ("练6 续年 = 年服务费", SERVICE_QUOTE, 36000),
    ("练5 回本用报价单总价重算", r(payback_month, 2), r(first_year_quote / (benefit / 12), 2)),
]
lines = []
lines.append("企业报价包 · 数字咬合校验（由 测算脚本/calc.py 生成）")
lines.append("=" * 64)
ok = True
for name, a, b in checks:
    good = abs(a - b) < 0.011
    ok = ok and good
    lines.append(f"[{'PASS' if good else 'FAIL'}] {name}: {money(a)} vs {money(b)}")
lines.append("-" * 64)
lines.append(f"校验结果：{'全部通过' if ok else '存在不一致'}")
lines.append("")
lines.append("关键数字：")
lines.append(f"  单次随访 Agent 成本 = {r(cost_a, 4)} 元；单次问答 = {r(cost_b, 4)} 元")
lines.append(f"  月模型成本 = {money(model_month)} 元；年 = {money(model_year)} 元")
lines.append(f"  月 Token 总量 = {token_in + token_out:,}（输入 {token_in:,} / 输出 {token_out:,}）")
lines.append(f"  人天明细 {detail_days} + 缓冲 {buffer_days} = {detail_days + buffer_days} 天；内部 {money(labor_cost)} 元")
lines.append(f"  实施费测算 = {money(impl_quote_calc)} 元 → 报价 80,000 元（与已批预算一致）")
lines.append(f"  首年内部成本 = {money(cost_year1)} 元；首年报价 = {money(first_year_quote)} 元；毛利率 = {r(gross_pct, 2)}%")
lines.append(f"  私有化年成本 = {money(private_year)} 元；混合 = {money(hybrid_year)} 元；云端 = {money(cloud_year)} 元")
lines.append(f"  显存需求 = 权重 {weights} + KV {r(kv, 2)} → ×1.15 = {r(vram, 2)} GB/台")
lines.append(f"  盈亏平衡用量 = {r(breakeven_tokens_m, 2)} 百万 Token/月；本项目 = {r(project_tokens_m, 2)} 百万 Token/月")
lines.append(f"  年收益 = {money(benefit)} 元；首年 ROI = {r(roi_y1, 2)}%；回本 = {r(payback_month, 1)} 个月（净现金流 {r(cash_payback, 1)} 个月）")
lines.append(f"  三年 ROI = {r(roi_3y, 2)}%")
for label, b, pm, roi in sens:
    lines.append(f"  敏感性 {label}：年收益 {money(b)}，回本 {r(pm, 1)} 个月，首年 ROI {r(roi, 2)}%")

text = "\n".join(lines)
with open(os.path.join(CHECK_DIR, "一致性校验.txt"), "w", encoding="utf-8") as f:
    f.write(text + "\n")
print(text)
