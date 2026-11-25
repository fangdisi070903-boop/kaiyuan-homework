# 第四周作业：开源软件许可证合规分析

对应课程仓库《卓越班每周作业汇总》第四周（2026-10-08）与《第二章平时作业：开源软件许可证分析》作业 1。

## 一、作业要求

1. 选取 Apache 或任意开源社区中的一个开源项目；
2. 选取“开源软件许可合规检测工具”进行扫描；
3. 报告包含：项目介绍、工具安装过程及问题、工具输出报告、针对输出的详细分析；
4. 报告内容不超过 5 页；
5. 命名：学号-姓名-开源合规与许可证。

## 二、交付物

| 文件 | 说明 |
| --- | --- |
| `f25011202-方帝斯-开源合规与许可证.docx` | 作业报告（Word，按模板格式） |
| `f25011202-方帝斯-开源合规与许可证.pdf` | 同一报告的 PDF 版本，便于直接查看 |
| `report/报告源文.md` | 报告正文的 Markdown 源文，便于核对修改 |
| `scan/environment.txt` | 扫描环境与工具版本（真实执行） |
| `scan/terminal_session.txt` | 关键命令与输出节选（真实执行） |
| `scan/licensee-osi-production.txt` | licensee 生产依赖扫描完整文本输出 |
| `scan/licensee-osi-production.ndjson` | licensee 生产依赖扫描机器可读输出 |
| `scan/licensee-osi-all.ndjson` | licensee 全量依赖（含 dev）扫描输出 |
| `scan/license-checker-production.json` | license-checker 生产依赖扫描 JSON |
| `scan/license-checker-production.csv` | license-checker 生产依赖扫描 CSV |
| `scan/tool_install_notes.md` | 工具选型、安装问题与局限性说明 |
| `scan/commands.sh` | 一键复现脚本 |
| `scan/pm2-commit.txt` | 被扫描项目的仓库、版本、commit 信息 |

## 三、扫描对象与工具

- 项目：PM2 7.1.2（Node.js 进程管理器），许可证 AGPL-3.0
- 仓库：<https://github.com/Unitech/pm2>
- commit：`7a7fb4e22e9a26ec79c870ce8daafd2f78b648d1`
- 主工具：`licensee` 12.0.2（课程资料第 18 项 Licensee.js）
- 交叉验证：`license-checker` 25.0.1
- 规则：`--osi`（仅批准 OSI 认证许可证）

## 四、核心结论

| 指标 | 结果 |
| --- | --- |
| 生产依赖（第三方包） | 44 个 |
| OSI 规则批准 | 41 个（93.2%） |
| 未批准 | 3 个（6.8%） |
| 许可证分布 | MIT 35、ISC 5、Apache* 1、Python-2.0 1、MIT* 1、Public Domain/MIT 1 |
| 未批准原因 | 均为元数据不规范（非法 SPDX、缺少 license 字段、数组格式），人工复核后实际均为宽松许可 |
| 真实合规重点 | PM2 自身的 AGPL-3.0 在分发与网络服务场景下的义务 |

## 五、复现方式

```bash
bash scan/commands.sh
```

或在已有 Node.js 环境下手动执行：

```bash
npm install -g licensee@12.0.2 license-checker@25.0.1
cd /path/to/pm2
npm install --ignore-scripts
licensee --osi --production
license-checker --production --json
```

## 六、真实性声明

- 所有扫描结果均来自本机真实执行，原始输出未经修改；
- 报告未声称做过源码级、二进制级或容器镜像级扫描；
- 未在报告中虚构 CVE、法律意见或平台截图；
- 报告中的许可证判断依据为 SPDX 标识、依赖 `package.json` 与包内 `LICENSE` 文件，属于技术合规分析，不构成法律意见。

---

完成日期：2026-11-25
