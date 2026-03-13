"""
Editor Agent skills registry.
Wraps literary tools (lit_write.py, draft_email.py, lit_status.py) as async skills.
Reuses Skill/SkillResult/SkillRegistry base classes from Agent PM.
"""

import sys
from pathlib import Path

# Share base classes from Agent PM
AGENT_PM_DIR = Path(__file__).resolve().parent.parent.parent.parent / "agent"
sys.path.insert(0, str(AGENT_PM_DIR.parent.parent))

from wechat.agent.skills import (
    Skill,
    SkillResult,
    SkillRegistry,
    NotifySkill,
    IdleSkill,
    _clean_env,
)

# Import editor-specific skills
from wechat.文学外包.agent.skills.write_manuscript import WriteManuscriptSkill
from wechat.文学外包.agent.skills.compress_goldline import CompressGoldlineSkill
from wechat.文学外包.agent.skills.draft_submission import DraftSubmissionSkill
from wechat.文学外包.agent.skills.track_submissions import TrackSubmissionsSkill
from wechat.文学外包.agent.skills.check_methodology import CheckMethodologySkill
from wechat.文学外包.agent.skills.scan_opportunities import ScanOpportunitiesSkill
from wechat.文学外包.agent.skills.refresh_opportunities import RefreshOpportunitiesSkill
from wechat.文学外包.agent.skills.gather_materials import GatherMaterialsSkill
from wechat.文学外包.agent.skills.analyze_result import AnalyzeResultSkill
from wechat.文学外包.agent.skills.intervene import InterveneSkill
from wechat.文学外包.agent.skills.check_inbox import CheckInboxSkill


def create_editor_registry() -> SkillRegistry:
    """Create registry with all editor skills."""
    registry = SkillRegistry()
    registry.register(NotifySkill())
    registry.register(IdleSkill())
    registry.register(ScanOpportunitiesSkill())
    registry.register(RefreshOpportunitiesSkill())
    registry.register(GatherMaterialsSkill())
    registry.register(CompressGoldlineSkill())
    registry.register(WriteManuscriptSkill())
    registry.register(DraftSubmissionSkill())
    registry.register(TrackSubmissionsSkill())
    registry.register(CheckMethodologySkill())
    registry.register(AnalyzeResultSkill())
    registry.register(InterveneSkill())
    registry.register(CheckInboxSkill())
    return registry
