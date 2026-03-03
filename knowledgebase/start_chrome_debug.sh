#!/bin/bash

# 启动 Chrome 浏览器并开启远程调试端口

echo "正在关闭所有 Chrome 进程..."
killall "Google Chrome" 2>/dev/null || true
sleep 2

echo "启动 Chrome（远程调试模式）..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/Library/Application Support/Google/Chrome" \
  > /dev/null 2>&1 &

echo "Chrome 已启动，远程调试端口: 9222"
echo "现在可以在 Chrome 中打开文章，然后运行: python connect_chrome.py"
