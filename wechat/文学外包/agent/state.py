"""
Manuscript lifecycle state management.
Tracks each manuscript from OPPORTUNITY_MATCHED to ARCHIVED with JSONL persistence.

Manuscript lifecycle is different from Article lifecycle:
- Article: IDEA → RESEARCHING → WRITING → PUBLISHED
- Manuscript: OPPORTUNITY → TOPIC → MATERIALS → GOLDLINE → WRITING → DRAFT → SUBMISSION → TRACKING → LEARNING
"""

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ManuscriptStatus(str, Enum):
    OPPORTUNITY_MATCHED = "OPPORTUNITY_MATCHED"  # Agent 发现匹配的征文机会
    TOPIC_PROPOSED = "TOPIC_PROPOSED"            # 选题方案已提出（等用户确认）
    MATERIAL_GATHERING = "MATERIAL_GATHERING"    # 采集素材中
    GOLDLINE_READY = "GOLDLINE_READY"            # 金线压缩完成（等用户确认意象）
    WRITING = "WRITING"                          # Pass 1-3 展开写作中
    DRAFT_READY = "DRAFT_READY"                  # 终稿完成（等用户审阅）
    REVISION = "REVISION"                        # 用户要求修改（Agent 修改中）
    SUBMISSION_READY = "SUBMISSION_READY"         # 邮件草稿已生成（等用户审核+发送）
    SUBMITTED = "SUBMITTED"                      # 已投出
    TRACKING = "TRACKING"                        # 等待结果
    RESULT_IN = "RESULT_IN"                      # 收到结果（采用/拒稿）
    LEARNING = "LEARNING"                        # 分析结果，压缩经验
    ARCHIVED = "ARCHIVED"                        # 归档


# What the agent is waiting for at each status
AWAITING = {
    ManuscriptStatus.TOPIC_PROPOSED: "user_confirm",
    ManuscriptStatus.GOLDLINE_READY: "user_confirm",
    ManuscriptStatus.DRAFT_READY: "user_review",
    ManuscriptStatus.SUBMISSION_READY: "user_send",
    ManuscriptStatus.RESULT_IN: "user_input",
}


class Manuscript:
    """A single manuscript in the literary pipeline."""

    def __init__(self, id: str, title: str = "", venue: str = "",
                 genre: str = "散文", work_dir: str = "",
                 materials_dir: str = "", opportunity: str = "",
                 word_count: str = ""):
        self.id = id
        self.title = title
        self.venue = venue              # 目标刊物
        self.genre = genre
        self.work_dir = work_dir        # 作品目录
        self.materials_dir = materials_dir
        self.opportunity = opportunity  # 征文机会描述
        self.word_count = word_count
        self.status = ManuscriptStatus.OPPORTUNITY_MATCHED
        self.created = datetime.now().isoformat()
        self.updated = datetime.now().isoformat()
        self.awaiting: Optional[str] = None
        self.history: list[str] = [f"OPPORTUNITY_MATCHED@{datetime.now().strftime('%H:%M')}"]
        self.goldline: str = ""         # 金线（Pass 0 输出）
        self.core_image: str = ""       # 核心意象
        self.revision_notes: str = ""   # 用户的修改意见
        self.submission_id: str = ""    # submissions.jsonl 中的 ID
        self.result: str = ""           # 采用/拒稿

    def transition(self, new_status: ManuscriptStatus):
        self.status = new_status
        self.updated = datetime.now().isoformat()
        self.history.append(f"{new_status.value}@{datetime.now().strftime('%H:%M')}")
        self.awaiting = AWAITING.get(new_status)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "venue": self.venue,
            "genre": self.genre,
            "work_dir": self.work_dir,
            "materials_dir": self.materials_dir,
            "opportunity": self.opportunity,
            "word_count": self.word_count,
            "status": self.status.value,
            "created": self.created,
            "updated": self.updated,
            "awaiting": self.awaiting,
            "history": self.history,
            "goldline": self.goldline,
            "core_image": self.core_image,
            "revision_notes": self.revision_notes,
            "submission_id": self.submission_id,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Manuscript":
        m = cls(
            id=d["id"],
            title=d.get("title", ""),
            venue=d.get("venue", ""),
            genre=d.get("genre", "散文"),
            work_dir=d.get("work_dir", ""),
            materials_dir=d.get("materials_dir", ""),
            opportunity=d.get("opportunity", ""),
            word_count=d.get("word_count", ""),
        )
        m.status = ManuscriptStatus(d["status"])
        m.created = d.get("created", "")
        m.updated = d.get("updated", "")
        m.awaiting = d.get("awaiting")
        m.history = d.get("history", [])
        m.goldline = d.get("goldline", "")
        m.core_image = d.get("core_image", "")
        m.revision_notes = d.get("revision_notes", "")
        m.submission_id = d.get("submission_id", "")
        m.result = d.get("result", "")
        return m

    def summary(self) -> str:
        title_part = self.title or self.id
        venue_part = f" → {self.venue}" if self.venue else ""
        return f"[{self.status.value}] {title_part}{venue_part} ({self.genre})"


class ManuscriptStateManager:
    """JSONL persistence for manuscripts."""

    def __init__(self, state_file: str):
        self.state_file = Path(state_file).expanduser()
        self.manuscripts: dict[str, Manuscript] = {}
        self._load()

    def _load(self):
        if not self.state_file.exists():
            return
        with open(self.state_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                m = Manuscript.from_dict(d)
                self.manuscripts[m.id] = m

    def _save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            for m in self.manuscripts.values():
                f.write(json.dumps(m.to_dict(), ensure_ascii=False) + "\n")

    def add_manuscript(self, manuscript: Manuscript) -> Manuscript:
        self.manuscripts[manuscript.id] = manuscript
        self._save()
        return manuscript

    def update_status(self, manuscript_id: str, new_status: ManuscriptStatus):
        if manuscript_id not in self.manuscripts:
            raise KeyError(f"Manuscript {manuscript_id} not found")
        self.manuscripts[manuscript_id].transition(new_status)
        self._save()

    def update_field(self, manuscript_id: str, **kwargs):
        """Update arbitrary fields on a manuscript."""
        if manuscript_id not in self.manuscripts:
            raise KeyError(f"Manuscript {manuscript_id} not found")
        m = self.manuscripts[manuscript_id]
        for k, v in kwargs.items():
            if hasattr(m, k):
                setattr(m, k, v)
        m.updated = datetime.now().isoformat()
        self._save()

    def get_manuscript(self, manuscript_id: str) -> Optional[Manuscript]:
        return self.manuscripts.get(manuscript_id)

    def get_active(self) -> list[Manuscript]:
        """Manuscripts not yet ARCHIVED."""
        return [m for m in self.manuscripts.values()
                if m.status != ManuscriptStatus.ARCHIVED]

    def get_awaiting_user(self) -> list[Manuscript]:
        """Manuscripts waiting for user input."""
        return [m for m in self.manuscripts.values() if m.awaiting is not None]

    def get_by_status(self, status: ManuscriptStatus) -> list[Manuscript]:
        return [m for m in self.manuscripts.values() if m.status == status]

    def status_summary(self) -> str:
        """Markdown summary for Brain context."""
        active = self.get_active()
        if not active:
            return "没有正在进行的稿件。"
        lines = []
        for m in active:
            wait = f" (等待: {m.awaiting})" if m.awaiting else ""
            lines.append(f"- {m.summary()}{wait}")
        return "\n".join(lines)
