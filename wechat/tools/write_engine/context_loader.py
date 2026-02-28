#!/usr/bin/env python3
"""
上下文加载器 — 为每个 Pass 组装所需的上下文。

职责：读取方法论、人设、经验库、系列经验、素材，按 Pass 需求裁剪后返回。

v2: 新增共享上下文层 + Pass 3.5 协商闭环所需的 assemble 方法。
"""

import json
import re
from pathlib import Path
from datetime import datetime


class ContextLoader:
    """加载写作引擎所需的各类上下文。"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.wechat_dir = project_root / "wechat"

    # ── 基础加载方法 ────────────────────────────────────

    def load_methodology(self) -> str:
        """读取完整内容方法论。"""
        path = self.wechat_dir / "内容方法论.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def load_methodology_section(self, section_name: str) -> str:
        """提取方法论中的特定章节。按 ## 标题切分。"""
        full = self.load_methodology()
        if not full:
            return ""
        sections = full.split("\n## ")
        for s in sections:
            if s.startswith(section_name) or s.startswith(f" {section_name}"):
                return f"## {s}"
        return ""

    def load_persona(self, name: str) -> str:
        """读取人设档案。"""
        path = self.wechat_dir / "人设" / f"{name}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return f"（未找到人设档案：{name}）"

    def load_experience(self, max_entries: int = 20) -> str:
        """读取经验库最近 N 条。"""
        path = self.wechat_dir / "experience.jsonl"
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        recent = lines[-max_entries:]
        result = []
        for line in recent:
            try:
                entry = json.loads(line)
                lesson = entry.get("lesson") or entry.get("rule", "")
                tags = entry.get("tags", [])
                source = entry.get("source", "")
                result.append(f"- [{', '.join(tags)}] {lesson}（来源：{source}）")
            except json.JSONDecodeError:
                continue
        return "\n".join(result) if result else ""

    def load_series_lessons(self, series_name: str) -> str:
        """读取系列级经验。"""
        if not series_name:
            return ""
        path = self.wechat_dir / "公众号已发" / series_name / "lessons.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    def load_series_articles_summary(self, series_name: str) -> str:
        """读取系列已发文章的标题和开头，用于续恰。"""
        if not series_name:
            return "（独立篇，无系列对比）"
        series_dir = self.wechat_dir / "公众号已发" / series_name
        if not series_dir.exists():
            return ""
        result = []
        for md_file in sorted(series_dir.glob("*.md")):
            if md_file.name in ("lessons.md",) or md_file.name.endswith("-metrics.md"):
                continue
            content = md_file.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            preview = "\n".join(lines[:10])
            result.append(f"### {md_file.name}\n{preview}\n")
        return "\n".join(result) if result else "（暂无已发文章）"

    def load_materials(self, topic_dir: Path) -> str:
        """读取选题目录下的所有素材。"""
        materials_dir = topic_dir / "素材"
        if not materials_dir.exists():
            materials_dir = topic_dir

        result = []
        for md_file in sorted(materials_dir.rglob("*.md")):
            if md_file.name.startswith("article") or md_file.name.startswith("iteration_") or md_file.name in (
                "poll.md", "publish_guide.md", "review_report.md",
                "factcheck_report.md", "consensus.md",
                "verification_report.md", "description_options.md",
                "consensus_doc.md", "orphaned_recommendations.md",
            ):
                continue
            content = md_file.read_text(encoding="utf-8")
            result.append(f"\n--- 素材：{md_file.name} ---\n{content}")

        return "\n".join(result) if result else "（未找到素材文件）"

    # ── 共享上下文层 ────────────────────────────────────

    def load_materials_summary(self, topic_dir: Path, max_chars: int = 3000) -> str:
        """提取 deep_research.md 的核心段落（核心事实/时间线/数据表），截断到 max_chars。"""
        dr_path = topic_dir / "素材" / "deep_research.md"
        if not dr_path.exists():
            # fallback: 如果没有 deep_research.md，从所有素材取摘要
            materials = self.load_materials(topic_dir)
            if materials and len(materials) > max_chars:
                return materials[:max_chars] + "\n\n[...素材摘要已截断...]"
            return materials

        content = dr_path.read_text(encoding="utf-8")

        # 优先提取核心段落
        target_sections = ["核心事实", "时间线", "数据表", "关键数据", "多方观点", "争议点"]
        extracted = []
        current_section = None
        current_lines = []

        for line in content.split("\n"):
            if line.startswith("## ") or line.startswith("### "):
                # 保存上一段
                if current_section and any(kw in current_section for kw in target_sections):
                    extracted.append(f"{current_section}\n" + "\n".join(current_lines))
                current_section = line
                current_lines = []
            else:
                current_lines.append(line)

        # 最后一段
        if current_section and any(kw in current_section for kw in target_sections):
            extracted.append(f"{current_section}\n" + "\n".join(current_lines))

        if extracted:
            summary = "\n\n".join(extracted)
        else:
            # 没有匹配的段落，取前 max_chars
            summary = content

        if len(summary) > max_chars:
            summary = summary[:max_chars] + "\n\n[...素材摘要已截断...]"

        return summary

    def load_persona_summary(self, name: str, max_lines: int = 50) -> str:
        """读取人设摘要（前 max_lines 行），用于共享上下文。"""
        full = self.load_persona(name)
        lines = full.strip().split("\n")
        if len(lines) <= max_lines:
            return full
        return "\n".join(lines[:max_lines]) + "\n\n[...人设摘要已截断...]"

    def load_methodology_core(self, max_chars: int = 2000) -> str:
        """提取方法论核心：铁律 + 写作规则 + Review 铁律。"""
        full = self.load_methodology()
        if not full:
            return ""

        # 提取所有 🔺 铁律标记的段落
        iron_rules = []
        for line in full.split("\n"):
            if "🔺" in line:
                iron_rules.append(line.strip())

        # 提取关键段落
        key_sections = []
        section_names = ["结构与叙事规则", "排版与风格规则", "技术圈表述红线"]
        for sname in section_names:
            section = self.load_methodology_section(sname)
            if section:
                # 只取前几行作为摘要
                lines = section.strip().split("\n")
                key_sections.append("\n".join(lines[:15]))

        parts = []
        if iron_rules:
            parts.append("### 铁律\n" + "\n".join(iron_rules))
        if key_sections:
            parts.append("\n".join(key_sections))

        result = "\n\n".join(parts)
        if len(result) > max_chars:
            result = result[:max_chars] + "\n\n[...方法论摘要已截断...]"

        return result

    def load_review_checklist(self) -> str:
        """从内容方法论.md 提取完整 Review checklist。

        提取 '🔺 **Review 铁律' 开始到该 blockquote 结束的内容，
        加上 '自我 Review 框架：三层恰' 段落。
        """
        full = self.load_methodology()
        if not full:
            return ""

        parts = []

        # 1. 提取 Review 铁律 blockquote
        in_review_blockquote = False
        review_lines = []
        for line in full.split("\n"):
            if "Review 铁律" in line and "🔺" in line:
                in_review_blockquote = True
                review_lines.append(line)
                continue
            if in_review_blockquote:
                if line.startswith("> ") or line.strip() == ">":
                    review_lines.append(line)
                elif line.strip() == "":
                    # 空行可能在 blockquote 内
                    review_lines.append(line)
                else:
                    # blockquote 结束
                    break

        if review_lines:
            parts.append("\n".join(review_lines))

        # 2. 提取三层恰框架
        three_layer = self.load_methodology_section("自我 Review 框架：三层恰")
        if three_layer:
            parts.append(three_layer)

        return "\n\n".join(parts) if parts else ""

    def load_competitor_articles(self, topic_dir: Path, max_chars_per_article: int = 500,
                                  max_total_chars: int = 5000) -> str:
        """读取素材中其他公众号文章摘要，用于 Pass 3 他恰对比。

        读取 素材/{公众号名}/ 下所有 md 文件，每篇取标题 + 前 max_chars_per_article 字符。
        """
        materials_dir = topic_dir / "素材"
        if not materials_dir.exists():
            return "（未找到竞品文章素材）"

        result = []
        total_chars = 0

        for subdir in sorted(materials_dir.iterdir()):
            if not subdir.is_dir():
                continue
            # 跳过非公众号目录（如 英文源）
            if subdir.name in ("英文源", "en_sources"):
                continue

            source_name = subdir.name
            for md_file in sorted(subdir.glob("*.md")):
                if total_chars >= max_total_chars:
                    break
                content = md_file.read_text(encoding="utf-8")
                # 提取标题
                title = md_file.stem
                lines = content.strip().split("\n")
                for line in lines:
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                # 取摘要
                summary = content[:max_chars_per_article]
                if len(content) > max_chars_per_article:
                    summary += "\n[...已截断...]"

                entry = f"### 来源：{source_name}\n**{title}**\n{summary}\n"
                result.append(entry)
                total_chars += len(entry)

            if total_chars >= max_total_chars:
                result.append("\n[...更多竞品文章已省略...]")
                break

        return "\n".join(result) if result else "（未找到竞品文章素材）"

    def build_shared_context(self, topic_dir: Path, persona_name: str) -> str:
        """构建所有 Pass 共享的上下文层。

        包含：素材摘要 + 人设摘要 + 方法论核心 + 经验库最近10条。
        总共约 6-7k chars。
        """
        parts = []

        # 素材摘要
        materials_summary = self.load_materials_summary(topic_dir)
        if materials_summary:
            parts.append(f"## 素材摘要\n\n{materials_summary}")

        # 人设摘要
        persona_summary = self.load_persona_summary(persona_name)
        if persona_summary:
            parts.append(f"## 执笔人设摘要\n\n{persona_summary}")

        # 方法论核心
        methodology_core = self.load_methodology_core()
        if methodology_core:
            parts.append(f"## 方法论核心\n\n{methodology_core}")

        # 经验库（最近10条）
        experience = self.load_experience(max_entries=10)
        if experience:
            parts.append(f"## 经验库（最近10条）\n\n{experience}")

        return "\n\n---\n\n".join(parts) if parts else ""

    # ── Pass 1-4 上下文组装 ────────────────────────────

    def assemble_pass1_context(self, topic_dir: Path, persona_name: str,
                                series_name: str = None) -> dict:
        """组装 Pass 1 写作Agent 所需的全部上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "PERSONA": self.load_persona(persona_name),
            "PERSONA_NAME": persona_name,
            "DATE": datetime.now().strftime("%Y-%m-%d"),
            "EXPERIENCE": self.load_experience(),
            "SERIES_LESSONS": self.load_series_lessons(series_name),
            "MATERIALS": self.load_materials(topic_dir),
        }

    def assemble_pass2_context(self, topic_dir: Path, article_draft: str,
                                persona_name: str) -> dict:
        """组装 Pass 2 事实核查Agent 所需的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE_DRAFT": article_draft,
            "MATERIALS": self.load_materials(topic_dir),
        }

    def assemble_pass3_context(self, topic_dir: Path, article_factchecked: str,
                                persona_name: str, series_name: str = None) -> dict:
        """组装 Pass 3 审视Agent 所需的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE_FACTCHECKED": article_factchecked,
            "PERSONA": self.load_persona(persona_name),
            "EXPERIENCE": self.load_experience(),
            "SERIES_CONTEXT": self.load_series_articles_summary(series_name),
            "COMPETITOR_ARTICLES": self.load_competitor_articles(topic_dir),
            "REVIEW_CHECKLIST": self.load_review_checklist(),
        }

    def assemble_pass4_context(self, topic_dir: Path, article_draft: str,
                                factcheck_report: str, review_report: str,
                                latest_article: str, consensus_doc: str,
                                persona_name: str) -> dict:
        """组装 Pass 4 整合Agent 所需的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE_DRAFT": article_draft,
            "FACTCHECK_REPORT": factcheck_report,
            "REVIEW_REPORT": review_report,
            "CONSENSUS_DOC": consensus_doc,
            "LATEST_ARTICLE": latest_article,
        }

    # ── Pass 3.5 协商闭环上下文组装 ────────────────────

    def assemble_write_respond_context(self, topic_dir: Path, review_report: str,
                                        article_factchecked: str, consensus_doc: str,
                                        persona_name: str) -> dict:
        """组装 Writing Agent 回应 review 的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "REVIEW_REPORT": review_report,
            "ARTICLE_FACTCHECKED": article_factchecked,
            "CONSENSUS_DOC": consensus_doc,
            "PERSONA": self.load_persona(persona_name),
        }

    def assemble_fact_respond_context(self, topic_dir: Path, review_report: str,
                                       article_factchecked: str, consensus_doc: str,
                                       persona_name: str) -> dict:
        """组装 Fact Agent 回应 review 的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "REVIEW_REPORT": review_report,
            "ARTICLE_FACTCHECKED": article_factchecked,
            "CONSENSUS_DOC": consensus_doc,
            "MATERIALS": self.load_materials(topic_dir),
        }

    def assemble_consensus_evaluate_context(self, topic_dir: Path, review_report: str,
                                              article_factchecked: str,
                                              consensus_doc: str,
                                              persona_name: str) -> dict:
        """组装 Review Agent 评估所有回应的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "REVIEW_REPORT": review_report,
            "ARTICLE_FACTCHECKED": article_factchecked,
            "CONSENSUS_DOC": consensus_doc,
        }

    def assemble_revision_context(self, topic_dir: Path, article_factchecked: str,
                                    consensus_doc: str, persona_name: str) -> dict:
        """组装 Writing Agent 按共识执行写作类修改的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE_FACTCHECKED": article_factchecked,
            "CONSENSUS_DOC": consensus_doc,
            "PERSONA": self.load_persona(persona_name),
        }

    def assemble_fact_revision_context(self, topic_dir: Path, article_after_write_revision: str,
                                         consensus_doc: str, persona_name: str) -> dict:
        """组装 Fact Agent 按共识执行事实类修改的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE": article_after_write_revision,
            "CONSENSUS_DOC": consensus_doc,
            "MATERIALS": self.load_materials(topic_dir),
        }

    def assemble_verification_context(self, article_before: str, article_after: str,
                                        consensus_doc: str, change_list: str,
                                        topic_dir: Path, persona_name: str) -> dict:
        """组装 Review Agent 验收的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE_BEFORE": article_before,
            "ARTICLE_AFTER": article_after,
            "CONSENSUS_DOC": consensus_doc,
            "CHANGE_LIST": change_list,
        }

    # ── Pass 5 迭代求导上下文组装 ────────────────────────

    def assemble_pass5_weakness_context(self, topic_dir: Path, article: str,
                                         persona_name: str) -> dict:
        """组装 Pass 5a 证据硬度审计的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE": article,
            "MATERIALS": self.load_materials(topic_dir),
        }

    def assemble_pass5_research_context(self, topic_dir: Path, article: str,
                                          weakness: str, persona_name: str) -> dict:
        """组装 Pass 5b 定向调研的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE": article,
            "WEAKNESS_REPORT": weakness,
            "MATERIALS_SUMMARY": self.load_materials_summary(topic_dir),
        }

    def assemble_pass5_rewrite_context(self, topic_dir: Path, article: str,
                                         weakness: str, research: str,
                                         persona_name: str) -> dict:
        """组装 Pass 5c 定向重写的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE": article,
            "WEAKNESS_REPORT": weakness,
            "TARGETED_RESEARCH": research,
            "PERSONA": self.load_persona(persona_name),
        }

    def assemble_pass5_compare_context(self, topic_dir: Path, prev: str,
                                         curr: str, persona_name: str) -> dict:
        """组装 Pass 5d 版本对比的上下文。"""
        return {
            "SHARED_CONTEXT": self.build_shared_context(topic_dir, persona_name),
            "ARTICLE_PREV": prev,
            "ARTICLE_CURR": curr,
        }
