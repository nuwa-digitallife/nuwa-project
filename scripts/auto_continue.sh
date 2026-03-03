#!/bin/bash
# auto_continue.sh — Token 额度恢复后自动在指定终端输入"继续"
#
# 用法：
#   ./auto_continue.sh              # 先列出所有窗口，选择目标
#   ./auto_continue.sh 45175        # 直接指定窗口 ID
#   ./auto_continue.sh 45175 300    # 指定窗口 ID + 间隔秒数
#
# 原理：用窗口 ID（不会变）锁定目标，pbcopy + Cmd+V 粘贴"继续" + 回车

WINDOW_ID="$1"
INTERVAL="${2:-300}"

# 如果没给 ID，列出所有窗口让用户选
if [ -z "$WINDOW_ID" ]; then
    echo "当前所有 Terminal 窗口："
    echo ""
    osascript <<'EOF'
tell application "Terminal"
    repeat with w in windows
        log "  ID=" & (id of w) & "  " & name of w
    end repeat
end tell
EOF
    echo ""
    echo "用法: $0 <窗口ID> [间隔秒数]"
    echo "示例: $0 45175 300"
    exit 0
fi

# 验证窗口存在
CHECK=$(osascript -e "tell application \"Terminal\" to return name of window id $WINDOW_ID" 2>&1)
if echo "$CHECK" | grep -q "error"; then
    echo "❌ 窗口 ID $WINDOW_ID 不存在"
    exit 1
fi

echo "🔄 Auto-continue 已启动"
echo "   目标窗口: ID=$WINDOW_ID"
echo "   窗口标题: $CHECK"
echo "   检查间隔: ${INTERVAL}秒"
echo "   按 Ctrl+C 停止"
echo ""

while true; do
    sleep "$INTERVAL"

    # 保存当前剪贴板
    OLD_CLIP=$(pbpaste 2>/dev/null)

    # 把"继续"放进剪贴板
    echo -n "继续" | pbcopy

    FOUND=$(osascript <<EOF
try
    tell application "Terminal"
        set targetWin to window id $WINDOW_ID
        -- 把目标窗口带到最前
        set frontmost of targetWin to true
    end tell

    delay 0.5

    tell application "System Events"
        tell process "Terminal"
            set frontmost to true
            delay 0.5
            -- Cmd+V 粘贴
            keystroke "v" using command down
            delay 0.3
            -- 回车
            key code 36
        end tell
    end tell

    return "found"
on error
    return "not_found"
end try
EOF
)

    # 恢复剪贴板
    echo -n "$OLD_CLIP" | pbcopy 2>/dev/null

    NOW=$(date "+%H:%M:%S")
    if [ "$FOUND" = "found" ]; then
        echo "[$NOW] ✅ 已向窗口 $WINDOW_ID 发送「继续」"
    else
        echo "[$NOW] ❌ 窗口 $WINDOW_ID 已关闭或不可达"
    fi
done
