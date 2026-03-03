# qqinvest 部署指南

> **给 Claude 的指令**：读完这个文件，按顺序执行所有步骤，遇到错误自行排查，全部跑通后告诉我可以访问的地址。

---

## 前置说明：目录结构

两个仓库必须放在同一个父目录下：

```
nuwa-project/          ← 父目录（名字随意）
├── qqinvest/          ← 本仓库
└── TradingAgents-CN/  ← 量化 Agent 依赖（必须和 qqinvest/ 同级）
```

克隆方式：
```bash
git clone <qqinvest-repo-url> qqinvest
git clone <TradingAgents-CN-repo-url> TradingAgents-CN
```

---

## 第一步：Python 3.13

```bash
python3.13 --version   # 必须是 3.13.x，akshare 不支持 3.14+
```

没有就装：
```bash
brew install python@3.13   # macOS
```

---

## 第二步：安装依赖

### qqinvest 依赖
```bash
pip3.13 install streamlit fastapi uvicorn akshare pandas-ta baostock \
    pandas python-dotenv requests --break-system-packages
```

### TradingAgents-CN 依赖
```bash
cd ../TradingAgents-CN
pip3.13 install -e . --break-system-packages
# 如果 -e 安装慢，也可以直接：
pip3.13 install langchain langgraph langchain-core langchain-openai \
    pydantic akshare baostock pandas yfinance tqdm pytz rich \
    --break-system-packages
cd ../qqinvest
```

验证：
```bash
python3.13 -c "import streamlit, akshare, langgraph; print('依赖 OK')"
```

---

## 第三步：Claude CLI

```bash
claude --version
```

没有就装：
```bash
npm install -g @anthropic-ai/claude-code
```

装完登录（OAuth，需要浏览器）：
```bash
claude
```

验证：
```bash
claude -p "回复 OK" --output-format text
# 应输出：OK
```

---

## 第四步：创建必要目录

```bash
mkdir -p reports 素材 logs
mkdir -p ../TradingAgents-CN/reports
```

---

## 第五步：启动演示 UI

```bash
cd qqinvest/   # 确保在 qqinvest 目录下
python3.13 -m streamlit run app.py --server.port 8502
```

浏览器打开 `http://localhost:8502`，看到「主观研究 × 量化验证」页面即为成功。

**公网暴露（给朋友演示）：**
```bash
brew install ngrok/ngrok/ngrok
ngrok config add-authtoken <TOKEN>   # 从 dashboard.ngrok.com 获取
ngrok http 8502
# 拿到 https://xxxx.ngrok-free.app 发给朋友
```

---

## 第六步（可选）：启动旧版 FastAPI 服务

旧版四 Tab 服务（行业研报 / 素材上传 / 个股量化 / 深度分析）：
```bash
python3.13 server.py
# 访问 http://localhost:8080
```

---

## 功能说明

### 演示 UI（app.py，推荐）

| Tab | 内容 | 关键操作 |
|-----|------|---------|
| 🧠 行业主观研究 | 左侧填写研究员主观判断，右侧看 AI 验证报告 | 填催化剂/标的/非共识 → 「运行完整分析」|
| ⚡ 个股量化分析 | 8 Agent 多空辩论 + 风险评估 + 交易信号 | 输入股票代码 → 看交易信号 / 下载报告 |
| 📋 综合投研决策 | 两层合并：主观行业研判 + 量化执行信号 | 选报告 → 左右对比 + 方法论说明 |

**推荐演示流程：**
1. Tab 1：展示已有行业研报（特种机器人），指出 AI 是如何逐条验证研究员判断的
2. Tab 2：展示 601608 的量化报告 → 卖出 ¥7.1，置信度 0.62，风险 0.76
3. Tab 3：综合视图，讲「主观选赛道、量化给执行信号」

### 生成新报告（命令行）

```bash
# 行业研报（全流程，约 60-90 分钟）
python3.13 run_round1.py --sector "特种机器人（矿山/军工/安防/电力巡检）"

# 只跑 Pass 2（用已有素材，约 30-60 分钟）
python3.13 run_round1.py --skip-pass1

# 个股量化分析（约 15-30 分钟）
cd ../TradingAgents-CN
python3.13 run_demo_claudecli.py 601608 2026-03-01
# 报告保存在 TradingAgents-CN/reports/claudecli_601608_2026-03-01.md
```

---

## 常见问题

**`akshare` / `baostock` 拉不到数据**（在境外或有代理时）：
```bash
export NO_PROXY="eastmoney.com,push2his.eastmoney.com,xueqiu.com,baostock.com,sina.com.cn"
```

**`claude` 命令 not found**：
```bash
export PATH="$PATH:$(npm root -g)/../.bin"
```

**端口被占用**：
```bash
lsof -ti:8502 | xargs kill -9
python3.13 -m streamlit run app.py --server.port 8502
```

**TradingAgents-CN 找不到**（app.py 报错 `No such file or directory`）：
- 确认目录结构：`qqinvest/` 和 `TradingAgents-CN/` 必须在同一个父目录下
- 检查：`ls ../TradingAgents-CN/run_demo_claudecli.py`

**`ModuleNotFoundError: tradingagents`**：
```bash
cd ../TradingAgents-CN && pip3.13 install -e . --break-system-packages
```

---

## 验收 Checklist

- [ ] `http://localhost:8502` 能打开，标题是「主观研究 × 量化验证」
- [ ] Tab 1 右侧能看到行业研报内容，「下载报告」按钮可用
- [ ] Tab 2 显示 601608 的量化报告，「交易信号」显示「卖出」，目标价 ¥7.1
- [ ] Tab 3 左右两栏都有内容，右侧卡片显示卖出信号
- [ ] `claude -p "回复 OK" --output-format text` 正常输出
