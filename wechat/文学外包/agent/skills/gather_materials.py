"""
Skill: 素材采集
根据选题方向，从素材库查找已有素材 + web 搜索补充新素材。

输出：素材集目录（供 compress_goldline 使用）
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from wechat.agent.skills import Skill, SkillResult, _clean_env


class GatherMaterialsSkill(Skill):
    name = "gather_materials"
    description = "根据选题采集素材：查找已有素材库 + web 搜索补充"
    estimated_duration = "10min"

    async def execute(self, params: dict, config: dict) -> SkillResult:
        topic = params.get("topic", "")
        venue = params.get("venue", "")
        genre = params.get("genre", "散文")
        work_title = params.get("work_title", "")

        if not topic:
            return SkillResult(False, "需要 topic 参数（选题描述）")

        lit_root = Path(config["paths"]["lit_root"]).expanduser()
        materials_dir = Path(config["paths"]["materials_dir"]).expanduser()
        works_dir = Path(config["paths"]["works_dir"]).expanduser()

        # 1. Scan existing materials
        existing_materials = []
        if materials_dir.exists():
            for d in materials_dir.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    readme = d / "README.md"
                    if readme.exists():
                        content = readme.read_text()[:1000]
                        existing_materials.append(f"### {d.name}\n{content}")

        existing_str = "\n\n".join(existing_materials) if existing_materials else "素材库为空"

        # 2. Use Claude to research + compile materials
        prompt = f"""你是文学编辑 Agent 的素材采集模块。

## 任务
为以下选题采集写作素材：

选题：{topic}
目标刊物：{venue}
体裁：{genre}
{'作品标题：' + work_title if work_title else ''}

## 已有素材库
{existing_str}

## 要求

1. 先检查已有素材库中是否有可复用的素材
2. 搜索补充新的素材（历史典故、人物故事、地方志记载、统计数据等）
3. 按主题分组整理
4. 标注每条素材的来源（具体书名/网页/方志）
5. 标注哪些素材适合作为"核心意象"候选

输出格式：
===REUSABLE===
（从已有素材库可复用的内容）

===NEW_MATERIALS===
（新搜索到的素材，按主题分组）

===IMAGE_CANDIDATES===
（适合作为核心意象的候选，每个一句话描述）

===SUMMARY===
（一段话总结素材采集结果，给人类做决策参考）"""

        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", "sonnet",
                 "--output-format", "text", "--allowedTools", "WebSearch,WebFetch"],
                capture_output=True, text=True, timeout=600, env=_clean_env(),
            )

            if result.returncode != 0:
                return SkillResult(False, f"素材采集失败: {result.stderr[:300]}")

            output = result.stdout.strip()

            # 3. Save materials to work directory
            if work_title:
                work_dir = works_dir / work_title
            else:
                # Generate work dir name from topic
                safe_name = topic[:20].replace("/", "_").replace(" ", "_")
                work_dir = works_dir / f"{datetime.now().strftime('%Y%m%d')}_{safe_name}"

            work_dir.mkdir(parents=True, exist_ok=True)
            materials_file = work_dir / "gathered_materials.md"
            materials_file.write_text(
                f"# 素材采集\n\n"
                f"选题：{topic}\n"
                f"目标：{venue} ({genre})\n"
                f"采集时间：{datetime.now().isoformat()}\n\n"
                f"---\n\n{output}"
            )

            # Extract summary section
            summary = output
            if "===SUMMARY===" in output:
                summary = output.split("===SUMMARY===")[-1].strip()

            return SkillResult(
                True,
                f"素材采集完成\n\n工作目录: {work_dir}\n\n{summary[:1500]}",
                {"work_dir": str(work_dir), "materials_file": str(materials_file)},
            )
        except subprocess.TimeoutExpired:
            return SkillResult(False, "素材采集超时（>10min）")
        except Exception as e:
            return SkillResult(False, f"素材采集异常: {e}")
