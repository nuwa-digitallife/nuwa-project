"""
Article lifecycle state management.
Tracks each article from IDEA to ARCHIVED with JSONL persistence.
"""

import json
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ArticleStatus(str, Enum):
    IDEA = "IDEA"
    RESEARCHING = "RESEARCHING"
    OUTLINE_READY = "OUTLINE_READY"
    WRITING = "WRITING"
    DRAFT_READY = "DRAFT_READY"
    APPROVED = "APPROVED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    COLLECTING_METRICS = "COLLECTING_METRICS"
    LEARNING = "LEARNING"
    ARCHIVED = "ARCHIVED"


# What the agent is waiting for at each status
AWAITING = {
    ArticleStatus.OUTLINE_READY: "user_review",
    ArticleStatus.DRAFT_READY: "user_review",
    ArticleStatus.APPROVED: "agent_publish",
}


class Article:
    def __init__(self, id: str, persona: str, series: str = "独立篇",
                 topic_dir: str = "", url: str = "", instructions: str = ""):
        self.id = id
        self.persona = persona
        self.series = series
        self.topic_dir = topic_dir
        self.url = url
        self.instructions = instructions
        self.status = ArticleStatus.IDEA
        self.created = datetime.now().isoformat()
        self.updated = datetime.now().isoformat()
        self.awaiting: Optional[str] = None
        self.history: list[str] = [f"IDEA@{datetime.now().strftime('%H:%M')}"]

    def transition(self, new_status: ArticleStatus):
        self.status = new_status
        self.updated = datetime.now().isoformat()
        self.history.append(f"{new_status.value}@{datetime.now().strftime('%H:%M')}")
        self.awaiting = AWAITING.get(new_status)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status.value,
            "persona": self.persona,
            "series": self.series,
            "topic_dir": self.topic_dir,
            "url": self.url,
            "instructions": self.instructions,
            "created": self.created,
            "updated": self.updated,
            "awaiting": self.awaiting,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Article":
        art = cls(
            id=d["id"],
            persona=d.get("persona", "大史"),
            series=d.get("series", "独立篇"),
            topic_dir=d.get("topic_dir", ""),
            url=d.get("url", ""),
            instructions=d.get("instructions", ""),
        )
        art.status = ArticleStatus(d["status"])
        art.created = d.get("created", "")
        art.updated = d.get("updated", "")
        art.awaiting = d.get("awaiting")
        art.history = d.get("history", [])
        return art

    def summary(self) -> str:
        return f"[{self.status.value}] {self.id} ({self.persona}/{self.series})"


class StateManager:
    def __init__(self, state_file: str):
        self.state_file = Path(state_file).expanduser()
        self.articles: dict[str, Article] = {}
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
                art = Article.from_dict(d)
                self.articles[art.id] = art

    def _save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w") as f:
            for art in self.articles.values():
                f.write(json.dumps(art.to_dict(), ensure_ascii=False) + "\n")

    def add_article(self, article: Article) -> Article:
        self.articles[article.id] = article
        self._save()
        return article

    def update_status(self, article_id: str, new_status: ArticleStatus):
        if article_id not in self.articles:
            raise KeyError(f"Article {article_id} not found")
        self.articles[article_id].transition(new_status)
        self._save()

    def get_article(self, article_id: str) -> Optional[Article]:
        return self.articles.get(article_id)

    def get_active(self) -> list[Article]:
        """Articles not yet ARCHIVED."""
        terminal = {ArticleStatus.ARCHIVED}
        return [a for a in self.articles.values() if a.status not in terminal]

    def get_awaiting_user(self) -> list[Article]:
        """Articles waiting for user input."""
        return [a for a in self.articles.values() if a.awaiting == "user_review"]

    def get_by_status(self, status: ArticleStatus) -> list[Article]:
        return [a for a in self.articles.values() if a.status == status]

    def status_summary(self) -> str:
        """One-line summary for Brain context."""
        active = self.get_active()
        if not active:
            return "没有正在进行的文章。"
        lines = []
        for a in active:
            wait = f" (等待: {a.awaiting})" if a.awaiting else ""
            lines.append(f"- {a.summary()}{wait}")
        return "\n".join(lines)
