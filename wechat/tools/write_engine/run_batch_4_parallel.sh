#!/bin/bash
# 并发跑 4 篇文章：每篇独立进程，deep_research → engine
cd "$(dirname "$0")"
export PATH="/usr/local/bin:/opt/homebrew/bin:/Users/ciwang/.npm-global/bin:$PATH"

PROJECT_ROOT="$(cd ../../.. && pwd)"
TOPIC_BASE="$PROJECT_ROOT/wechat/公众号选题"
PROGRESS="/tmp/batch_4_progress.txt"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$PROGRESS"
}

echo "=== 并发批量写稿 $(date) ===" > "$PROGRESS"
echo "4 篇同时启动" >> "$PROGRESS"

# ── Worker 函数 ──
run_article() {
    local ID="$1"
    local TOPIC_DIR="$2"
    local PERSONA="$3"
    local SERIES="$4"
    local LABEL="$5"
    local LOG="/tmp/batch_4_${ID}.log"

    log "▶ [$ID] $LABEL — 深度调研启动"

    # Step 1: 深度调研
    python3 deep_research.py \
        --topic-dir "$TOPIC_DIR" \
        --model sonnet >> "$LOG" 2>&1

    if [ $? -ne 0 ]; then
        log "❌ [$ID] $LABEL — 调研失败"
        return 1
    fi
    log "✅ [$ID] $LABEL — 调研完成"

    # Step 2: 写作引擎
    log "▶ [$ID] $LABEL — 写作引擎启动"

    local ENGINE_CMD="python3 engine.py --topic-dir \"$TOPIC_DIR\" --persona $PERSONA --model sonnet"
    if [ -n "$SERIES" ]; then
        ENGINE_CMD="$ENGINE_CMD --series $SERIES"
    fi

    eval $ENGINE_CMD >> "$LOG" 2>&1

    if [ $? -ne 0 ]; then
        log "❌ [$ID] $LABEL — 写作失败"
        return 1
    fi
    log "✅ [$ID] $LABEL — 写作完成"
}

# ── 并发启动 4 篇 ──

run_article "A" \
    "$TOPIC_BASE/2026-03-01|Anthropic-Skill转向" \
    "丁仪" "技术祛魅" "Anthropic-Skill转向" &
PID_A=$!

run_article "B" \
    "$TOPIC_BASE/2026-03-01|中国AI-Token超美" \
    "智子" "涟漪" "中国AI-Token超美" &
PID_B=$!

run_article "C" \
    "$TOPIC_BASE/2026-03-01|OpenClaw算力涟漪" \
    "智子" "涟漪" "OpenClaw算力涟漪" &
PID_C=$!

run_article "D" \
    "$TOPIC_BASE/2026-03-01|Agent创业壁垒" \
    "罗辑" "" "Agent创业壁垒" &
PID_D=$!

log "所有任务已启动: A=$PID_A B=$PID_B C=$PID_C D=$PID_D"

# ── 等待全部完成 ──
wait $PID_A $PID_B $PID_C $PID_D

log "=== 全部完成 $(date) ==="

# ── 汇总 ──
echo "" >> "$PROGRESS"
echo "=== 产出汇总 ===" >> "$PROGRESS"
for d in "$TOPIC_BASE/2026-03-01|Anthropic-Skill转向" \
         "$TOPIC_BASE/2026-03-01|中国AI-Token超美" \
         "$TOPIC_BASE/2026-03-01|OpenClaw算力涟漪" \
         "$TOPIC_BASE/2026-03-01|Agent创业壁垒"; do
    name=$(basename "$d")
    if [ -f "$d/article.md" ]; then
        size=$(wc -c < "$d/article.md" | tr -d ' ')
        echo "✅ $name — article.md (${size}b)" >> "$PROGRESS"
    else
        echo "❌ $name — 无 article.md" >> "$PROGRESS"
    fi
done
