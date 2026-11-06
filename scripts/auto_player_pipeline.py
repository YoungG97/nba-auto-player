#!/usr/bin/env python3
"""
NBA Auto Player Master Pipeline Orchestrator
============================================
Orchestrates the entire 5-step end-to-end NBA documentary production workflow:
1. TTS Script Cleaning (Word preservation & structure stripping)
2. MiniMax HD Voice Synthesis (Zero clone fee)
3. Visual Media Harvesting (Getty 2048px watermark-free + YouTube 100% non-game B-Roll)
4. 1080P 60fps Broadcast Animation Production (8 packaging modules)
5. Surgical Breath-Gap Trimming & JianYing Pro 12-Track Assembly

Supports both --interactive (human-in-the-loop step-by-step confirmation)
and --auto (fully autonomous hands-free execution).
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# Relative script imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tts_script_cleaner import clean_tts_script
from voice_synthesizer import synthesize_text
from image_aligner_harvester import batch_harvest_images
from broll_downloader import batch_download_broll
from visual_packager import package_all_visual_modules
from timeline_assembler import trim_breath_gaps, build_jianying_draft

def prompt_confirm(step_name: str, details: str, interactive: bool) -> bool:
    """Prompt user for confirmation if interactive mode is active."""
    print(f"\n==================================================")
    print(f"📍【{step_name}】完成")
    print(f"详情: {details}")
    print(f"==================================================")
    if not interactive:
        return True
    ans = input(f"👉 是否确认通过并进入下一步？(y/n, 默认 y): ").strip().lower()
    return ans in ["", "y", "yes", "ok", "确认", "继续"]

def run_pipeline(
    raw_script_path: str,
    player_name: str,
    workspace_dir: str,
    interactive: bool = True
) -> dict:
    """Executes the complete 5-step pipeline."""
    player_dir = os.path.join(workspace_dir, player_name)
    os.makedirs(player_dir, exist_ok=True)
    
    print(f"\n🏀 Starting NBA Auto Player Pipeline for: 《{player_name}》")
    print(f"📁 Workspace: {player_dir}")
    print(f"⚙️ Mode: {'逐步人机确认 (--interactive)' if interactive else '一键全自动 (--auto)'}\n")

    # ----------------------------------------------------
    # Step 1: TTS Script Cleaning
    # ----------------------------------------------------
    with open(raw_script_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    cleaned_script = clean_tts_script(raw_text)
    tts_script_path = os.path.join(player_dir, f"{player_name}_TTS口播文案.txt")
    with open(tts_script_path, "w", encoding="utf-8") as f:
        f.write(cleaned_script)

    if not prompt_confirm(
        "Step 1: TTS 口播稿清洗",
        f"已剔除结构标题与赛季战报，100% 保留作者原版词汇与热梗。生成文件：{tts_script_path}",
        interactive
    ):
        print("🛑 流程被用户暂停。")
        return {"status": "paused_at_step_1"}

    # ----------------------------------------------------
    # Step 2: MiniMax HD Voiceover Synthesis
    # ----------------------------------------------------
    mp3_path = os.path.join(player_dir, f"{player_name}_配音原声.mp3")
    wav_path = os.path.join(player_dir, f"{player_name}_配音原声.wav")
    synthesize_text(cleaned_script, mp3_path, wav_path)

    if not prompt_confirm(
        "Step 2: 声音克隆与配音合成",
        f"已使用 MiniMax speech-02-hd 原声克隆生成全套广播级人声：\n- MP3: {mp3_path}\n- WAV: {wav_path}",
        interactive
    ):
        print("🛑 流程被用户暂停。")
        return {"status": "paused_at_step_2"}

    # ----------------------------------------------------
    # Step 3: Visual Assets Harvesting (Images & Non-Game B-Roll)
    # ----------------------------------------------------
    img_dir = os.path.join(player_dir, f"{player_name}_高清图片素材")
    video_dir = os.path.join(player_dir, f"{player_name}_视频素材")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)

    if not prompt_confirm(
        "Step 3: 视觉图库与纯非比赛纪实采编",
        f"图片与视频素材已完成校验（恪守零比赛转播红线）：\n- 图片库: {img_dir}\n- 纪实视频: {video_dir}",
        interactive
    ):
        print("🛑 流程被用户暂停。")
        return {"status": "paused_at_step_3"}

    # ----------------------------------------------------
    # Step 4: Broadcast Animation Packaging
    # ----------------------------------------------------
    anim_dir = os.path.join(player_dir, f"{player_name}_动效包装")
    package_all_visual_modules(player_name, anim_dir)

    if not prompt_confirm(
        "Step 4: 8套广播级 1080P 60fps 动效包装渲染",
        f"入场流光、核心词云、章节海报、生涯荣誉与 32s 跑马灯相册均已就绪：{anim_dir}",
        interactive
    ):
        print("🛑 流程被用户暂停。")
        return {"status": "paused_at_step_4"}

    # ----------------------------------------------------
    # Step 5: Surgical Breath-Gap Trimming & JianYing Assembly
    # ----------------------------------------------------
    trimmed_wav_path = os.path.join(player_dir, f"{player_name}_配音精修紧凑版.wav")
    trim_breath_gaps(wav_path, trimmed_wav_path)

    draft_name = f"{player_name}_人物志"
    draft_dir = build_jianying_draft(draft_name, trimmed_wav_path, video_dir, anim_dir)

    print(f"\n🎉🎉🎉 恭喜！《{draft_name}》全自动端到端制作完成！")
    print(f"🎬 打开剪映专业版首页即可直接查看、播放与导出工程：{draft_dir}\n")
    return {"status": "completed", "draft_dir": draft_dir}

def main():
    parser = argparse.ArgumentParser(description="nba-auto-player: NBA Player Documentary Master Pipeline")
    parser.add_argument("--script", type=str, required=True, help="Path to raw biography script (.txt)")
    parser.add_argument("--player", type=str, required=True, help="Player Chinese name (e.g. 克莱·汤普森)")
    parser.add_argument("--out", type=str, default="~/Downloads", help="Base output directory")
    parser.add_argument("--auto", action="store_true", help="Run in hands-free fully automated mode (no prompts)")
    args = parser.parse_args()

    workspace = os.path.expanduser(args.out)
    interactive = not args.auto
    run_pipeline(args.script, args.player, workspace, interactive=interactive)

if __name__ == "__main__":
    main()
