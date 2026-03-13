"""
Brain: ReAct reasoning engine.
Given state + memory + signals → decide next action.
Each think() call is stateless — all context injected via prompt.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("agent.brain")


class BrainAction:
    """Result of a think() cycle."""
    def __init__(self, skill: str, params: dict, reason: str, priority: int = 0):
        self.skill = skill       # skill name to invoke
        self.params = params     # skill parameters
        self.reason = reason     # why this action
        self.priority = priority # 0=normal, 1=high, 2=urgent

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "params": self.params,
            "reason": self.reason,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "BrainAction":
        return cls(
            skill=d.get("skill", "idle"),
            params=d.get("params", {}),
            reason=d.get("reason", ""),
            priority=d.get("priority", 0),
        )

    @classmethod
    def idle(cls, reason: str = "没有需要处理的事项") -> "BrainAction":
        return cls(skill="idle", params={}, reason=reason)


class Brain:
    def __init__(self, config: dict, axioms_path: str):
        self.config = config
        self.backend = config.get("brain", {}).get("backend", "cli")
        self.think_model = config.get("brain", {}).get("think_model", "haiku")
        self.max_tokens = config.get("budget", {}).get("single_think_max_tokens", 2000)

        # Load axioms
        axioms_file = Path(axioms_path).expanduser()
        self.axioms = axioms_file.read_text() if axioms_file.exists() else ""

        # Budget tracking (resets daily)
        self.think_count = 0
        self.think_limit = config.get("budget", {}).get("daily_think_limit", 50)
        self.last_reset = datetime.now().date()

    def _check_budget(self) -> bool:
        today = datetime.now().date()
        if today != self.last_reset:
            self.think_count = 0
            self.last_reset = today
        return self.think_count < self.think_limit

    # ── Intent classification ─────────────────────────────────
    # Subclass can override INTENT_KEYWORDS to add domain-specific intents.
    # "general" is the fallback — keep its keyword list empty.
    INTENT_KEYWORDS: dict[str, list[str]] = {
        "general": [],
    }

    def _classify_intent(self, signals: list[dict]) -> str:
        """Keyword-based intent classification. No LLM call, pure string match."""
        text = " ".join(s.get("content", "") for s in signals)
        for intent, keywords in self.INTENT_KEYWORDS.items():
            if intent == "general":
                continue
            if any(kw in text for kw in keywords):
                return intent
        return "general"

    # ── Prompt building ────────────────────────────────────────

    def _build_prompt(self, state_summary: str, memory_summary: str,
                      signals: list[dict], skills_desc: str,
                      intent: str = "general",
                      chat_history: str = "") -> str:
        signals_md = "\n".join(
            f"- [{s.get('type', '?')}] {s.get('content', '')}"
            for s in signals
        ) if signals else "无新信号。"

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        return f"""# 你的身份

你是公众号「先驱者」的项目经理 Agent。当前时间：{now}

# 你的公理

{self.axioms}

# 当前文章状态

{state_summary}

# 最近行动路径

{memory_summary}

# 新信号

{signals_md}

# 可用技能

{skills_desc}

# 指令

根据上述信息，决定你的下一步行动。

输出严格 JSON（不要 markdown 代码块）：
{{"skill": "技能名", "params": {{}}, "reason": "一句话理由", "priority": 0}}

如果当前没有需要处理的事项，输出：
{{"skill": "idle", "params": {{}}, "reason": "原因", "priority": 0}}

注意：
- 如果有文章等待用户审核（awaiting=user_review），不要催促，等用户回复
- 如果有新的用户消息/链接，优先处理
- 如果空闲且有选题储备不足，考虑 select_topic
- priority: 0=普通, 1=高（用户主动发消息）, 2=紧急（发布失败等）
"""

    def think(self, state_summary: str, memory_summary: str,
              signals: list[dict], skills_desc: str,
              chat_history: str = "") -> BrainAction:
        """One reasoning step. Stateless — all context in params."""
        if not self._check_budget():
            logger.warning("Daily think budget exhausted (%d/%d)",
                           self.think_count, self.think_limit)
            return BrainAction.idle("今日推理次数已达上限，进入休眠。")

        intent = self._classify_intent(signals)
        prompt = self._build_prompt(state_summary, memory_summary,
                                     signals, skills_desc, intent=intent,
                                     chat_history=chat_history)
        logger.info("Brain think: intent=%s, prompt_len=%d chars", intent, len(prompt))

        try:
            result = self._call_llm(prompt)
            self.think_count += 1
            return self._parse_action(result)
        except subprocess.TimeoutExpired:
            logger.error("Brain think timeout (intent=%s, prompt_len=%d)", intent, len(prompt))
            return BrainAction.idle("推理超时，请重试。")
        except Exception as e:
            # Truncate error — never leak full prompt into reason
            err_msg = str(e)[:200]
            logger.error("Brain think error: %s", err_msg)
            return BrainAction.idle(f"推理出错: {err_msg}")

    def _call_llm(self, prompt: str) -> str:
        if self.backend == "cli":
            return self._call_cli(prompt)
        else:
            return self._call_api(prompt)

    @staticmethod
    def _clean_env() -> dict:
        """Get env dict that allows nested claude -p calls."""
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        return env

    def _call_cli(self, prompt: str) -> str:
        """Call claude -p CLI."""
        cmd = [
            "claude", "-p", prompt,
            "--model", self.think_model,
            "--output-format", "text",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            env=self._clean_env(),
        )
        if result.returncode != 0:
            raise RuntimeError(f"claude -p failed: {result.stderr[:200]}")
        return result.stdout.strip()

    def _call_api(self, prompt: str) -> str:
        """Call Anthropic API directly. Placeholder for future."""
        raise NotImplementedError("API backend not yet implemented. Use 'cli'.")

    def _parse_action(self, raw: str) -> BrainAction:
        """Parse LLM output to BrainAction."""
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        text = text.strip()

        try:
            d = json.loads(text)
            return BrainAction.from_dict(d)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    d = json.loads(text[start:end])
                    return BrainAction.from_dict(d)
                except json.JSONDecodeError:
                    pass
            logger.warning("Failed to parse Brain output: %s", text[:200])
            return BrainAction.idle(f"输出解析失败: {text[:100]}")
