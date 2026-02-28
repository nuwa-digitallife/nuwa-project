#!/bin/bash
# ============================================================
# Mac Mini 发布专机 · 一键环境配置
#
# 使用:
#   curl -sL <raw_url> | bash
#   或: git clone ... && bash scripts/setup_mac_mini.sh
#
# 前置条件:
#   - macOS + Homebrew
#   - Chrome 已安装
# ============================================================

set -euo pipefail

echo "=============================================="
echo "降临派手记 · Mac Mini 发布专机配置"
echo "=============================================="

# ── 1. Homebrew ──
if ! command -v brew &>/dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# ── 2. Python 3 ──
if ! command -v python3 &>/dev/null; then
    echo "Installing Python 3..."
    brew install python3
fi

# ── 3. 虚拟环境 ──
VENV_DIR="$HOME/venv/automation"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creating virtual environment: $VENV_DIR"
    mkdir -p "$(dirname "$VENV_DIR")"
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "Activated: $VENV_DIR"

# ── 4. Python 依赖 ──
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install \
    playwright \
    pyobjc-framework-Cocoa \
    markdown \
    premailer \
    cssutils \
    pyyaml \
    requests

# ── 5. Playwright Chromium ──
echo "Installing Playwright browsers..."
playwright install chromium

# ── 6. 自签证书 (HTTPS server) ──
CERT_FILE="/tmp/cert.pem"
KEY_FILE="/tmp/key.pem"
if [[ ! -f "$CERT_FILE" ]] || [[ ! -f "$KEY_FILE" ]]; then
    echo "Generating self-signed certificate..."
    openssl req -x509 -newkey rsa:2048 \
        -keyout "$KEY_FILE" -out "$CERT_FILE" \
        -days 365 -nodes \
        -subj '/CN=localhost' 2>/dev/null
    echo "Certificate: $CERT_FILE"
fi

# ── 7. Chrome 配置提示 ──
echo ""
echo "=============================================="
echo "手动步骤（只需做一次）:"
echo "=============================================="
echo ""
echo "1. Chrome 启动参数添加 --remote-debugging-port=9222"
echo "   方法A: 创建 Chrome 启动脚本:"
echo "     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 &"
echo ""
echo "   方法B: 修改 Chrome 启动 plist:"
echo "     打开 自动操作.app → 创建应用程序 → Shell脚本 → 上面那行命令"
echo ""
echo "2. 在 Chrome 中访问 https://localhost:18443 接受自签证书（首次）"
echo "   先运行: python wechat/tools/publish/https_server.py /tmp 18443"
echo "   然后访问: https://localhost:18443 → 高级 → 继续"
echo ""
echo "3. Chrome 登录微信公众号后台:"
echo "   https://mp.weixin.qq.com → 扫码登录"
echo ""
echo "=============================================="
echo ""

# ── 8. 验证安装 ──
echo "验证安装..."
python3 -c "import markdown; print('  ✅ markdown')"
python3 -c "import premailer; print('  ✅ premailer')"
python3 -c "import AppKit; print('  ✅ AppKit (PyObjC)')"
python3 -c "from playwright.sync_api import sync_playwright; print('  ✅ playwright')"
python3 -c "import yaml; print('  ✅ pyyaml')"

echo ""
echo "=============================================="
echo "安装完成！"
echo ""
echo "测试发布:"
echo "  source $VENV_DIR/bin/activate"
echo "  python wechat/tools/publish/one_click_publish.py \\"
echo "    --topic-dir 'wechat/公众号选题/2026-02-21|机器人棋局' \\"
echo "    --dry-run"
echo "=============================================="
