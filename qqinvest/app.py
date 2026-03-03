#!/usr/bin/env python3.13
"""
qqinvest 投研演示系统
主观行业研究 × 量化个股分析 — 整合演示 UI
"""

import subprocess
import os
import time
import threading
from datetime import datetime
from pathlib import Path

import streamlit as st

# ── 路径 ──────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
TRADING_ROOT = ROOT.parent / "TradingAgents-CN"
REPORTS_DIR = ROOT / "reports"
MATERIALS_DIR = ROOT / "素材"
PROMPTS_DIR = ROOT / "prompts"
TA_REPORTS_DIR = TRADING_ROOT / "reports"

# ── 页面配置 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="qqinvest · 投研系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 样式 ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 主色调 */
:root {
    --primary: #1a56db;
    --accent: #e74694;
    --success: #0e9f6e;
    --warning: #ff5a1f;
    --bg-card: #f9fafb;
    --border: #e5e7eb;
}

/* 全局字体 */
body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }

/* Tab 样式 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 2px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    padding: 12px 28px;
    font-size: 15px;
    font-weight: 500;
    color: #6b7280;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
}
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom: 2px solid var(--primary) !important;
    background: transparent !important;
}

/* 卡片 */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}

/* 标签 */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 6px;
}
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-green { background: #d1fae5; color: #065f46; }
.badge-red { background: #fee2e2; color: #991b1b; }
.badge-gray { background: #f3f4f6; color: #374151; }

/* 流程图 */
.flow-box {
    background: white;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    padding: 12px 18px;
    text-align: center;
    font-weight: 600;
    font-size: 14px;
}
.flow-arrow {
    text-align: center;
    font-size: 20px;
    color: #9ca3af;
    line-height: 1.2;
}

/* 研究员输入区 */
.analyst-input-header {
    background: linear-gradient(135deg, #1a56db08, #e7469408);
    border: 1.5px solid #1a56db30;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 16px;
}

/* 决策信号 */
.signal-buy { color: #0e9f6e; font-size: 28px; font-weight: 800; }
.signal-sell { color: #e02424; font-size: 28px; font-weight: 800; }
.signal-hold { color: #ff5a1f; font-size: 28px; font-weight: 800; }

/* 隐藏默认元素 */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════════════════════

def list_reports(directory: Path, pattern: str = "*.md") -> list[Path]:
    """列出目录下所有 .md 报告，按修改时间倒序。"""
    if not directory.exists():
        return []
    files = [f for f in directory.glob(pattern)
             if not f.name.startswith("duplicate_")
             and not f.name.startswith("logger_")
             and not f.name.startswith("logging_")
             and not f.name.startswith("print_to_")
             and not f.name.startswith("syntax_")]
    return sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)


def read_report(path: Path) -> str:
    """读取报告文件内容。"""
    if path and path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def extract_decision(content: str) -> dict:
    """从 TradingAgents-CN 报告中提取关键决策信息。"""
    import re, ast
    result = {"action": "", "price": "", "confidence": "", "risk": "", "reasoning": ""}

    # 优先：匹配 Python dict repr 格式（TradingAgents-CN 的最终输出格式）
    # 形如: {'action': '卖出', 'target_price': 7.1, 'confidence': 0.62, ...}
    m = re.search(r"\{['\"]action['\"]\s*:\s*['\"][^'\"]+['\"].*?\}", content, re.DOTALL)
    if m:
        try:
            d = ast.literal_eval(m.group(0))
            result["action"] = str(d.get("action", ""))
            tp = d.get("target_price", "")
            result["price"] = f"¥{tp}" if tp else ""
            conf = d.get("confidence", "")
            result["confidence"] = str(conf) if conf else ""
            risk = d.get("risk_score", "")
            result["risk"] = str(risk) if risk else ""
            result["reasoning"] = str(d.get("reasoning", ""))[:300]
            return result
        except Exception:
            pass

    # fallback：正则提取纯文本格式
    for kw in ["最终决策", "交易决策", "操作建议", "建议：", "结论："]:
        m = re.search(rf"{kw}[：:\s]*([^\n]{{2,20}})", content)
        if m:
            result["action"] = m.group(1).strip()
            break

    m = re.search(r"目标价[：:\s]*[¥￥]?([\d.]+)", content)
    if m:
        result["price"] = f"¥{m.group(1)}"

    m = re.search(r"置信度[：:\s]*([\d.]+)", content)
    if m:
        result["confidence"] = m.group(1)

    m = re.search(r"风险[评分]*[：:\s]*([\d.]+)", content)
    if m:
        result["risk"] = m.group(1)

    return result


def run_pass2_with_analyst_view(
    sector: str,
    analyst_views: dict,
    materials_file: Path,
    output_placeholder,
) -> Path:
    """注入研究员主观观点后运行 Pass 2。"""
    template_file = PROMPTS_DIR / "pass2_template.md"
    if not template_file.exists():
        template_file = PROMPTS_DIR / "pass2_analysis.md"

    prompt_template = template_file.read_text(encoding="utf-8").replace("{sector}", sector)
    materials = materials_file.read_text(encoding="utf-8")

    # 构建主观框架注入块
    analyst_block = _build_analyst_block(analyst_views)

    prompt = f"""{prompt_template}

---

{analyst_block}

---

## 以下是 Pass 1 采集的原始素材

{materials}

---

请基于以上素材，按照上述五节框架撰写完整研报。
对【研究员主观框架】中的每条判断，必须在报告对应章节明确回应：
- ✅ 数据支持此判断（引用具体数据）
- ❌ 数据不支持（说明原因）
- ⚠️ 证据不足（指出缺少什么数据）

素材中标注「[待验证]」的内容，在报告中同样标注，不编造。
"""

    # 异步运行，实时更新状态
    date_str = datetime.now().strftime("%Y-%m-%d")
    import re
    slug = re.sub(r"[（）()【】\[\]/\\]", "_", sector)[:20].strip("_")
    output_file = REPORTS_DIR / f"{slug}_round1_{date_str}.md"

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)

    cmd = [
        "claude", "-p", prompt,
        "--model", "claude-opus-4-6",
        "--allowedTools", "WebSearch,WebFetch,Read",
        "--output-format", "text",
    ]

    output_placeholder.info("正在启动 Claude Opus 分析（约 30-60 分钟）...")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=str(ROOT),
        env=env,
    )

    stdout, stderr = proc.communicate(timeout=3600)

    if proc.returncode != 0:
        output_placeholder.error(f"分析失败：{stderr[-500:]}")
        return None

    # 保存报告
    header = f"# {sector} 行业投研报告\n**生成时间**：{date_str}\n**素材来源**：{materials_file.name}\n\n---\n\n"
    full_report = header + analyst_block + "\n\n---\n\n" + stdout
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file.write_text(full_report, encoding="utf-8")

    return output_file


def _build_analyst_block(views: dict) -> str:
    """将研究员的主观判断格式化为结构化注入块。"""
    parts = ["## 研究员主观框架（AI 必须逐条验证）\n"]
    parts.append("> 以下是研究员基于主观判断提出的假设，请用数据逐条回应：\n")

    mapping = {
        "catalyst": "催化剂假设",
        "core_stocks": "核心标的判断",
        "non_consensus": "非共识/差异化观点",
        "concerns": "主要顾虑/风险",
        "timeframe": "时间节奏判断",
    }

    for key, label in mapping.items():
        val = views.get(key, "").strip()
        if val:
            parts.append(f"**{label}**：{val}\n")

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════════════
# 页面顶部
# ══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="padding: 24px 0 8px 0;">
  <div style="font-size: 11px; font-weight: 600; letter-spacing: 2px; color: #6b7280; text-transform: uppercase; margin-bottom: 4px;">qqinvest · 投研演示系统</div>
  <div style="font-size: 26px; font-weight: 700; color: #111827; line-height: 1.2;">主观研究 × 量化验证</div>
  <div style="font-size: 14px; color: #6b7280; margin-top: 6px;">研究员写下判断 → AI 用数据验证 → 量化 Agent 给出执行信号</div>
</div>
""", unsafe_allow_html=True)

# 流程示意
c1, c2, c3, c4, c5 = st.columns([2, 0.6, 2, 0.6, 2])
with c1:
    st.markdown('<div class="flow-box" style="border-color: #1a56db40; background: #eff6ff;">🧠 研究员主观判断<br><span style="font-size:11px;color:#6b7280;font-weight:400;">催化剂 · 标的 · 节奏</span></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="flow-arrow">→</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="flow-box" style="border-color: #7c3aed40; background: #f5f3ff;">📊 AI 行业研报<br><span style="font-size:11px;color:#6b7280;font-weight:400;">数据验证 · 产业链 · 筛股</span></div>', unsafe_allow_html=True)
with c4:
    st.markdown('<div class="flow-arrow">→</div>', unsafe_allow_html=True)
with c5:
    st.markdown('<div class="flow-box" style="border-color: #059669 40; background: #ecfdf5;">⚡ 量化 Agent<br><span style="font-size:11px;color:#6b7280;font-weight:400;">技术 · 基本面 · 风控 · 择时</span></div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════
# 三个 Tab
# ══════════════════════════════════════════════════════════════════════════

tab1, tab2, tab3 = st.tabs([
    "🧠  行业主观研究",
    "⚡  个股量化分析",
    "📋  综合投研决策",
])


# ──────────────────────────────────────────────────────────────────────────
# Tab 1：行业主观研究
# ──────────────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1.6], gap="large")

    with col_left:
        # ── 研究员主观判断输入区 ──────────────────────────────────────
        st.markdown("""
        <div class="analyst-input-header">
          <div style="font-size: 15px; font-weight: 700; color: #1a56db; margin-bottom: 4px;">
            ✏️ 研究员主观框架
          </div>
          <div style="font-size: 12px; color: #6b7280;">
            先写下你的判断，AI 会用数据逐条验证或挑战
          </div>
        </div>
        """, unsafe_allow_html=True)

        sector = st.text_input(
            "目标行业",
            value="特种机器人（矿山/军工/安防/电力巡检）",
            help="AI 将围绕此行业进行深度研究",
        )

        catalyst = st.text_area(
            "🔥 催化剂假设",
            placeholder="例：我认为 2025 年矿山机器人最大催化剂是安监新规落地，煤矿智能化改造强制时间窗口打开...",
            height=100,
            help="你认为行业今年/明年最重要的驱动因素",
        )

        core_stocks = st.text_area(
            "🎯 核心标的判断",
            placeholder="例：重点关注中信重工（601608）和北方自动化（600184），前者矿山机器人收入占比高，后者军工资质稀缺...",
            height=100,
            help="你偏好的标的及逻辑",
        )

        non_consensus = st.text_area(
            "💡 非共识/差异化观点",
            placeholder="例：市场只关注地面机器人，但我认为今年无人机巡检的渗透率被严重低估，因为电力系统采购规模已超出预期...",
            height=80,
            help="你认为市场没有充分定价的观点",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            concerns = st.text_area(
                "⚠️ 主要顾虑",
                placeholder="例：最担心政策落地打折，历史上有过多次'规划强、执行弱'的情况...",
                height=80,
            )
        with col_b:
            timeframe = st.text_area(
                "📅 时间节奏判断",
                placeholder="例：认为 2025H2 才是真正的订单兑现窗口，现在布局是提前半年埋伏...",
                height=80,
            )

        analyst_views = {
            "catalyst": catalyst,
            "core_stocks": core_stocks,
            "non_consensus": non_consensus,
            "concerns": concerns,
            "timeframe": timeframe,
        }

        has_any_view = any(v.strip() for v in analyst_views.values())

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 操作按钮 ──────────────────────────────────────────────────
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            run_analysis = st.button(
                "🚀 运行完整分析",
                type="primary",
                use_container_width=True,
                disabled=not has_any_view,
                help="需要填写至少一项主观判断才能运行",
            )
        with col_btn2:
            load_existing = st.button(
                "📂 查看已有报告",
                use_container_width=True,
            )

    with col_right:
        # ── 报告显示区 ─────────────────────────────────────────────────

        # 已有报告选择
        r1_reports = list_reports(REPORTS_DIR, "*.md")
        r1_reports = [f for f in r1_reports
                      if "round1" in f.name or "特种机器人" in f.name or "robots" in f.name.lower()]

        if run_analysis:
            # 运行分析
            materials_files = sorted(MATERIALS_DIR.glob("research_materials_*.md"))
            if not materials_files:
                st.error("找不到素材文件，请先运行 Pass 1 素材采集。")
                st.code("python3.13 run_round1.py --pass 1")
            else:
                materials_file = materials_files[-1]
                st.info(f"使用素材：`{materials_file.name}`")

                if has_any_view:
                    st.markdown("**注入主观框架：**")
                    st.code(_build_analyst_block(analyst_views), language="markdown")

                status_placeholder = st.empty()

                with st.spinner("Claude Opus 正在分析（约 30-60 分钟）..."):
                    try:
                        output_file = run_pass2_with_analyst_view(
                            sector, analyst_views, materials_file, status_placeholder
                        )
                        if output_file:
                            st.success(f"分析完成！报告已保存：{output_file.name}")
                            content = read_report(output_file)
                            st.markdown(content, unsafe_allow_html=False)
                    except Exception as e:
                        st.error(f"分析失败：{e}")

        elif load_existing or True:  # 默认显示最新报告
            if r1_reports:
                # 报告选择器
                report_names = [f.name for f in r1_reports]
                selected_name = st.selectbox(
                    "选择报告",
                    report_names,
                    index=0,
                    label_visibility="collapsed",
                )
                selected_file = next(f for f in r1_reports if f.name == selected_name)

                # 元数据行
                mtime = datetime.fromtimestamp(selected_file.stat().st_mtime)
                content = read_report(selected_file)
                st.markdown(
                    f'<div style="display:flex;gap:8px;align-items:center;margin-bottom:12px;">'
                    f'<span class="badge badge-blue">行业研报</span>'
                    f'<span class="badge badge-gray">{mtime.strftime("%Y-%m-%d %H:%M")}</span>'
                    f'<span class="badge badge-gray">{len(content)//1000}k 字</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # 下载按钮
                st.download_button(
                    "⬇️ 下载报告",
                    data=content.encode("utf-8"),
                    file_name=selected_file.name,
                    mime="text/markdown",
                )

                # 渲染报告
                st.divider()
                st.markdown(content, unsafe_allow_html=False)
            else:
                st.markdown("""
                <div class="card" style="text-align:center;padding:40px;">
                  <div style="font-size:40px;margin-bottom:12px;">📭</div>
                  <div style="font-weight:600;color:#374151;">暂无行业报告</div>
                  <div style="color:#6b7280;font-size:13px;margin-top:8px;">
                    填写左侧主观框架后点击「运行完整分析」生成首份报告<br>
                    或先运行 <code>python3.13 run_round1.py</code>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────
# Tab 2：个股量化分析
# ──────────────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("<br>", unsafe_allow_html=True)

    col_left2, col_right2 = st.columns([1, 1.6], gap="large")

    with col_left2:
        st.markdown("""
        <div class="card" style="border-color: #7c3aed30; background: #faf5ff;">
          <div style="font-size: 15px; font-weight: 700; color: #5b21b6; margin-bottom: 4px;">⚡ 多智能体量化分析</div>
          <div style="font-size: 12px; color: #6b7280;">8 个 AI Agent 协作：技术面 · 基本面 · 新闻情绪 · 多空辩论 · 风险评估 · 交易决策</div>
        </div>
        """, unsafe_allow_html=True)

        ticker_input = st.text_input(
            "股票代码",
            value="601608",
            help="A股6位代码，如 601608（中信重工）",
        )

        date_input = st.date_input(
            "分析日期",
            value=datetime(2026, 3, 1).date(),
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Agent 流程说明
        st.markdown("**Agent 分析流程：**")
        agents = [
            ("📈", "市场技术分析师", "K线·均线·MACD·RSI"),
            ("📰", "新闻情绪分析师", "资讯·公告·市场情绪"),
            ("💼", "基本面分析师", "财报·估值·行业地位"),
            ("🐂🐻", "多空研究员辩论", "Bull vs Bear 论证"),
            ("🛡️", "三维风险评估", "市场·财务·操作风险"),
            ("💹", "交易员决策", "仓位·时机·止损"),
        ]
        for icon, name, detail in agents:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #f3f4f6;">'
                f'<span style="font-size:16px;">{icon}</span>'
                f'<div><div style="font-size:13px;font-weight:600;">{name}</div>'
                f'<div style="font-size:11px;color:#9ca3af;">{detail}</div></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        run_quant = st.button(
            "🚀 运行量化分析",
            type="primary",
            use_container_width=True,
            help="约需 15-30 分钟，调用 8 个 Claude Agent",
        )

    with col_right2:
        # 已有量化报告
        ta_reports = list_reports(TA_REPORTS_DIR, "claudecli_*.md")
        deep_reports = list_reports(REPORTS_DIR, "deep_*.md")
        quant_reports = ta_reports + deep_reports
        quant_reports.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        if run_quant:
            ticker = ticker_input.strip()
            date_str = date_input.strftime("%Y-%m-%d")

            st.info(f"开始分析 {ticker}（{date_str}）...")
            st.markdown(f"预计耗时 15-30 分钟，调用 `claude -p` 约 8 次")

            with st.spinner("量化 Agent 运行中..."):
                try:
                    env = os.environ.copy()
                    env.pop("CLAUDECODE", None)

                    result = subprocess.run(
                        ["python3.13", str(TRADING_ROOT / "run_demo_claudecli.py"), ticker, date_str],
                        capture_output=True,
                        text=True,
                        timeout=2400,
                        cwd=str(TRADING_ROOT),
                        env=env,
                    )

                    if result.returncode == 0:
                        st.success("分析完成！")
                        # 找新生成的报告
                        new_report = TA_REPORTS_DIR / f"claudecli_{ticker}_{date_str}.md"
                        if new_report.exists():
                            content = read_report(new_report)
                            st.markdown(content)
                        else:
                            st.text(result.stdout[-3000:])
                    else:
                        st.error(f"分析失败：{result.stderr[-500:]}")
                except subprocess.TimeoutExpired:
                    st.error("超时（40分钟），请重试")
                except Exception as e:
                    st.error(f"错误：{e}")

        elif quant_reports:
            report_names = [f.name for f in quant_reports]

            # 根据输入预选对应报告
            preselect = 0
            for i, f in enumerate(quant_reports):
                if ticker_input in f.name:
                    preselect = i
                    break

            selected_name = st.selectbox(
                "选择报告",
                report_names,
                index=preselect,
                label_visibility="collapsed",
            )
            selected_file = next(f for f in quant_reports if f.name == selected_name)
            content = read_report(selected_file)

            # 提取并显示关键决策
            decision = extract_decision(content)
            mtime = datetime.fromtimestamp(selected_file.stat().st_mtime)

            # 决策摘要卡片
            if decision["action"]:
                action_text = decision["action"]
                if "买" in action_text or "BUY" in action_text.upper():
                    signal_class = "signal-buy"
                    signal_icon = "📈"
                elif "卖" in action_text or "SELL" in action_text.upper():
                    signal_class = "signal-sell"
                    signal_icon = "📉"
                else:
                    signal_class = "signal-hold"
                    signal_icon = "➡️"

                col_d1, col_d2, col_d3, col_d4 = st.columns(4)
                with col_d1:
                    st.metric("交易信号", f"{signal_icon} {action_text[:4]}")
                with col_d2:
                    st.metric("目标价位", decision["price"] or "—")
                with col_d3:
                    st.metric("置信度", decision["confidence"] or "—")
                with col_d4:
                    st.metric("风险评分", decision["risk"] or "—")

            # 元数据 + 下载
            st.markdown(
                f'<div style="display:flex;gap:8px;align-items:center;margin:8px 0;">'
                f'<span class="badge badge-blue">量化分析</span>'
                f'<span class="badge badge-gray">{mtime.strftime("%Y-%m-%d %H:%M")}</span>'
                f'<span class="badge badge-gray">{selected_file.stem}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.download_button(
                "⬇️ 下载报告",
                data=content.encode("utf-8"),
                file_name=selected_file.name,
                mime="text/markdown",
            )

            st.divider()
            st.markdown(content, unsafe_allow_html=False)

        else:
            st.markdown("""
            <div class="card" style="text-align:center;padding:40px;">
              <div style="font-size:40px;margin-bottom:12px;">📭</div>
              <div style="font-weight:600;color:#374151;">暂无量化报告</div>
              <div style="color:#6b7280;font-size:13px;margin-top:8px;">
                点击「运行量化分析」生成首份报告<br>
                或运行 <code>python3.13 run_demo_claudecli.py 601608 2026-03-01</code>
              </div>
            </div>
            """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────
# Tab 3：综合投研决策
# ──────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("<br>", unsafe_allow_html=True)

    # 读取最新的行业报告和量化报告
    r1_latest = None
    r1_all = list_reports(REPORTS_DIR, "*.md")
    r1_all = [f for f in r1_all
              if "round1" in f.name or "特种机器人" in f.name or "robots" in f.name.lower()]
    if r1_all:
        r1_latest = r1_all[0]

    ta_all = list_reports(TA_REPORTS_DIR, "claudecli_*.md")
    deep_all = list_reports(REPORTS_DIR, "deep_*.md")
    quant_all = ta_all + deep_all
    quant_all.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        st.markdown("**选择行业研报（主观层）**")
        if r1_all:
            r1_sel = st.selectbox("行业研报", [f.name for f in r1_all], label_visibility="collapsed")
            r1_latest = next(f for f in r1_all if f.name == r1_sel)
    with col_sel2:
        st.markdown("**选择个股量化报告（执行层）**")
        if quant_all:
            q_sel = st.selectbox("量化报告", [f.name for f in quant_all], label_visibility="collapsed")
            quant_latest = next(f for f in quant_all if f.name == q_sel)
        else:
            quant_latest = None

    st.markdown("<br>", unsafe_allow_html=True)

    if not r1_latest and not quant_latest:
        st.info("请先在「行业主观研究」和「个股量化分析」两个 Tab 中生成报告，然后回到此处查看综合视图。")
    else:
        # ── 综合决策摘要 ──────────────────────────────────────────────
        st.markdown("""
        <div style="font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 16px;">
          📋 投研决策综合视图
        </div>
        """, unsafe_allow_html=True)

        col_layer1, col_layer2 = st.columns(2, gap="large")

        with col_layer1:
            st.markdown("""
            <div style="font-size: 13px; font-weight: 700; color: #1a56db;
                        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
              🧠 主观层 — 行业研究结论
            </div>
            """, unsafe_allow_html=True)

            if r1_latest:
                r1_content = read_report(r1_latest)

                # 尝试提取第五节综合研判
                import re
                section5_match = re.search(
                    r"第五节[：:]?\s*综合研判(.*?)(?=\n##|\n---|\Z)",
                    r1_content,
                    re.DOTALL
                )
                if section5_match:
                    section5 = section5_match.group(1).strip()[:2000]
                    st.markdown(f"**综合研判摘要：**\n\n{section5}...")
                else:
                    # 显示末尾汇总表部分
                    table_match = re.search(r"\|.+?\|.+?\|.+?\|.+?\|", r1_content)
                    if table_match:
                        table_start = r1_content.rfind("\n\n", 0, table_match.start())
                        st.markdown(r1_content[max(0, table_start):table_start+1500])
                    else:
                        # 显示最后 1000 字
                        st.markdown(r1_content[-1000:])

                st.download_button(
                    "⬇️ 下载完整行业报告",
                    data=r1_content.encode("utf-8"),
                    file_name=r1_latest.name,
                    mime="text/markdown",
                    key="dl_r1_tab3",
                )
            else:
                st.markdown('<div class="card" style="text-align:center;color:#9ca3af;">暂无行业报告</div>', unsafe_allow_html=True)

        with col_layer2:
            st.markdown("""
            <div style="font-size: 13px; font-weight: 700; color: #5b21b6;
                        text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">
              ⚡ 量化层 — 个股执行信号
            </div>
            """, unsafe_allow_html=True)

            if quant_latest:
                q_content = read_report(quant_latest)
                decision = extract_decision(q_content)

                # 决策卡片
                if decision["action"]:
                    action = decision["action"]
                    if "买" in action or "BUY" in action.upper():
                        bg, color = "#d1fae5", "#065f46"
                        icon = "📈"
                    elif "卖" in action or "SELL" in action.upper():
                        bg, color = "#fee2e2", "#991b1b"
                        icon = "📉"
                    else:
                        bg, color = "#fff7ed", "#9a3412"
                        icon = "➡️"

                    st.markdown(
                        f'<div style="background:{bg};border-radius:10px;padding:20px;text-align:center;margin-bottom:16px;">'
                        f'<div style="font-size:36px;margin-bottom:4px;">{icon}</div>'
                        f'<div style="font-size:22px;font-weight:800;color:{color};">{action}</div>'
                        f'<div style="font-size:13px;color:{color};margin-top:6px;">'
                        f'目标价 {decision["price"] or "—"} &nbsp;|&nbsp; 置信度 {decision["confidence"] or "—"} &nbsp;|&nbsp; 风险 {decision["risk"] or "—"}'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

                # 展示决策依据
                if decision.get("reasoning"):
                    st.markdown(f"**决策依据：**\n\n{decision['reasoning']}...")
                else:
                    # fallback: 找最终决策段落
                    final_section = re.search(
                        r"(?:建议：卖出|建议：买入|建议：持有)(.*?)(?=\n##|\n---|\Z)",
                        q_content,
                        re.DOTALL | re.IGNORECASE,
                    )
                    if final_section:
                        st.markdown(final_section.group(1).strip()[:1500])
                    else:
                        st.markdown(q_content[-1000:])

                st.download_button(
                    "⬇️ 下载完整量化报告",
                    data=q_content.encode("utf-8"),
                    file_name=quant_latest.name,
                    mime="text/markdown",
                    key="dl_q_tab3",
                )
            else:
                st.markdown('<div class="card" style="text-align:center;color:#9ca3af;">暂无量化报告</div>', unsafe_allow_html=True)

        # ── 方法论说明 ─────────────────────────────────────────────────
        st.divider()
        st.markdown("""
        **方法论说明：主观 × 量化如何结合**

        | 层次 | 解决什么问题 | 工具 | 输出 |
        |------|-------------|------|------|
        | 🧠 主观层（行业研究）| **选什么赛道、选什么股** | 研究员 + Claude Opus | 行业研报：纯度筛选 · 产业链 · 催化剂 · 推荐标的 |
        | ⚡ 量化层（个股分析）| **什么时候买、买多少、止损在哪** | 8 Agent · Claude CLI | 交易信号：技术面 · 基本面 · 情绪 · 风险评分 · 目标价 |
        | 🔗 整合逻辑 | 两层互相验证，减少单一视角偏差 | — | 主观选股 + 量化择时 = 完整投研闭环 |

        > **核心价值**：研究员的判断给 AI 锚定方向，AI 的数据验证帮研究员规避认知偏差。不是替代判断，而是加速验证。
        """)
