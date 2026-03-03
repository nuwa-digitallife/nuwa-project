#!/bin/bash
# 2并发续跑：Phase1 B+D(从Pass2), Phase2 A+C(全跑)
cd "$(dirname "$0")"
export PATH="/usr/local/bin:/opt/homebrew/bin:/Users/ciwang/.npm-global/bin:$PATH"
unset CLAUDECODE  # 允许嵌套调用 claude -p

PROJECT_ROOT="$(cd ../../.. && pwd)"
TOPIC_BASE="$PROJECT_ROOT/wechat/公众号选题"
PROGRESS="/tmp/batch_4_progress.txt"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$PROGRESS"
}

echo "" >> "$PROGRESS"
echo "=== v2 续跑 (2并发) $(date) ===" >> "$PROGRESS"

# ── Phase 1: B + D 从 Pass 2 续跑 ──
log "Phase 1: B + D (从 Pass 2 续跑)"

(
    log "▶ [B] 中国AI-Token超美 — 写作引擎 Pass 2 续跑"
    python3 engine.py \
        --topic-dir "$TOPIC_BASE/2026-03-01|中国AI-Token超美" \
        --persona 智子 --series 涟漪 --model sonnet --pass 2 \
        >> /tmp/batch_4_B.log 2>&1 \
    && log "✅ [B] 中国AI-Token超美 — 写作完成" \
    || log "❌ [B] 中国AI-Token超美 — 写作失败"
) &
PID_B=$!

(
    log "▶ [D] Agent创业壁垒 — 写作引擎 Pass 2 续跑"
    python3 engine.py \
        --topic-dir "$TOPIC_BASE/2026-03-01|Agent创业壁垒" \
        --persona 罗辑 --model sonnet --pass 2 \
        >> /tmp/batch_4_D.log 2>&1 \
    && log "✅ [D] Agent创业壁垒 — 写作完成" \
    || log "❌ [D] Agent创业壁垒 — 写作失败"
) &
PID_D=$!

log "Phase 1 启动: B=$PID_B D=$PID_D"
wait $PID_B $PID_D
log "Phase 1 完成"

# ── Phase 2: A + C 全跑 ──
log "Phase 2: A + C (全跑)"

(
    # A 已有 deep_research，直接 engine
    log "▶ [A] Anthropic-Skill转向 — 写作引擎启动"
    python3 engine.py \
        --topic-dir "$TOPIC_BASE/2026-03-01|Anthropic-Skill转向" \
        --persona 丁仪 --series 技术祛魅 --model sonnet \
        >> /tmp/batch_4_A.log 2>&1 \
    && log "✅ [A] Anthropic-Skill转向 — 写作完成" \
    || log "❌ [A] Anthropic-Skill转向 — 写作失败"
) &
PID_A=$!

(
    # C 需要重跑 research + engine
    log "▶ [C] OpenClaw算力涟漪 — 深度调研启动"
    python3 deep_research.py \
        --topic-dir "$TOPIC_BASE/2026-03-01|OpenClaw算力涟漪" \
        --model sonnet >> /tmp/batch_4_C.log 2>&1
    if [ $? -ne 0 ]; then
        log "❌ [C] OpenClaw算力涟漪 — 调研失败"
    else
        log "✅ [C] OpenClaw算力涟漪 — 调研完成"
        log "▶ [C] OpenClaw算力涟漪 — 写作引擎启动"
        python3 engine.py \
            --topic-dir "$TOPIC_BASE/2026-03-01|OpenClaw算力涟漪" \
            --persona 智子 --series 涟漪 --model sonnet \
            >> /tmp/batch_4_C.log 2>&1 \
        && log "✅ [C] OpenClaw算力涟漪 — 写作完成" \
        || log "❌ [C] OpenClaw算力涟漪 — 写作失败"
    fi
) &
PID_C=$!

log "Phase 2 启动: A=$PID_A C=$PID_C"
wait $PID_A $PID_C
log "Phase 2 完成"

log "=== v2 全部完成 $(date) ==="

# ── 汇总 ──
echo "" >> "$PROGRESS"
echo "=== 产出汇总 ===" >> "$PROGRESS"
for d in "Anthropic-Skill转向" "中国AI-Token超美" "OpenClaw算力涟漪" "Agent创业壁垒"; do
    dir="$TOPIC_BASE/2026-03-01|$d"
    if [ -f "$dir/article.md" ]; then
        size=$(wc -c < "$dir/article.md" | tr -d ' ')
        echo "✅ $d — article.md (${size}b)" >> "$PROGRESS"
    else
        echo "❌ $d — 无 article.md" >> "$PROGRESS"
    fi
done
