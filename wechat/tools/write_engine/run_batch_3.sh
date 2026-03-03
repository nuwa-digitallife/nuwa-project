#!/bin/bash
# 批量写稿脚本：3篇文章顺序执行
# 用 nohup 运行：nohup bash run_batch_3.sh > /tmp/batch_3.log 2>&1 &

cd "$(dirname "$0")"

# 确保 PATH 包含 python3 和 claude
export PATH="/usr/local/bin:/opt/homebrew/bin:/Users/ciwang/.npm-global/bin:$PATH"

PROJECT_ROOT="$(cd ../../.. && pwd)"
TOPIC_BASE="$PROJECT_ROOT/wechat/公众号选题"

LOG="/tmp/batch_3.log"
PROGRESS="/tmp/batch_3_progress.txt"

log() {
    echo "[$(date '+%H:%M:%S')] $1" | tee -a "$PROGRESS"
}

# 清空进度文件
echo "=== 批量写稿开始 $(date) ===" > "$PROGRESS"

# ── 1. 三局棋：写作引擎（素材已就绪）──────────────
log "▶ [1/5] 三局棋 — 写作引擎启动"
python3 engine.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|三局棋" \
    --persona 叶哲泰 \
    --series 先驱者 \
    --model sonnet && log "✅ [1/5] 三局棋 — 写作完成" || log "❌ [1/5] 三局棋 — 写作失败"

# ── 2. Anthropic硬刚：深度调研 ──────────────────────
log "▶ [2/5] Anthropic硬刚 — 深度调研启动"
python3 deep_research.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|Anthropic硬刚vs-OpenAI合作" \
    --model sonnet && log "✅ [2/5] Anthropic硬刚 — 调研完成" || log "❌ [2/5] Anthropic硬刚 — 调研失败"

# ── 3. Anthropic硬刚：写作引擎 ──────────────────────
log "▶ [3/5] Anthropic硬刚 — 写作引擎启动"
python3 engine.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|Anthropic硬刚vs-OpenAI合作" \
    --persona 大史 \
    --model sonnet && log "✅ [3/5] Anthropic硬刚 — 写作完成" || log "❌ [3/5] Anthropic硬刚 — 写作失败"

# ── 4. 世界模型：深度调研 ──────────────────────────
log "▶ [4/5] 世界模型 — 深度调研启动"
python3 deep_research.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|世界模型" \
    --model sonnet && log "✅ [4/5] 世界模型 — 调研完成" || log "❌ [4/5] 世界模型 — 调研失败"

# ── 5. 世界模型：写作引擎 ──────────────────────────
log "▶ [5/5] 世界模型 — 写作引擎启动"
python3 engine.py \
    --topic-dir "$TOPIC_BASE/2026-03-01|世界模型" \
    --persona 丁仪 \
    --series 技术祛魅 \
    --model sonnet && log "✅ [5/5] 世界模型 — 写作完成" || log "❌ [5/5] 世界模型 — 写作失败"

log "=== 全部完成 $(date) ==="
