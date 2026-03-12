"""
Path-based memory system.
Stores action paths (not conclusions), compresses experience over time.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class PathRecord:
    """A single action path: goal → steps → outcome → compression."""
    def __init__(self, goal: str, steps: list[dict] = None,
                 outcome: dict = None, compression: str = ""):
        self.timestamp = datetime.now().isoformat()
        self.goal = goal
        self.steps = steps or []
        self.outcome = outcome or {}
        self.compression = compression

    def add_step(self, step: str, result: str = "", duration: str = ""):
        self.steps.append({
            "step": step,
            "result": result,
            "duration": duration,
            "time": datetime.now().strftime("%H:%M"),
        })

    def set_outcome(self, outcome: dict, compression: str = ""):
        self.outcome = outcome
        self.compression = compression

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "goal": self.goal,
            "path": self.steps,
            "outcome": self.outcome,
            "compression": self.compression,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PathRecord":
        rec = cls(goal=d.get("goal", ""))
        rec.timestamp = d.get("timestamp", "")
        rec.steps = d.get("path", [])
        rec.outcome = d.get("outcome", {})
        rec.compression = d.get("compression", "")
        return rec


class MemoryManager:
    def __init__(self, paths_file: str, experience_file: str = None):
        self.paths_file = Path(paths_file).expanduser()
        self.experience_file = Path(experience_file).expanduser() if experience_file else None
        self.paths_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_path: Optional[PathRecord] = None

    def save_path(self, record: PathRecord):
        with open(self.paths_file, "a") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def recent_paths(self, n: int = 5) -> list[PathRecord]:
        """Read last N path records."""
        if not self.paths_file.exists():
            return []
        records = []
        with open(self.paths_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(PathRecord.from_dict(json.loads(line)))
        return records[-n:]

    def recent_paths_markdown(self, n: int = 5) -> str:
        """Format recent paths as markdown for Brain context."""
        paths = self.recent_paths(n)
        if not paths:
            return "暂无历史路径记录。"
        lines = []
        for p in paths:
            steps_str = " → ".join(s.get("step", "?") for s in p.steps)
            comp = f"\n  压缩: {p.compression}" if p.compression else ""
            lines.append(f"- [{p.timestamp[:10]}] {p.goal}: {steps_str}{comp}")
        return "\n".join(lines)

    def load_experience(self) -> list[dict]:
        """Load experience.jsonl (cross-series rules)."""
        if not self.experience_file or not self.experience_file.exists():
            return []
        records = []
        with open(self.experience_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records

    def experience_summary(self, n: int = 10) -> str:
        """Recent experience rules as markdown."""
        exps = self.load_experience()
        if not exps:
            return "暂无经验记录。"
        recent = exps[-n:]
        lines = []
        for e in recent:
            rule = e.get("rule", e.get("insight", ""))
            source = e.get("source", "")
            lines.append(f"- {rule}" + (f" (来源: {source})" if source else ""))
        return "\n".join(lines)

    def start_path(self, goal: str) -> PathRecord:
        """Begin tracking a new action path."""
        self.current_path = PathRecord(goal=goal)
        return self.current_path

    def finish_path(self, outcome: dict = None, compression: str = ""):
        """Complete and persist the current path."""
        if self.current_path:
            self.current_path.set_outcome(outcome or {}, compression)
            self.save_path(self.current_path)
            result = self.current_path
            self.current_path = None
            return result
        return None
