# 周末冲刺计划 (2026-02-28)

> 状态: 执行中 | 归档后标记 ✅

## 目标

T0 发布自动化 + T1 备稿7篇 + T2 新闻反应管道 + T3 幽灵Demo

## Checklist

### 第一阶段：基础设施
- [x] `publish/theme_orange.css` — 橙心主题 CSS（已创建，后弃用改走 mdnice）
- [x] `publish/render_html.py` — Markdown → HTML（已创建，后弃用改走 mdnice）
- [x] `publish/clipboard_html.py` — HTML → macOS剪贴板
- [x] `publish/wechat_automator.py` — Playwright CDP 控制微信编辑器
- [x] `scripts/setup_mac_mini.sh` — Mac Mini 一键环境配置

### 第二阶段：发布自动化
- [x] `publish/one_click_publish.py` — 端到端发布脚本（重写为 mdnice 浏览器自动化方案）
- [🔧] 用机器人棋局 dry-run 实测 — Mac Mini 上调试中，接近完成

### 第三阶段：批量生产
- [x] `run_pipeline.sh` 新增 `--batch N` 模式
- [x] `topic_pipeline.py` 新增 `--num-topics N` 参数
- [ ] 跑已有5个选题（AI大模型前沿/AI工作室动态/AI应用落地/中美AI竞争/具身智能）
- [ ] 搜索+推荐2个新选题

### 第四阶段：反应管道 + Ghost
- [x] `react.py` — 链接→草稿一键流程（含 exporter auth-key 修复）
- [x] `ghost_analyze.py` — 能力缺口分析 demo
- [x] `prompts/ghost_gap_analysis.md` — Ghost prompt
- [ ] react.py 端到端实测
- [ ] ghost_analyze.py 端到端实测

### 第五阶段：集成验证
- [ ] 完整流程实测：react.py → one_click_publish.py
- [x] 更新 AUTOMATION_PLAN.md（场景愿景 + WS-4/WS-8 状态）
