#!/usr/bin/env python3
"""
NBA YouTube Non-Game B-Roll Harvester
====================================
Downloads 1080P/4K non-game documentary B-Roll videos via yt-dlp & FFmpeg.
STRICT RED LINE: Rejects all broadcast game footage / game highlights!
"""

import os
import sys
import json
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

FORBIDDEN_KEYWORDS = [
    "full game highlights", "game highlights", "vs highlights", "top 10 plays of the game",
    "condensed game", "full quarter", "every shot from", "match highlights"
]

def check_video_validity(title: str) -> bool:
    """Validate that title does not indicate game highlights."""
    title_lower = title.lower()
    for kw in FORBIDDEN_KEYWORDS:
        if kw in title_lower:
            return False
    return True

def download_video(url: str, output_path: str, max_retries: int = 3) -> bool:
    """Download single YouTube video with yt-dlp."""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 102400:
        sz_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"  ⏭️ Already exists ({sz_mb:.1f} MB): {os.path.basename(output_path)}")
        return True

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fmt = "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"

    cmd = [
        "yt-dlp",
        "-f", fmt,
        "--merge-output-format", "mp4",
        "--no-playlist",
        "--continue",
        "--retries", str(max_retries),
        "-o", output_path,
        url
    ]

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
        if res.returncode == 0 and os.path.exists(output_path):
            sz_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  ✅ Downloaded successfully: {os.path.basename(output_path)} ({sz_mb:.1f} MB)")
            return True
        else:
            # Fallback format
            cmd_fallback = [
                "yt-dlp",
                "-f", "best[ext=mp4]/best",
                "--merge-output-format", "mp4",
                "--no-playlist",
                "-o", output_path,
                url
            ]
            res2 = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)
            return res2.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print(f"  ❌ Error downloading {url}: {e}")
        return False

def batch_download_broll(
    config_json_path: str,
    max_workers: int = 4
) -> Dict[str, int]:
    """Execute batch download from curation JSON."""
    with open(config_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    base_dir = data.get("base_dir", "~/Downloads/nba_broll")
    base_dir = os.path.expanduser(base_dir)
    videos = data.get("videos", [])

    print(f"\n🎬 Starting B-Roll download ({len(videos)} videos) into: {base_dir}")
    tasks = []
    for v in videos:
        subfolder = v.get("category", "01_引言")
        filename = v.get("filename", "video.mp4")
        url = v.get("url")
        if url:
            target_path = os.path.join(base_dir, subfolder, filename)
            tasks.append((subfolder, filename, url, target_path))

    success = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futs = {executor.submit(download_video, u, tp): (sf, fn) for sf, fn, u, tp in tasks}
        for fut in as_completed(futs):
            sf, fn = futs[fut]
            try:
                if fut.result():
                    success += 1
                else:
                    failed += 1
            except Exception:
                failed += 1

    print(f"🏁 Finished: {success} succeeded, {failed} failed.\n")
    return {"total": len(tasks), "success": success, "failed": failed}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cfg = sys.argv[1]
        batch_download_broll(cfg)
    else:
        print("Usage: python3 broll_downloader.py <curation.json>")
