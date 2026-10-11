#!/usr/bin/env bash
#
# 生成当前的订阅地址（带绕缓存参数）。
#
# 为什么需要绕缓存
# ----------------
# 仓库更新后，中间层可能仍在返回旧内容：
#   - raw.githubusercontent.com  CDN 缓存约 5 分钟
#   - cdn.jsdelivr.net 的 @main   缓存最长约 12 小时（实测踩过：源从 30 个扩到 54 个，
#     raw 已经是 54 条，jsDelivr 仍返回 30 条）
#   - App 自身的 NetworkCacheManager 是内存缓存，重启可清
#
# 在地址后加 ?v=<commit> 即可绕过全部缓存。App 解析源文件用的是
# `地址.substring(0, 地址.lastIndexOf("/") + 1) + fileName`，
# 最后一个 "/" 在 index.json 之前，所以查询参数会被自然丢弃，不影响任何源。
#
# 用法：
#   bash tools/subscribe_url.sh              # 输出 raw 地址（推荐）
#   bash tools/subscribe_url.sh --jsdelivr   # 输出 jsDelivr 地址
#   bash tools/subscribe_url.sh --plain      # 不带缓存戳

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GH_USER="bolangLEE12138"
GH_REPO="Manga_Subscribe"
BRANCH="main"

PLAIN=0
USE_JSDELIVR=0
for arg in "$@"; do
    case "$arg" in
        --plain)     PLAIN=1 ;;
        --jsdelivr)  USE_JSDELIVR=1 ;;
        -h|--help)   sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "未知参数: $arg（可用: --plain --jsdelivr）" >&2; exit 1 ;;
    esac
done

if [ "$USE_JSDELIVR" = "1" ]; then
    BASE="https://cdn.jsdelivr.net/gh/$GH_USER/$GH_REPO@$BRANCH"
else
    BASE="https://raw.githubusercontent.com/$GH_USER/$GH_REPO/$BRANCH"
fi

SUFFIX=""
if [ "$PLAIN" = "0" ]; then
    if STAMP="$(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null)"; then
        if [ -n "$(git -C "$REPO_DIR" status --porcelain 2>/dev/null)" ]; then
            STAMP="${STAMP}-dirty"
        fi
        SUFFIX="?v=$STAMP"
    else
        SUFFIX="?v=$(date +%s)"
    fi
fi

echo "$BASE/index.json$SUFFIX"

if [ "$PLAIN" = "0" ]; then
    echo "" >&2
    echo "提示：这是带缓存戳的地址（?v= 后为当前 commit 短哈希）。" >&2
    echo "      仓库每次更新后重跑本脚本即可拿到新地址。" >&2
    if [ "$USE_JSDELIVR" = "1" ]; then
        echo "      若仍需立即生效，可额外执行：" >&2
        echo "        curl \"https://purge.jsdelivr.net/gh/$GH_USER/$GH_REPO@$BRANCH/index.json\"" >&2
    fi
fi
