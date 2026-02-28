#!/bin/bash
# ============================================================
# 降临派手记 · 自动选题+写作流水线 orchestrator
#
# 流程：
#   1.  Python 搜素材 + 推荐选题 (topic_pipeline.py)
#   1.5 深度素材采集 (deep_research.py, opus $4/选题)
#   2.  4-Pass 写作引擎 (engine.py, opus $11.5/选题)
#       含：写作→事实核查→三层恰Review→整合交付物→封面图→lessons提取
#   3.  输出到 wechat/公众号选题/{日期}|{选题名}/
#
# 使用：
#   ./run_pipeline.sh              # 完整流程：搜+推荐+写
#   ./run_pipeline.sh --search     # 只搜素材
#   ./run_pipeline.sh --write      # 只写文章（用已有素材）
#   ./run_pipeline.sh --topic "Anthropic蒸馏"  # 手动选题
#   ./run_pipeline.sh --batch 7                # 批量模式：搜+写 N 篇
#   ./run_pipeline.sh --batch 7 --persona 章北海  # 批量 + 指定人设
#   ./run_pipeline.sh --publish-all            # 对所有已完成文章调用发布
#
# 定时执行：
#   launchd 每晚 23:00 运行
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WECHAT_DIR="$PROJECT_ROOT/wechat"
VENV="$HOME/venv/automation/bin/activate"
CONFIG_FILE="$SCRIPT_DIR/topic_config.yaml"
TODAY=$(date +%Y-%m-%d)
LOG_FILE="$PROJECT_ROOT/logs/pipeline_${TODAY}.log"

# 从 topic_config.yaml 读取模型配置（各阶段共用这里的值）
read_model_config() {
    local stage="$1"
    python3 -c "
import yaml, sys
with open('$CONFIG_FILE') as f:
    c = yaml.safe_load(f)
m = c.get('models', {}).get('$stage', {})
print(m.get('model', 'opus'))
" 2>/dev/null || echo "opus"
}

MODEL_DEEP=$(read_model_config deep_research)
MODEL_WRITE=$(read_model_config write_engine)

# 确保日志目录存在
mkdir -p "$PROJECT_ROOT/logs"

log() {
    echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG_FILE"
}

# ── 读取人设文件 ──────────────────────────────────────
get_persona_prompt() {
    local persona_name="$1"
    local persona_file="$WECHAT_DIR/人设/${persona_name}.md"
    if [[ -f "$persona_file" ]]; then
        cat "$persona_file"
    else
        echo "你是降临派手记的作者。"
    fi
}

# ── Phase 1: 素材搜集 ────────────────────────────────
run_search() {
    log "========== Phase 1: 素材搜集 =========="
    source "$VENV"
    python "$SCRIPT_DIR/topic_pipeline.py" "$@" 2>&1 | tee -a "$LOG_FILE"
}

