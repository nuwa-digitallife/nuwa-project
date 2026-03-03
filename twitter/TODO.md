# Twitter 采集层 — 进度与待办

> 上次更新：2026-02-25
> 上次会话：实现了全部代码文件，未做实际运行测试

## 已完成

- [x] `config.py` — List URL、DOM 选择器、路径、阈值配置
- [x] `scraper.py` — Playwright persistent_context 登录态管理 + List 页抓取 + DOM 解析 + 去重 + JSONL 存储
- [x] `analyzer.py` — URL/关键词聚合 + 互动加权 + 热点检测 → signals JSON
- [x] `monitor.py` — 调度入口（scrape → analyze），CLI 参数 + 日志
- [x] 目录结构：`auth/`, `data/tweets/`, `data/signals/`, `logs/`
- [x] `.gitignore` — 忽略 auth/ data/ logs/
- [x] 语法检查通过，analyzer dry-run 正常（无数据时正确输出空结果）

## 待完成（按顺序）

### 1. 首次登录（必须手动）
```bash
source ~/venv/automation/bin/activate
cd /Users/ciwang/Desktop/nuwa-project/twitter
python scraper.py --login
```
- 浏览器弹出后手动登录 Twitter
- 登录完成后在终端按 Enter
- 登录态保存到 `auth/` 目录

### 2. 手动抓取测试
```bash
python scraper.py
```
- 确认 headless 模式能抓到推文
- 检查 `data/tweets/YYYY-MM-DD.jsonl` 内容是否正确
- 重点验证：handle 提取、推文正文、时间戳、tweet_id

### 3. 去重验证
- 连续运行两次 `python scraper.py`
- 第二次应该报告 0 条新推文（全部被去重过滤）

### 4. 热点检测测试
```bash
python analyzer.py
```
- 需要有一定量推文数据后才有意义
- 检查 `data/signals/YYYY-MM-DD.json` 输出

### 5. 端到端测试
```bash
python monitor.py
```
- 完整流程：scrape → analyze → 日志
- 检查 `logs/` 目录日志输出

### 6. 部署 cron job（Mac Mini）
```bash
crontab -e
# 添加：
*/30 * * * * source ~/venv/automation/bin/activate && cd /Users/ciwang/Desktop/nuwa-project/twitter && python monitor.py >> logs/monitor.log 2>&1
```

## 技术要点（给下一个 Claude session）

- **虚拟环境**：必须用 `~/venv/automation`，系统 Python 没有 playwright
- **登录态**：存在 `auth/` 目录，是 Chromium user data dir，一旦过期需重新 `--login`
- **DOM 选择器**：Twitter 经常改版，选择器集中在 `config.py:SELECTORS`，如果抓取失败先检查这里
- **去重索引**：`data/index.json`，key 是 tweet_id
- **List URL**：`https://x.com/i/lists/2024053078484521383`

## 风险

- Twitter 反爬：30 分钟间隔应该安全，但如果被封需要加随机延迟
- DOM 结构变化：`[data-testid="tweet"]` 是核心选择器，Twitter 改版后可能失效
- 登录态过期：scraper 会检测并报错，需手动 `--login`
