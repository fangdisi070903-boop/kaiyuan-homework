# 工具选型、安装过程与遇到的问题

## 一、环境

| 项目 | 值 |
| --- | --- |
| 操作系统 | macOS 26.6.2（arm64） |
| 系统 Python | 3.9.6（仅用于辅助脚本） |
| Node.js | v20.18.1 |
| npm | 10.8.2 |
| npm registry | https://registry.npmmirror.com |

## 二、工具选型过程

### 2.1 首选 ScanCode Toolkit（未成功）

ScanCode Toolkit 是课程参考资料中列出的工具（第 27 项），功能最全面，因此首先尝试安装：

```bash
python3 -m venv /tmp/sc-venv
/tmp/sc-venv/bin/pip install "scancode-toolkit==31.2.6"
```

安装依赖 `pyicu` 时编译失败，原始报错：

```text
RuntimeError:
Please install pkg-config on your system or set the ICU_VERSION environment
variable to the version of ICU you have installed.
ERROR: Failed to build 'pyicu' when getting requirements to build wheel
```

原因分析：PyICU 在 PyPI 上只提供源码包，没有 macOS arm64 的预编译 wheel；编译需要 ICU 开发头文件与 `pkg-config`，而本机未安装 Homebrew，macOS 也不自带 ICU 开发头文件，因此放弃该方案。

### 2.2 改用 Licensee.js（成功）

课程参考资料第 18 项为 **Licensee.js**：按 SPDX 许可证表达式与白名单检查 npm 依赖的许可证元数据，正好适配 Node.js 生态。实际安装的 npm 包名为 `licensee`：

```bash
npm install -g licensee@12.0.2
```

同时安装 `license-checker@25.0.1` 作为交叉验证工具，用于统计许可证分布，避免单一工具的元数据误判。

## 三、安装与运行中遇到的问题

| 序号 | 问题 | 现象 | 处理方式 |
| --- | --- | --- | --- |
| 1 | 系统没有 Node.js / npm | `zsh: command not found: node` | 从 npmmirror 下载 Node v20.18.1 darwin-arm64 二进制包并加入 PATH |
| 2 | GitHub 直连克隆失败 | `fatal: unable to access 'https://github.com/Unitech/pm2.git/': Error in the HTTP2 framing layer` | 改用 `codeload.github.com` 下载源码 tar.gz |
| 3 | licensee 首次运行报错 | `Cannot read /private/tmp/pm2/.licensee.json` | 不生成配置文件，直接使用 `--osi` 规则参数 |
| 4 | 依赖安装脚本风险 | 第三方包可能执行 postinstall | 使用 `npm install --ignore-scripts` |
| 5 | licensee 退出码为 1 | 存在未批准包时返回非零 | 属于预期行为，用 `|| true` 保留输出，不影响报告结论 |
| 6 | 许可证元数据不规范 | `Apache-2` 不是合法 SPDX；`cli-tableau` 缺少 license 字段；`tv4` 的 license 是数组 | 工具判为 NOT APPROVED，再人工查看包内 `package.json` 与 `LICENSE` 文件复核 |
| 7 | BlueOak-1.0.0 被判定未批准 | `jackspeak`、`minipass` 等开发依赖使用 BlueOak-1.0.0 | 该许可证未通过 OSI 认证，但属于宽松许可；仅存在于开发依赖树，生产依赖不受影响 |

## 四、最终使用的命令

```bash
# 生产依赖（不含 devDependencies）
licensee --osi --production
licensee --osi --production --ndjson
license-checker --production --json
license-checker --production --csv

# 全量依赖（含 devDependencies，用于对照）
licensee --osi --ndjson
```

原始输出见本目录下的 `.txt`、`.ndjson`、`.json`、`.csv` 文件。

## 五、局限性说明

1. `licensee` 与 `license-checker` 均属于**依赖元数据扫描**，读取的是 `package.json` 中的 `license` 字段，不解析源码文件头，也不做二进制成分分析。
2. 元数据错误会直接导致误报或漏报，因此本报告对 3 个未批准项逐一做了人工复核。
3. 扫描范围为 PM2 的生产依赖树（44 个第三方包），未对 PM2 自身源码做逐文件许可证头检查。
4. 未进行漏洞（CVE）扫描，本报告只讨论许可证合规，不涉及安全性结论。
