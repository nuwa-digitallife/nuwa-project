#!/usr/bin/env python3
"""
LUNA COFFEE 开箱视频自动剪辑脚本
风格参考：成品视频（刷漆DIY + 搞门头）
用 moviepy + Pillow 实现字幕烧入
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip, concatenate_videoclips, CompositeVideoClip,
    ImageClip
)

BASE = "/Users/ciwang/Desktop/nuwa-project/videocut"
RAW = os.path.join(BASE, "rawMaterial")
OUTPUT = os.path.join(BASE, "output")
os.makedirs(OUTPUT, exist_ok=True)

# ── 剪辑方案 V4（对照偏好模型修正）──
# 修正：删窗帘纱(离题)、删空镜(楼梯站着看)、压缩码牛奶(36s→16s)
# 修正：字幕去广告词、加开头钩子、加收尾、全部压到3-6s/段
CLIPS = [
    # (源文件, 起始秒, 结束秒, 字幕文本)
    # --- 开头钩子 ---
    ("开箱 1.mp4", 0, 3, "谁懂，开咖啡馆第一步居然是洗杯子"),
    # --- 开箱1: 厨房，洗碗机放杯碗 ---
    ("开箱 1.mp4", 3, 8, "新到的杯碗，先全部过一遍水"),
    ("开箱 1.mp4", 8, 14, "一个个掏出来往洗碗机里码"),
    # --- 开箱4前半: 门口开大箱，发现立邦活性炭 ---
    ("开箱 4.mp4", 0, 6, "门口还堆着大箱子，继续拆"),
    ("开箱 4.mp4", 8, 14, "美工刀一划，好几箱活性炭"),
    ("开箱 4.mp4", 16, 22, "新装修的店，除甲醛是头等大事"),
    # --- 开箱2: 花窗旁放活性炭包 ---
    ("开箱 2.mp4", 0, 6, "冰裂纹花窗前，先放几包"),
    ("开箱 2.mp4", 8, 14, "一包包塞进每个角落"),
    # --- 开箱3: 搬运上二楼 ---
    ("开箱 3.mp4", 0, 6, "搬完一楼搬二楼"),
    ("开箱 3.mp4", 18, 24, "楼梯上也不放过，一层一包"),
    # --- 开箱4后半: 二楼新漆柜子旁放炭包 ---
    ("开箱 4.mp4", 38, 44, "二楼新刷的柜子，得多放几包"),
    # --- 开箱5: 冰柜 + 鲜活牛乳入库 ---
    ("开箱 5.mp4", 0, 5, "冰柜到了，插上电试试"),
    ("开箱 5.mp4", 22, 28, "鲜活牛乳到货，一盒盒码进去"),
    ("开箱 5.mp4", 42, 48, "码到满满当当，成就感拉满"),
    ("开箱 5.mp4", 54, 58, "奶源到位，离开业又近一步"),
]

# ── 字幕风格参数（匹配成品视频） ──
SUBTITLE_STYLE = {
    "font_size": 36,          # 基于720p
    "font_color": (255, 255, 255),
    "outline_color": (0, 0, 0),
    "outline_width": 3,
    "shadow_offset": (2, 2),
    "shadow_color": (0, 0, 0, 128),
    "y_position_ratio": 0.85,  # 距顶部85%
    "fade_in": 0.3,
    "fade_out": 0.3,
}


def find_chinese_font():
    """查找系统中可用的中文字体"""
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def make_subtitle_frame(text, width, height, style):
    """生成一帧字幕图片（透明背景 + 白字 + 黑色描边）"""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_path = find_chinese_font()
    if font_path:
        font = ImageFont.truetype(font_path, style["font_size"])
    else:
        font = ImageFont.load_default()

    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (width - text_w) // 2
    y = int(height * style["y_position_ratio"]) - text_h // 2

    # 阴影
    sx, sy = style["shadow_offset"]
    draw.text((x + sx, y + sy), text, font=font, fill=style["shadow_color"])

    # 描边（八方向偏移模拟）
    ow = style["outline_width"]
    oc = style["outline_color"] + (255,)
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=oc)

    # 主文字
    fc = style["font_color"] + (255,)
    draw.text((x, y), text, font=font, fill=fc)

    return np.array(img)


def create_subtitle_clip(text, duration, width, height, style):
    """创建带淡入淡出的字幕 clip"""
    frame = make_subtitle_frame(text, width, height, style)
    clip = ImageClip(frame).with_duration(duration)

    # 淡入淡出
    if style["fade_in"] > 0:
        clip = clip.with_effects([])  # moviepy v2 API
    return clip


def main():
    print("=== LUNA COFFEE 开箱视频剪辑 ===\n")

    # Step 1: 加载并截取片段
    print("1. 加载素材并截取片段...")
    video_clips = []
    subtitle_data = []  # (start_in_final, duration, text)
    current_time = 0.0

    for i, (src, start, end, subtitle) in enumerate(CLIPS):
        src_path = os.path.join(RAW, src)
        clip = VideoFileClip(src_path).subclipped(start, end)
        # 统一分辨率
        clip = clip.resized((1280, 720))
        video_clips.append(clip)

        duration = end - start
        subtitle_data.append((current_time, duration, subtitle))
        current_time += duration
        print(f"  [{i+1}/{len(CLIPS)}] {src} [{start}s-{end}s] ({duration}s) - {subtitle}")

    # Step 2: 拼接视频
    print(f"\n2. 拼接视频 (总时长 {current_time:.0f}s)...")
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Step 3: 生成字幕叠加层
    print("3. 生成字幕...")
    width, height = 1280, 720
    style = SUBTITLE_STYLE

    subtitle_clips = []
    for start_time, duration, text in subtitle_data:
        # 字幕延迟出现、提前消失
        sub_start = start_time + style["fade_in"]
        sub_duration = duration - style["fade_in"] - style["fade_out"]
        if sub_duration <= 0:
            sub_duration = duration * 0.8
            sub_start = start_time + duration * 0.1

        frame = make_subtitle_frame(text, width, height, style)
        sub_clip = (
            ImageClip(frame)
            .with_duration(sub_duration)
            .with_start(sub_start)
        )
        subtitle_clips.append(sub_clip)
        print(f"  [{sub_start:.1f}s-{sub_start+sub_duration:.1f}s] {text}")

    # Step 4: 合成
    print("\n4. 合成输出...")
    output_path = os.path.join(OUTPUT, "开箱成品.mp4")
    final = CompositeVideoClip([final_video] + subtitle_clips)
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30,
        preset="medium",
        bitrate="2000k",
        logger="bar",
    )

    # Cleanup
    for clip in video_clips:
        clip.close()
    final_video.close()
    final.close()

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"\n完成! 输出: {output_path}")
    print(f"大小: {size_mb:.1f}MB, 时长: {current_time:.0f}s")


if __name__ == "__main__":
    main()
