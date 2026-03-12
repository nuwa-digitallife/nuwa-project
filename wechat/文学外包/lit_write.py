#!/usr/bin/env python3
"""
文学写作引擎 — 金线压缩-展开法

复用 engine.py 的核心函数（fill_template, run_claude, parse_delimited_output），
以文学专用 prompts 驱动 4-Pass 写作流程。

流程：
  Pass 0: 金线压缩 — 素材→核心意象+洞察（交互式确认）
  Pass 1: 展开写作 — 金线→全文
  Pass 2: 金线自检 — 6C + 六大败相扫描（只出报告）
  Pass 3: 整合修订 — 根据审稿报告修订→终稿 + DOCX

用法：
  # 完整流程（Pass 0 后暂停确认）
  python lit_write.py --materials-dir 素材库/城市文化-南宁 --venue "《红豆》" --genre 散文

  # 只跑金线压缩
  python lit_write.py --materials-dir 素材库/城市文化-南宁 --venue "《红豆》" --genre 散文 --pass 0

  # 断点续跑（已有金线，从 Pass 1 开始）
  python lit_write.py --work-dir 作品/新作品名 --pass 1

  # 指定字数
  python lit_write.py --materials-dir ... --venue ... --genre 散文 --word-count 4000
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# ── 路径设置 ─────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # nuwa-project/
PROMPTS_DIR = SCRIPT_DIR / "prompts"
DEVLOG_FILE = SCRIPT_DIR / "logs" / "devlog.jsonl"

# 从 engine.py 导入核心函数
ENGINE_DIR = PROJECT_ROOT / "wechat" / "tools" / "write_engine"
sys.path.insert(0, str(ENGINE_DIR))
from engine import fill_template, run_claude, parse_delimited_output

# ── 日志 ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lit_write")

# ── 默认配置 ─────────────────────────────────────────
DEFAULT_MODEL = "opus"
DEFAULT_EFFORT = "high"
DEFAULT_TOOLS = "WebSearch,WebFetch"
DEFAULT_WORD_COUNT = "4000-5000"


def devlog(entry: dict):
    """追加开发日志。"""
    DEVLOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now().isoformat()
    entry["project"] = "文学外包"
    with open(DEVLOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_materials(materials_dir: Path) -> str:
    """加载素材目录下所有 .md 和 .txt 文件内容。"""
    contents = []
    for ext in ("*.md", "*.txt"):
        for f in sorted(materials_dir.glob(ext)):
            contents.append(f"--- {f.name} ---\n{f.read_text()}")
    if not contents:
        log.warning(f"素材目录 {materials_dir} 中没有找到 .md/.txt 文件")
    return "\n\n".join(contents)


def load_prompt(name: str) -> str:
    """加载 prompt 模板。"""
    path = PROMPTS_DIR / name
    if not path.exists():
        log.error(f"Prompt 文件不存在: {path}")
        sys.exit(1)
    return path.read_text()


def ensure_work_dir(work_dir: Path) -> Path:
    """确保作品目录存在。"""
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


# ── Pass 0：金线压缩 ─────────────────────────────────

def pass0_compress(materials_dir: Path, venue: str, genre: str, work_dir: Path) -> str:
    """从素材中压缩出金线。返回金线输出文本。"""
    log.info("=== Pass 0: 金线压缩 ===")

    materials = load_materials(materials_dir)
    if not materials:
        log.error("无素材可用，退出")
        sys.exit(1)

    template = load_prompt("lit_pass0_compress.md")
    prompt = fill_template(template, {
        "MATERIAL_DOMAIN": materials_dir.name,
        "VENUE": venue,
        "GENRE": genre,
        "MATERIALS": materials,
    })

    output = run_claude(prompt, DEFAULT_MODEL, DEFAULT_TOOLS, DEFAULT_EFFORT)
    if not output:
        log.error("Pass 0 返回为空")
        sys.exit(1)

    # 保存金线输出
    goldline_file = work_dir / "goldline.md"
    goldline_file.write_text(output)
    log.info(f"金线输出已保存到: {goldline_file}")

    # 解析关键字段打印摘要
    parsed = parse_delimited_output(output, [
        "PATTERN", "IMAGE", "INSIGHT", "GOLDLINE", "EMOTION", "STRUCTURE_HINT"
    ])
    print("\n" + "=" * 60)
    print("金线压缩结果")
    print("=" * 60)
    for key in ["IMAGE", "INSIGHT", "GOLDLINE", "EMOTION"]:
        if key in parsed:
            print(f"\n【{key}】\n{parsed[key]}")
    if "STRUCTURE_HINT" in parsed:
        print(f"\n【结构草案】\n{parsed['STRUCTURE_HINT']}")
    print("=" * 60)

    return output


# ── Pass 1：展开写作 ─────────────────────────────────

def pass1_write(work_dir: Path, venue: str, genre: str, word_count: str,
                materials_dir: Path = None) -> str:
    """根据金线展开写作。返回文章文本。"""
    log.info("=== Pass 1: 展开写作 ===")

    goldline_file = work_dir / "goldline.md"
    if not goldline_file.exists():
        log.error(f"找不到金线文件: {goldline_file}")
        sys.exit(1)
    goldline_output = goldline_file.read_text()

    materials = ""
    if materials_dir and materials_dir.exists():
        materials = load_materials(materials_dir)

    template = load_prompt("lit_pass1_write.md")
    prompt = fill_template(template, {
        "VENUE": venue,
        "GENRE": genre,
        "WORD_COUNT": word_count,
        "GOLDLINE_OUTPUT": goldline_output,
        "MATERIALS": materials,
    })

    output = run_claude(prompt, DEFAULT_MODEL, "WebSearch,WebFetch", DEFAULT_EFFORT)
    if not output:
        log.error("Pass 1 返回为空")
        sys.exit(1)

    # 保存
    draft_file = work_dir / "draft.md"
    draft_file.write_text(output)
    log.info(f"初稿已保存到: {draft_file}")

    # 提取文章
    parsed = parse_delimited_output(output, ["ARTICLE", "TITLE", "SELF_CHECK"])
    if "ARTICLE" in parsed:
        article_file = work_dir / "article_v1.md"
        content = ""
        if "TITLE" in parsed:
            content = f"# {parsed['TITLE']}\n\n"
        content += parsed["ARTICLE"]
        article_file.write_text(content)
        log.info(f"文章提取到: {article_file}")
        print(f"\n标题: {parsed.get('TITLE', '(未提取)')}")
        print(f"字数: ~{len(parsed['ARTICLE'])} chars")

    return output


# ── Pass 2：金线自检 ─────────────────────────────────

def pass2_review(work_dir: Path, venue: str, genre: str, word_count: str) -> str:
    """对初稿进行自检和 AI 败相扫描。"""
    log.info("=== Pass 2: 金线自检 + AI败相扫描 ===")

    goldline_file = work_dir / "goldline.md"
    draft_file = work_dir / "draft.md"

    if not draft_file.exists():
        log.error(f"找不到初稿: {draft_file}")
        sys.exit(1)

    goldline_output = goldline_file.read_text() if goldline_file.exists() else ""
    draft_output = draft_file.read_text()

    # 提取文章正文
    parsed_draft = parse_delimited_output(draft_output, ["ARTICLE", "TITLE"])
    article = parsed_draft.get("ARTICLE", draft_output)

    template = load_prompt("lit_pass2_review.md")
    prompt = fill_template(template, {
        "GOLDLINE_OUTPUT": goldline_output,
        "ARTICLE": article,
        "VENUE": venue,
        "GENRE": genre,
        "WORD_COUNT": word_count,
    })

    output = run_claude(prompt, DEFAULT_MODEL, "WebSearch,WebFetch", DEFAULT_EFFORT)
    if not output:
        log.error("Pass 2 返回为空")
        sys.exit(1)

    review_file = work_dir / "review.md"
    review_file.write_text(output)
    log.info(f"审稿报告已保存到: {review_file}")

    # 打印摘要
    parsed = parse_delimited_output(output, [
        "GOLDLINE_CHECK", "6C_CHECK", "CLICHE_SCAN", "AI_SCAN",
        "COMPLIANCE", "SEVERITY", "FIX_LIST"
    ])
    severity = parsed.get("SEVERITY", "未知")
    print(f"\n审稿评级: {severity}")
    if "FIX_LIST" in parsed:
        print(f"\n修改清单:\n{parsed['FIX_LIST'][:500]}")

    return output


# ── Pass 3：整合修订 ─────────────────────────────────

def pass3_integrate(work_dir: Path) -> str:
    """根据审稿报告修订初稿，输出终稿。"""
    log.info("=== Pass 3: 整合修订 ===")

    goldline_file = work_dir / "goldline.md"
    draft_file = work_dir / "draft.md"
    review_file = work_dir / "review.md"

    if not review_file.exists():
        log.error(f"找不到审稿报告: {review_file}")
        sys.exit(1)

    goldline_output = goldline_file.read_text() if goldline_file.exists() else ""
    draft_output = draft_file.read_text()
    review_output = review_file.read_text()

    parsed_draft = parse_delimited_output(draft_output, ["ARTICLE", "TITLE"])
    article = parsed_draft.get("ARTICLE", draft_output)

    template = load_prompt("lit_pass3_integrate.md")
    prompt = fill_template(template, {
        "ARTICLE": article,
        "REVIEW_REPORT": review_output,
        "GOLDLINE_OUTPUT": goldline_output,
    })

    output = run_claude(prompt, DEFAULT_MODEL, "Bash", "high")
    if not output:
        log.error("Pass 3 返回为空")
        sys.exit(1)

    # 保存
    integrate_file = work_dir / "integrate.md"
    integrate_file.write_text(output)

    parsed = parse_delimited_output(output, [
        "FINAL_ARTICLE", "TITLE", "CHANGELOG", "STATS", "DOCX_CMD"
    ])

    if "FINAL_ARTICLE" in parsed:
        final_file = work_dir / "final.md"
        content = ""
        if "TITLE" in parsed:
            content = f"# {parsed['TITLE']}\n\n"
        content += parsed["FINAL_ARTICLE"]
        final_file.write_text(content)
        log.info(f"终稿已保存到: {final_file}")
        print(f"\n终稿标题: {parsed.get('TITLE', '(未提取)')}")

    if "STATS" in parsed:
        print(f"统计: {parsed['STATS']}")
    if "DOCX_CMD" in parsed:
        print(f"\n生成 DOCX 命令:\n{parsed['DOCX_CMD']}")

    return output


# ── 主流程 ───────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="文学写作引擎 — 金线压缩-展开法",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 完整流程
  python lit_write.py --materials-dir 素材库/城市文化-南宁 --venue "《红豆》" --genre 散文

  # 只跑金线压缩
  python lit_write.py --materials-dir 素材库/城市文化-南宁 --venue "《红豆》" --genre 散文 --pass 0

  # 断点续跑
  python lit_write.py --work-dir 作品/新作品 --pass 1
        """,
    )
    parser.add_argument("--materials-dir", help="素材目录路径")
    parser.add_argument("--work-dir", help="作品工作目录（断点续跑时使用）")
    parser.add_argument("--venue", default="通用", help="目标刊物")
    parser.add_argument("--genre", default="散文", help="体裁")
    parser.add_argument("--word-count", default=DEFAULT_WORD_COUNT, help="字数范围（如 4000-5000）")
    parser.add_argument("--pass", type=int, default=None, dest="start_pass",
                        help="从指定 Pass 开始（0-3），默认从头开始")
    parser.add_argument("--work-name", help="作品名称（用于创建工作目录）")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude 模型")
    args = parser.parse_args()

    # 确定素材目录
    materials_dir = None
    if args.materials_dir:
        materials_dir = Path(args.materials_dir).resolve()
        if not materials_dir.exists():
            # 尝试相对于 SCRIPT_DIR
            materials_dir = SCRIPT_DIR / args.materials_dir
        if not materials_dir.exists():
            log.error(f"素材目录不存在: {args.materials_dir}")
            sys.exit(1)

    # 确定工作目录
    if args.work_dir:
        work_dir = Path(args.work_dir).resolve()
        if not work_dir.exists():
            work_dir = SCRIPT_DIR / args.work_dir
    elif args.work_name:
        work_dir = SCRIPT_DIR / "作品" / args.work_name
    elif materials_dir:
        # 从素材目录名生成
        timestamp = datetime.now().strftime("%Y%m%d")
        work_dir = SCRIPT_DIR / "作品" / f"{materials_dir.name}_{timestamp}"
    else:
        log.error("必须提供 --materials-dir 或 --work-dir")
        sys.exit(1)

    ensure_work_dir(work_dir)
    log.info(f"工作目录: {work_dir}")

    # 保存运行配置
    config = {
        "venue": args.venue,
        "genre": args.genre,
        "word_count": args.word_count,
        "materials_dir": str(materials_dir) if materials_dir else None,
        "model": args.model,
        "started": datetime.now().isoformat(),
    }
    config_file = work_dir / "config.json"
    if not config_file.exists():
        config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2))
    else:
        # 断点续跑：从保存的配置加载
        saved = json.loads(config_file.read_text())
        args.venue = args.venue if args.venue != "通用" else saved.get("venue", "通用")
        args.genre = args.genre if args.genre != "散文" else saved.get("genre", "散文")
        if args.word_count == DEFAULT_WORD_COUNT:
            args.word_count = saved.get("word_count", DEFAULT_WORD_COUNT)

    # 注意：model 通过 args.model 传递，不修改模块级常量

    start = args.start_pass if args.start_pass is not None else 0

    # Pass 0
    if start <= 0:
        if not materials_dir:
            log.error("Pass 0 需要 --materials-dir")
            sys.exit(1)
        pass0_compress(materials_dir, args.venue, args.genre, work_dir)

        # 交互式确认
        if args.start_pass is None or args.start_pass == 0:
            print("\n" + "=" * 60)
            print("Pass 0 完成。请检查金线压缩结果。")
            print("确认金线没问题后，运行以下命令继续：")
            print(f"  python lit_write.py --work-dir {work_dir.relative_to(SCRIPT_DIR)} --pass 1")
            print("=" * 60)

            if args.start_pass == 0:
                devlog({"type": "task", "context": "lit_write Pass 0",
                        "action": f"金线压缩完成: {work_dir.name}", "result": "等待用户确认"})
                return
            # 完整流程模式下询问
            try:
                answer = input("\n继续 Pass 1？(y/n): ").strip().lower()
                if answer != "y":
                    log.info("用户选择暂停，可用 --pass 1 继续")
                    devlog({"type": "task", "context": "lit_write Pass 0",
                            "action": f"金线压缩完成: {work_dir.name}", "result": "用户暂停"})
                    return
            except (EOFError, KeyboardInterrupt):
                log.info("非交互环境，暂停于 Pass 0")
                return

    # Pass 1
    if start <= 1:
        pass1_write(work_dir, args.venue, args.genre, args.word_count, materials_dir)

    # Pass 2
    if start <= 2:
        pass2_review(work_dir, args.venue, args.genre, args.word_count)

    # Pass 3
    if start <= 3:
        pass3_integrate(work_dir)

    devlog({"type": "task", "context": "lit_write 完整流程",
            "action": f"写作完成: {work_dir.name}", "result": "终稿已生成"})
    log.info("全部 Pass 完成！")


if __name__ == "__main__":
    main()
