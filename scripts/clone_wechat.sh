#!/bin/bash
# 在其他电脑上只拉公众号相关内容（~30M vs 完整 repo 1.3G）
# 用法: curl -sL <raw_url> | bash
#   或: bash clone_wechat.sh [目标目录]

set -e

REPO="git@github.com:nuwa-digitallife/nuwa-project.git"
TARGET_DIR="${1:-nuwa-project}"

echo "=== 公众号轻量 clone ==="
echo "目标目录: $TARGET_DIR"
echo ""

git clone --filter=blob:none --sparse "$REPO" "$TARGET_DIR"
cd "$TARGET_DIR"

# 只拉公众号相关目录
git sparse-checkout set \
  wechat/ \
  logs/ \
  docs/ \
  write_engine/ \
  CLAUDE.md

echo ""
echo "=== 完成 ==="
echo "大小: $(du -sh . | cut -f1)"
echo ""
echo "后续按需添加目录:"
echo "  git sparse-checkout add knowledgebase/"
echo "  git sparse-checkout add scripts/"
echo ""
echo "查看当前拉取的目录:"
echo "  git sparse-checkout list"