# ── Phase 1.5: 素材深度采集 ─────────────────────────
run_deep_research() {
    log "========== Phase 1.5: 素材深度采集 =========="

    local base_dir="$WECHAT_DIR/公众号选题"
    local deep_research="$SCRIPT_DIR/write_engine/deep_research.py"
    local date_prefix="${1:-$TODAY}"

    local topic_dirs=()
    for dir in "$base_dir/${date_prefix}|"*/; do
        [[ -d "$dir" ]] && topic_dirs+=("$dir")
    done

    if [[ ${#topic_dirs[@]} -eq 0 ]]; then
        log "⚠ 未找到选题目录（前缀: ${date_prefix}|），跳过深度采集"
        return 0
    fi

    for topic_dir in "${topic_dirs[@]}"; do
        local topic_name=$(basename "$topic_dir" | sed "s/^[0-9-]*|//")
        local deep_file="$topic_dir/素材/deep_research.md"

        # 跳过已有深度素材的
        if [[ -f "$deep_file" ]]; then
            log "  [$topic_name] 已有深度素材，跳过"
            continue
        fi

        log "  [$topic_name] 启动深度素材采集 ($MODEL_DEEP, \$4)..."
        python "$deep_research" \
            --topic-dir "$topic_dir" \
            --model "$MODEL_DEEP" \
            2>&1 | tee -a "$LOG_FILE"

        if [[ -f "$deep_file" ]]; then
            log "  [$topic_name] ✅ 深度素材采集完成"
        else
            log "  [$topic_name] ⚠ 深度素材采集失败，继续写作"
        fi
    done

    log "Phase 1.5 完成"
}

# ── Phase 2: 写文章 ──────────────────────────────────
write_articles() {
    local persona_override="${1:-}"
    local date_prefix="${2:-$TODAY}"

    log "========== Phase 2: 写文章 =========="

    local base_dir="$WECHAT_DIR/公众号选题"
    local report="$base_dir/${date_prefix}_选题推荐.md"

    # 读取推荐的选题目录
    local topic_dirs=()
    for dir in "$base_dir/${date_prefix}|"*/; do
        [[ -d "$dir" ]] && topic_dirs+=("$dir")
    done

    if [[ ${#topic_dirs[@]} -eq 0 ]]; then
        log "⚠ 未找到选题目录（前缀: ${date_prefix}|）"
        return 1
    fi

    log "找到 ${#topic_dirs[@]} 个选题目录"

    # 为每个选题调用多Agent写作引擎
    local engine="$SCRIPT_DIR/write_engine/engine.py"
    local completed=0
    local failed=0

    for topic_dir in "${topic_dirs[@]}"; do
        local topic_name=$(basename "$topic_dir" | sed "s/^[0-9-]*|//")
        local article_file="$topic_dir/article.md"

        # 跳过已经有文章的选题
        if [[ -f "$article_file" ]]; then
            log "  [$topic_name] 已有 article.md，跳过"
            ((completed++))
            continue
        fi

        # 人设：命令行覆盖 > 推荐报告 > 默认
        local persona="${persona_override:-}"
        if [[ -z "$persona" ]] && [[ -f "$report" ]]; then
            if grep -q "$topic_name.*章北海" "$report" 2>/dev/null; then
                persona="章北海"
            elif grep -q "$topic_name.*罗辑" "$report" 2>/dev/null; then
                persona="罗辑"
            fi
        fi
        persona="${persona:-大史}"

        log "  [$topic_name] 启动 4-Pass 写作引擎 (人设: $persona, 模型: $MODEL_WRITE)..."

        python "$engine" \
            --topic-dir "$topic_dir" \
            --persona "$persona" \
            --model "$MODEL_WRITE" \
            2>&1 | tee -a "$LOG_FILE"

        if [[ -f "$article_file" ]] && [[ -s "$article_file" ]]; then
            local word_count=$(wc -c < "$article_file")
            log "  [$topic_name] ✅ 完成 (${word_count} bytes, 人设: ${persona})"
            ((completed++))
        else
            log "  [$topic_name] ⚠ 写作失败"
            ((failed++))
        fi
    done

    log "Phase 2 完成: ${completed} 篇完成, ${failed} 篇失败"
}

# ── 手动选题 ──────────────────────────────────────────
manual_topic() {
    local topic="$1"
    local persona_override="${2:-}"
    log "========== 手动选题: $topic =========="
    source "$VENV"

    # 搜素材
    python "$SCRIPT_DIR/topic_pipeline.py" --topic "$topic" 2>&1 | tee -a "$LOG_FILE"

    # 深度采集 + 写文章
    local topic_dir="$WECHAT_DIR/公众号选题/${TODAY}|${topic}"
    if [[ -d "$topic_dir" ]]; then
        # 创建临时推荐报告以便写文章流程找到
        local report="$WECHAT_DIR/公众号选题/${TODAY}_选题推荐.md"
        if [[ ! -f "$report" ]]; then
            echo "# 手动选题\n## 1. $topic (推荐人设: 大史)" > "$report"
        fi
        run_deep_research
        write_articles "$persona_override"
    fi
}

# ── 批量模式 ──────────────────────────────────────────
batch_mode() {
    local num_topics="$1"
    local persona_override="${2:-}"
    log "========== 批量模式: ${num_topics} 篇 =========="
    source "$VENV"

    # Phase 1: 搜素材 + 推荐 N 个选题
    log "--- 搜索 + 推荐 ${num_topics} 个选题 ---"
    python "$SCRIPT_DIR/topic_pipeline.py" --num-topics "$num_topics" 2>&1 | tee -a "$LOG_FILE"

    # Phase 1.5: 深度采集
    run_deep_research

    # Phase 2: 逐个写文章
    write_articles "$persona_override"

    # 生成批量 review 汇总
    generate_batch_review
}

# ── 生成批量 review 汇总 ──────────────────────────────
generate_batch_review() {
    local base_dir="$WECHAT_DIR/公众号选题"
    local review_file="$base_dir/${TODAY}_batch_review.md"

    log "--- 生成 batch review ---"

    cat > "$review_file" << 'HEADER'
# 批量写作 Review

> 标记 ✅ 表示可发布，❌ 表示需要修改

HEADER

    echo "| # | 选题 | 人设 | 字数 | 状态 |" >> "$review_file"
    echo "|---|------|------|------|------|" >> "$review_file"

    local idx=0
    for dir in "$base_dir/${TODAY}|"*/; do
        [[ -d "$dir" ]] || continue
        ((idx++))
        local topic_name=$(basename "$dir" | sed "s/^${TODAY}|//")
        local article="$dir/article.md"

        if [[ -f "$article" ]] && [[ -s "$article" ]]; then
            local chars=$(wc -c < "$article")
            # 尝试从 publish_guide.md 提取人设
            local persona="—"
            if [[ -f "$dir/publish_guide.md" ]]; then
                persona=$(grep -oP '(?<=· )\S+(?=执笔|·)' "$dir/publish_guide.md" 2>/dev/null | head -1)
                persona="${persona:-—}"
            fi
            echo "| $idx | $topic_name | $persona | ${chars} | ⬜ 待审 |" >> "$review_file"
        else
            echo "| $idx | $topic_name | — | — | ❌ 写作失败 |" >> "$review_file"
        fi
    done

    log "Review 汇总: $review_file"
}

# ── 批量发布 ──────────────────────────────────────────
publish_all() {
    local date_prefix="${1:-$TODAY}"
    log "========== 批量发布 =========="
    source "$VENV"

    local base_dir="$WECHAT_DIR/公众号选题"
    local publish_script="$SCRIPT_DIR/publish/one_click_publish.py"
    local published=0

    for dir in "$base_dir/${date_prefix}|"*/; do
        [[ -d "$dir" ]] || continue
        local topic_name=$(basename "$dir" | sed "s/^[0-9-]*|//")

        # 必须有完整的发布文件
        if [[ ! -f "$dir/article_mdnice.md" ]] || [[ ! -f "$dir/publish_guide.md" ]]; then
            log "  [$topic_name] 缺少发布文件，跳过"
            continue
        fi

        log "  [$topic_name] 发布中..."
        python "$publish_script" --topic-dir "$dir" 2>&1 | tee -a "$LOG_FILE"

        if [[ $? -eq 0 ]]; then
            ((published++))
            log "  [$topic_name] ✅ 草稿已保存"
        else
            log "  [$topic_name] ⚠ 发布失败"
        fi

        # 每篇之间间隔 5 秒，避免频率限制
        sleep 5
    done

    log "批量发布完成: ${published} 篇"
}

# ── 主入口 ────────────────────────────────────────────
main() {
    log "=============================================="
    log "降临派手记 · 流水线 v0.2"
    log "=============================================="

    # 解析全局选项
    local persona_override=""
    local args=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --persona)
                persona_override="$2"
                shift 2
                ;;
            *)
                args+=("$1")
                shift
                ;;
        esac
    done
    set -- "${args[@]:-}"

    case "${1:-full}" in
        --search)
            shift
            run_search "$@"
            ;;
        --write)
            write_articles "$persona_override"
            ;;
        --topic)
            shift
            manual_topic "$1" "$persona_override"
            ;;
        --batch)
            shift
            local num="${1:-7}"
            batch_mode "$num" "$persona_override"
            ;;
        --publish-all)
            shift
            publish_all "${1:-$TODAY}"
            ;;
        full|"")
            run_search
            run_deep_research
            write_articles "$persona_override"
            ;;
        *)
            echo "用法: $0 [--search|--write|--topic <名称>|--batch N|--publish-all] [--persona 人设]"
            exit 1
            ;;
    esac

    log "=============================================="
    log "流水线完成"
    log "=============================================="

    # macOS 通知
    osascript -e "display notification \"选题流水线完成\" with title \"降临派手记\"" 2>/dev/null || true
}

main "$@"
