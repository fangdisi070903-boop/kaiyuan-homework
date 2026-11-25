#!/usr/bin/env bash
#
# 第四周作业复现脚本（macOS arm64 实测）
#
# 前置条件：可访问 npmmirror（或自行替换为官方 npm registry）。
# 说明：本脚本只负责复现依赖扫描，不修改 PM2 源码。

set -euo pipefail

WORKDIR="${1:-/tmp/pm2-license-scan}"
NODE_VERSION="v20.18.1"
NODE_DIR="/tmp/node-${NODE_VERSION}-darwin-arm64"

mkdir -p "${WORKDIR}"
cd "${WORKDIR}"

# 1. Node.js（若系统未安装）
if ! command -v node >/dev/null 2>&1; then
  if [ ! -x "${NODE_DIR}/bin/node" ]; then
    curl -sSL "https://npmmirror.com/mirrors/node/${NODE_VERSION}/node-${NODE_VERSION}-darwin-arm64.tar.xz" -o node.tar.xz
    tar -xf node.tar.xz -C /tmp
    rm -f node.tar.xz
  fi
  export PATH="${NODE_DIR}/bin:${PATH}"
fi

node --version
npm --version

# 2. 安装许可证合规工具
npm config set registry https://registry.npmmirror.com
npm install -g licensee@12.0.2 license-checker@25.0.1

# 3. 获取 PM2 源码（GitHub 直连失败时使用 codeload）
if [ ! -d pm2 ]; then
  curl -sSL https://codeload.github.com/Unitech/pm2/tar.gz/refs/heads/master -o pm2.tar.gz
  tar -xzf pm2.tar.gz
  mv pm2-master pm2
fi

cd pm2
# 4. 安装依赖（跳过安装脚本，避免执行第三方 postinstall）
npm install --ignore-scripts --no-audit --no-fund

# 5. 执行扫描并保存原始输出
licensee --osi --production > licensee-osi-production.txt || true
licensee --osi --production --ndjson > licensee-osi-production.ndjson || true
licensee --osi --ndjson > licensee-osi-all.ndjson || true
license-checker --production --json > license-checker-production.json
license-checker --production --csv > license-checker-production.csv

echo "扫描完成，输出位于 ${WORKDIR}/pm2"
