"""
Skill: 自干预 (Intervene)

Agent 修改自己域内的文件（数据/配置/代码）。
如果改了 agent/ 下的 .py 文件，标记需要重启。

4-Phase:
  1. 定位 (haiku)  — 用户指令 + 文件索引 → 识别需读取的文件
  2. 编辑 (sonnet) — 文件内容 + 用户指令 → 结构化编辑补丁
  3. 应用 (Python) — 写入文件 + 记录 interventions.jsonl
  4. 重启 (Python) — 如果改了 agent/*.py → 设置 .restart 标记

安全边界：只能修改 wechat/文学外包/ 下的文件。
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env

logger = logging.getLogger("editor.skills.intervene")

# File extensions we index and allow editing
ALLOWED_EXTENSIONS = {".py", ".md", ".yaml", ".yml", ".jsonl", ".json", ".txt"}

# Directories to skip when building file index
SKIP_DIRS = {"__pycache__", ".git", "logs", ".mypy_cache", ".pytest_cache", "node_modules"}


def _build_file_index(lit_root: Path) -> str:
    """Walk lit_root, return a compact file listing for the LLM."""
    lines = []
    for dirpath, dirnames, filenames in os.walk(lit_root):
        # Prune skipped dirs in-place
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        rel_dir = Path(dirpath).relative_to(lit_root)
        for fname in sorted(filenames):
            ext = Path(fname).suffix.lower()
            if ext in ALLOWED_EXTENSIONS:
                rel_path = rel_dir / fname
                lines.append(str(rel_path))
    return "\n".join(lines)


def _validate_path(lit_root: Path, rel_path: str) -> Path | None:
    """Resolve relative path under lit_root. Reject traversal attempts.

    Also handles the case where LLM returns a path with redundant prefix
    (e.g. 'wechat/文学外包/作品/...' when lit_root is already 'wechat/文学外包/').
    """
    # Try as-is first
    target = (lit_root / rel_path).resolve()
    try:
        target.relative_to(lit_root.resolve())
        if target.exists() or not target.suffix:  # exists or is a new file
            return target
    except ValueError:
        return None

    # If file doesn't exist, try stripping common prefixes that LLM may add
    # e.g. rel_path="wechat/文学外包/作品/x.md" when lit_root already ends with "wechat/文学外包"
    parts = Path(rel_path).parts
    for i in range(1, min(len(parts), 4)):
        shortened = str(Path(*parts[i:]))
        candidate = (lit_root / shortened).resolve()
        try:
            candidate.relative_to(lit_root.resolve())
            if candidate.exists():
                return candidate
        except ValueError:
            continue

    return target  # Return original (may not exist, Phase 3 will handle)


def _fix_unescaped_quotes(text: str) -> str:
    """Fix unescaped double quotes inside JSON string values.

    LLMs often produce JSON like: {"old": "要求"原创首发"的比赛"}
    where the inner " should be escaped as \\".

    Strategy: walk char by char, track whether we're inside a JSON string,
    and escape " that appear inside strings but aren't structural delimiters.
    A structural " is one preceded by : , [ { or followed by : , ] } or at string boundaries.
    """
    import re
    # Simpler approach: use regex to find string values and escape inner quotes
    # Pattern: match "key": "value" pairs, fixing value part
    result = []
    i = 0
    in_string = False
    string_start = -1
    escaped = False

    while i < len(text):
        c = text[i]

        if escaped:
            escaped = False
            i += 1
            continue

        if c == '\\':
            escaped = True
            i += 1
            continue

        if c == '"':
            if not in_string:
                in_string = True
                string_start = i
            else:
                # Is this the real end of the string?
                # Look ahead: after closing ", expect , : ] } or whitespace+one of those
                rest = text[i + 1:].lstrip()
                if not rest or rest[0] in ':,]}':
                    in_string = False
                else:
                    # This " is inside a string value — escape it
                    text = text[:i] + '\\"' + text[i + 1:]
                    i += 2  # skip the escaped quote
                    continue

        i += 1

    return text


class InterveneSkill(Skill):
    name = "intervene"
    description = "修改 Agent 域内的任意文件（数据/配置/代码），支持自动重启"
    estimated_duration = "30s"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        instruction = params.get("instruction", "")
        if not instruction:
            return SkillResult(False, "缺少 instruction 参数")

        lit_root = Path(config["paths"]["lit_root"]).expanduser().resolve()
        if not lit_root.exists():
            return SkillResult(False, f"lit_root 不存在: {lit_root}")

        # ── Phase 1: Locate files (haiku) ──────────────────────
        file_index = _build_file_index(lit_root)
        locate_prompt = (
            f"你是文件定位助手。用户要修改一些文件。\n\n"
            f"## 用户指令\n{instruction}\n\n"
            f"## 可用文件列表（相对于项目根目录）\n{file_index}\n\n"
            f"## 要求\n"
            f"输出严格 JSON（不要 markdown 代码块）：\n"
            f'{{"files": ["需要读取的文件相对路径1", "路径2", ...], '
            f'"reasoning": "一句话说明为什么需要这些文件"}}\n\n'
            f"严格最小化：只列出【必须读取才能完成编辑】的文件。\n"
            f"不要包含计划文件、文档文件、日志文件等参考性文件。\n"
            f"通常 1-2 个文件就够了，最多 3 个。"
        )

        try:
            locate_result = subprocess.run(
                ["claude", "-p", locate_prompt, "--model", "sonnet",
                 "--output-format", "text"],
                capture_output=True, text=True, timeout=60, env=_clean_env(),
            )
            if locate_result.returncode != 0:
                return SkillResult(False, f"Phase 1 失败: {locate_result.stderr[:300]}")

            locate_data = self._parse_json(locate_result.stdout.strip())
            if not locate_data or "files" not in locate_data:
                return SkillResult(False, f"Phase 1 解析失败: {locate_result.stdout[:300]}")

            target_files = locate_data["files"]
            logger.info("Phase 1: 定位 %d 个文件: %s", len(target_files), target_files)

        except subprocess.TimeoutExpired:
            return SkillResult(False, "Phase 1 超时")
        except Exception as e:
            return SkillResult(False, f"Phase 1 异常: {e}")

        # ── Phase 2: Generate edits (sonnet) ───────────────────
        # Read the identified files
        file_contents = {}
        for rel_path in target_files[:5]:
            abs_path = _validate_path(lit_root, rel_path)
            if abs_path and abs_path.exists() and abs_path.is_file():
                try:
                    content = abs_path.read_text(encoding="utf-8")
                    file_contents[rel_path] = content
                except Exception as e:
                    file_contents[rel_path] = f"[读取失败: {e}]"
            else:
                file_contents[rel_path] = "[文件不存在或路径非法]"

        files_section = ""
        for rel_path, content in file_contents.items():
            # Truncate very large files
            truncated = content[:8000]
            if len(content) > 8000:
                truncated += f"\n... (truncated, total {len(content)} chars)"
            files_section += f"\n### {rel_path}\n```\n{truncated}\n```\n"

        edit_prompt = (
            f"你是文件编辑助手。根据用户指令，生成精确的文本替换补丁。\n\n"
            f"## 用户指令\n{instruction}\n\n"
            f"## 当前文件内容\n{files_section}\n\n"
            f"## 要求\n"
            f"直接输出纯 JSON，不要任何 markdown 代码块或解释文字：\n"
            f'{{"understanding":"一句话","edits":[{{"file":"相对路径","old":"原文片段","new":"新片段"}}],"summary":"一句话","restart_needed":false}}\n\n'
            f"规则：\n"
            f'- old 必须是文件中实际存在的精确片段，尽量短（只包含需要替换的部分及少量上下文来确保唯一性）\n'
            f'- 如果修改了 agent/ 下的 .py 文件，restart_needed 设为 true\n'
            f'- 如果是新增内容，old 是插入点前的一小段文本，new 包含该文本+新增内容'
        )

        try:
            edit_result = subprocess.run(
                ["claude", "-p", edit_prompt, "--model", "sonnet",
                 "--output-format", "text"],
                capture_output=True, text=True, timeout=300, env=_clean_env(),
            )
            if edit_result.returncode != 0:
                return SkillResult(False, f"Phase 2 失败: {edit_result.stderr[:300]}")

            raw_output = edit_result.stdout.strip()
            # Debug: dump raw output for diagnosis
            debug_path = Path(config["paths"].get("logs_dir", "")).expanduser() / "intervene_debug.txt"
            debug_path.parent.mkdir(parents=True, exist_ok=True)
            debug_path.write_text(raw_output, encoding="utf-8")
            logger.info("Phase 2 raw output saved to %s (%d chars)", debug_path, len(raw_output))

            edit_data = self._parse_json(raw_output)
            if not edit_data or "edits" not in edit_data:
                return SkillResult(False, f"Phase 2 解析失败（详见 {debug_path}）")

            logger.info("Phase 2: %d 条编辑, summary=%s",
                        len(edit_data["edits"]), edit_data.get("summary", ""))

        except subprocess.TimeoutExpired:
            return SkillResult(False, "Phase 2 超时")
        except Exception as e:
            return SkillResult(False, f"Phase 2 异常: {e}")

        # ── Phase 3: Apply edits ───────────────────────────────
        edits = edit_data.get("edits", [])
        applied = []
        failed = []

        for edit in edits:
            rel_path = edit.get("file", "")
            old_text = edit.get("old", "")
            new_text = edit.get("new", "")

            if not rel_path or old_text == new_text:
                continue

            abs_path = _validate_path(lit_root, rel_path)
            if not abs_path:
                failed.append(f"{rel_path}: 路径非法（可能试图越界）")
                continue

            if not abs_path.exists():
                # Allow creating new files only within lit_root
                if new_text and not old_text:
                    try:
                        abs_path.parent.mkdir(parents=True, exist_ok=True)
                        abs_path.write_text(new_text, encoding="utf-8")
                        applied.append(f"{rel_path}: 新建文件")
                        continue
                    except Exception as e:
                        failed.append(f"{rel_path}: 创建失败 — {e}")
                        continue
                failed.append(f"{rel_path}: 文件不存在")
                continue

            try:
                content = abs_path.read_text(encoding="utf-8")
                if old_text not in content:
                    failed.append(f"{rel_path}: old 片段未找到")
                    continue

                # Apply replacement (first occurrence only)
                new_content = content.replace(old_text, new_text, 1)
                abs_path.write_text(new_content, encoding="utf-8")
                # Describe what changed
                short_old = old_text[:50].replace("\n", "\\n")
                short_new = new_text[:50].replace("\n", "\\n")
                applied.append(f"{rel_path}: \"{short_old}\" → \"{short_new}\"")
            except Exception as e:
                failed.append(f"{rel_path}: 写入失败 — {e}")

        # ── Phase 3b: Log intervention ─────────────────────────
        logs_dir = Path(config["paths"].get("logs_dir", "")).expanduser()
        if not logs_dir.exists():
            logs_dir = lit_root / "agent" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        intervention_log = logs_dir / "interventions.jsonl"
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": edit_data.get("summary", instruction[:100]),
            "target": ", ".join(e.get("file", "") for e in edits),
            "trigger": instruction[:200],
            "applied": len(applied),
            "failed": len(failed),
        }
        with open(intervention_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        # ── Build result ───────────────────────────────────────
        restart_needed = edit_data.get("restart_needed", False)

        lines = []
        if applied:
            lines.append(f"已修改 {len(applied)} 个文件:")
            for a in applied:
                lines.append(f"  {a}")
        if failed:
            lines.append(f"\n失败 {len(failed)} 项:")
            for f_msg in failed:
                lines.append(f"  {f_msg}")

        if not applied and not failed:
            return SkillResult(False, "没有可应用的编辑")

        summary = edit_data.get("summary", "编辑完成")
        message = f"{summary}\n\n" + "\n".join(lines)
        if restart_needed and applied:
            message += "\n\n代码已更新，需要重启生效。"

        return SkillResult(
            success=len(applied) > 0,
            message=message,
            data={
                "applied": applied,
                "failed": failed,
                "restart_needed": restart_needed and len(applied) > 0,
                "summary": summary,
            },
        )

    @staticmethod
    def _parse_json(raw: str) -> dict | None:
        """Parse JSON from LLM output, handling markdown fences and unescaped quotes."""
        text = raw.strip()

        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        if "```" in text:
            first = text.find("```")
            last = text.rfind("```")
            if first != last:
                inner = text[first:last]
                newline = inner.find("\n")
                text = inner[newline + 1:] if newline >= 0 else inner[3:]
            text = text.strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Find the outermost { ... }
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            candidate = text[start:end]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

            # LLM often leaves unescaped " inside JSON string values
            # (e.g. "要求"原创首发"" → should be "要求\"原创首发\"")
            # Fix: escape quotes that appear inside string values
            fixed = _fix_unescaped_quotes(candidate)
            try:
                return json.loads(fixed)
            except json.JSONDecodeError:
                pass

        return None
