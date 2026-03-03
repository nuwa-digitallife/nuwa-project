# qqinvest 新机器部署指南

> 给 Claude 的指令：读完这个文件，按顺序执行所有步骤，遇到错误自行排查，全部跑通后告诉我可以访问的地址。

---

## 第一步：检查 Python 版本

```bash
python3.13 --version
```

**必须是 3.13.x**。akshare 不支持 3.14+。

如果没有 3.13，用 brew 装：
```bash
brew install python@3.13
```

---

## 第二步：安装 Python 依赖

```bash
pip3.13 install fastapi uvicorn akshare pandas-ta baostock pandas python-dotenv --break-system-packages
```

验证：
```bash
python3.13 -c "import fastapi, akshare, pandas_ta, baostock; print('依赖 OK')"
```

---

## 第三步：检查 Claude CLI

```bash
claude --version
```

如果没有，安装：
```bash
npm install -g @anthropic-ai/claude-code
```

安装后登录：
```bash
claude
# 按提示完成 OAuth 登录
```

验证（能输出文字即可）：
```bash
claude -p "回复 OK" --output-format text
```

---

## 第四步：创建必要目录

```bash
cd "$(dirname "$0")"   # 进入 qqinvest/ 目录
mkdir -p reports 素材 logs results_cli
```

---

## 第五步：启动 Web 服务

```bash
python3.13 server.py &
sleep 3
curl -s http://localhost:8080/ | grep -o '<title>.*</title>'
# 应输出：<title>qqinvest — AI 投研助手</title>
```

如果端口被占用：
```bash
lsof -ti:8080 | xargs kill -9
python3.13 server.py &
```

---

## 第六步（可选）：用 ngrok 暴露公网

```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken <TOKEN>   # 从 dashboard.ngrok.com 获取
env -u HTTP_PROXY -u HTTPS_PROXY ngrok http 8080
```

拿到 `https://xxxx.ngrok-free.app` 发给朋友。

---

## 验收检查

Claude 执行完后，确认以下几点：

- [ ] `http://localhost:8080` 能打开页面
- [ ] 页面有**四个** Tab：行业研报 / 素材上传分析 / 个股量化 / 深度个股分析
- [ ] 「行业研报」Tab 输入「特种机器人」，点生成研报，任务状态变为 running
- [ ] 「深度个股分析」Tab 输入 `601608`，点开始，任务状态变为 running
- [ ] `/api/reports` 接口返回 JSON 列表

---

## 功能说明

| Tab | 功能 | 耗时 | 模型 |
|-----|------|------|------|
| 行业研报 | 网络采集行业素材 + 五节研报框架 | 30-60 分钟 | Sonnet（Pass1）+ Opus（Pass2）|
| 素材上传分析 | 上传自有素材，方法论框架对齐 | 5-20 分钟 | Opus |
| 个股量化 | 技术/情绪/资金三维评分，最多5只 | 3-15 分钟 | Sonnet |
| 深度个股分析 | 7-Agent 多空辩论：技术+新闻+基本面→多空→裁定→风险→操作方案 | 15-20 分钟 | 3×Sonnet + 4×Opus |

**推荐工作流**：行业研报 → 找推荐标的代码 → 个股量化快速筛选 → 深度分析精选标的

---

## 常见问题

**`akshare` / `baostock` 数据拉不到**：A 股数据走国内直连，如果机器在境外或有代理，需设置：
```bash
export NO_PROXY="eastmoney.com,push2his.eastmoney.com,xueqiu.com,baostock.com"
```

**`claude` 命令 not found**：确认 npm global bin 在 PATH 里：
```bash
export PATH="$PATH:$(npm root -g)/../.bin"
```

**端口 8080 冲突**：改端口启动：
```bash
python3.13 -c "
import server, uvicorn
server.init_db()
uvicorn.run(server.app, host='0.0.0.0', port=9090)
"
```
