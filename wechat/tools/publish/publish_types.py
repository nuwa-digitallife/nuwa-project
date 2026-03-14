"""发布流程的结构化类型定义"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class StepStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    step: str
    status: StepStatus
    message: str = ""
    retries: int = 0

    @property
    def ok(self) -> bool:
        return self.status == StepStatus.SUCCESS

    def __bool__(self) -> bool:
        return self.ok


@dataclass
class ArticleResult:
    topic_dir: str
    title: str = ""
    steps: List[StepResult] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return all(
            s.status in (StepStatus.SUCCESS, StepStatus.SKIPPED) for s in self.steps
        )

    @property
    def issues(self) -> List[str]:
        return [
            f"[{s.step}] {s.message}" for s in self.steps if s.status == StepStatus.FAILED
        ]

    def summary_line(self) -> str:
        if self.success:
            return f"{self.title or self.topic_dir}: OK"
        failed = [s.step for s in self.steps if s.status == StepStatus.FAILED]
        return f"{self.title or self.topic_dir}: FAILED ({', '.join(failed)})"


@dataclass
class PublishReport:
    articles: List[ArticleResult] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["\n" + "=" * 60, "  PUBLISH REPORT", "=" * 60]
        ok_count = sum(1 for a in self.articles if a.success)
        lines.append(f"  {ok_count}/{len(self.articles)} articles succeeded\n")
        for a in self.articles:
            lines.append(f"  {a.summary_line()}")
            for issue in a.issues:
                lines.append(f"    - {issue}")
                # Add recovery hint
                step_name = issue.split("]")[0].lstrip("[")
                lines.append(
                    f'      -> python one_click_publish.py --topic-dir "{a.topic_dir}" --resume-from {step_name}'
                )
        lines.append("=" * 60)
        return "\n".join(lines)
