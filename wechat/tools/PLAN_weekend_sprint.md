# 周末冲刺计划 (2026-02-28)

> 状态: 执行中 | 归档后标记 ✅

## 目标

T0 发布自动化 + T1 备稿7篇 + T2 新闻反应管道 + T3 幽灵Demo

## Checklist

### 第一阶段：基础设施
- [ ] `publish/theme_orange.css` — 橙心主题 CSS
- [ ] `publish/render_html.py` — Markdown → 带内联CSS的HTML
- [ ] `publish/clipboard_html.py` — HTML → macOS剪贴板
- [ ] `publish/wechat_automator.py` — Playwright CDP 控制微信编辑器
- [ ] `scripts/setup_mac_mini.sh` — Mac Mini 一键环境配置

### 第二阶段：发布自动化
- [ ] `publish/one_click_publish.py` — 端到端发布脚本
- [ ] 用机器人棋局 dry-run 实测

### 第三阶段：批量生产
- [ ] `run_pipeline.sh` 新增 `--batch N` 模式
- [ ] `topic_pipeline.py` 新增 `--num-topics N` 参数
- [ ] 跑已有5个选题
- [ ] 搜索+推荐2个新选题

### 第四阶段：反应管道 + Ghost
- [ ] `react.py` — 链接→草稿一键流程
- [ ] `ghost_analyze.py` — 能力缺口分析 demo
- [ ] `prompts/ghost_gap_analysis.md` — Ghost prompt

### 第五阶段：集成验证
- [ ] 完整流程实测
- [ ] 更新 AUTOMATION_PLAN.md
