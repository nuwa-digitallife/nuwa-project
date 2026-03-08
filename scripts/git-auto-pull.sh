#!/bin/bash
# git-auto-pull.sh — 自动 pull 远端变更（launchd 定时调用）
# 仅 fast-forward，有冲突不动

REPO_DIR="$HOME/Desktop/nuwa-project"
LOG="$REPO_DIR/logs/auto-pull.log"

cd "$REPO_DIR" || exit 1

# 确保 SSH key 可用（launchd 环境没有 ssh-agent）
export SSH_AUTH_SOCK=$(launchctl getenv SSH_AUTH_SOCK 2>/dev/null || echo "")
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)" > /dev/null 2>&1
    ssh-add --apple-use-keychain ~/.ssh/id_ed25519 2>/dev/null
fi

# 确保不在 rebase/merge 中
if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ] || [ -f .git/MERGE_HEAD ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') SKIP: rebase/merge in progress" >> "$LOG"
    exit 0
fi

# 检查有无未提交的改动（有就跳过，避免冲突）
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') SKIP: uncommitted changes" >> "$LOG"
    exit 0
fi

# fast-forward only pull
OUTPUT=$(git pull --ff-only 2>&1)
STATUS=$?

if [ $STATUS -eq 0 ]; then
    if echo "$OUTPUT" | grep -q "Already up to date"; then
        # 静默，不刷日志
        :
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') PULLED: $OUTPUT" >> "$LOG"
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') FAIL: $OUTPUT" >> "$LOG"
fi
