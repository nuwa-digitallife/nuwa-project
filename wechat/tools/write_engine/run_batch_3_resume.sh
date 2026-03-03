#!/bin/bash
# 断点续跑：断网后恢复
cd "$(dirname "$0")"
export PATH="/usr/local/bin:/opt/homebrew/bin:/Users/ciwang/.npm-global/bin:$PATH"

PROJECT_ROOT="$(cd ../../.. && pwd)"
TOPIC_BASE="$PROJECT_ROOT/wechat/公众号选题"
PROGRESS="/tmp/batch_3_progress.txt"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$PROGRESS"
}

echo "" >> "$PROGRESS"
echo "=== 断点续跑 $(date) ===" >> "$PROGRESS"

# ── Anthropic硬刚：从 Pass 2 续跑 ──────────────────
log "▶ [R1/3] Anthropic硬刚 — 写作引擎 Pass 2 续跑"
python3 engine.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|Anthropic硬刚vs-OpenAI合作" \
    --persona 大史 \
    --model sonnet \
    --pass 2 && log "✅ [R1/3] Anthropic硬刚 — 写作完成" || log "❌ [R1/3] Anthropic硬刚 — 写作失败"

# ── 世界模型：深度调研 ──────────────────────────────
log "▶ [R2/3] 世界模型 — 深度调研启动"
python3 deep_research.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|世界模型" \
    --model sonnet && log "✅ [R2/3] 世界模型 — 调研完成" || log "❌ [R2/3] 世界模型 — 调研失败"

# ── 世界模型：写作引擎 ──────────────────────────────
log "▶ [R3/3] 世界模型 — 写作引擎启动"
python3 engine.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|世界模型" \
    --persona 丁仪 \
    --series 技术祛魅 \
    --model sonnet && log "✅ [R3/3] 世界模型 — 写作完成" || log "❌ [R3/3] 世界模型 — 写作失败"

log "=== 续跑完成 $(date) ==="
