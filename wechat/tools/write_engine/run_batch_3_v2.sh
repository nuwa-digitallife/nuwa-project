#!/bin/bash
# 第二次续跑：Anthropic硬刚从Pass1重跑（新素材）+ 世界模型全跑
cd "$(dirname "$0")"
export PATH="/usr/local/bin:/opt/homebrew/bin:/Users/ciwang/.npm-global/bin:$PATH"

PROJECT_ROOT="$(cd ../../.. && pwd)"
TOPIC_BASE="$PROJECT_ROOT/wechat/公众号选题"
PROGRESS="/tmp/batch_3_progress.txt"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$PROGRESS"
}

echo "" >> "$PROGRESS"
echo "=== v2 重跑 $(date) ===" >> "$PROGRESS"

# ── Anthropic硬刚：从 Pass 1 全部重跑（含 Khamenei/Claude 新素材）──
log "▶ [v2-1/3] Anthropic硬刚 — 写作引擎 Pass 1 全跑（新素材）"
python3 engine.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|Anthropic硬刚vs-OpenAI合作" \
    --persona 大史 \
    --model sonnet && log "✅ [v2-1/3] Anthropic硬刚 — 写作完成" || log "❌ [v2-1/3] Anthropic硬刚 — 写作失败"

# ── 世界模型：深度调研 ──
log "▶ [v2-2/3] 世界模型 — 深度调研"
python3 deep_research.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|世界模型" \
    --model sonnet && log "✅ [v2-2/3] 世界模型 — 调研完成" || log "❌ [v2-2/3] 世界模型 — 调研失败"

# ── 世界模型：写作引擎 ──
log "▶ [v2-3/3] 世界模型 — 写作引擎"
python3 engine.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|世界模型" \
    --persona 丁仪 \
    --series 技术祛魅 \
    --model sonnet && log "✅ [v2-3/3] 世界模型 — 写作完成" || log "❌ [v2-3/3] 世界模型 — 写作失败"

log "=== v2 完成 $(date) ==="
