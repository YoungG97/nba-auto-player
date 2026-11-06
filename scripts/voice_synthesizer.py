#!/usr/bin/env python3
"""
MiniMax HD Voice Synthesizer
============================
Synthesizes speech using MiniMax's speech-02-hd model with a locked custom cloned voice.
Strictly calls /v1/t2a_v2 (Zero cloning slot charges).
"""

import os
import sys
import json
import requests
import subprocess
from pathlib import Path
from typing import Optional

def load_config(config_path: Optional[str] = None) -> dict:
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 1. Check local config/minimax_config.json
    local_cfg = Path(__file__).parent.parent / "config" / "minimax_config.json"
    if local_cfg.exists():
        with open(local_cfg, "r", encoding="utf-8") as f:
            return json.load(f)
    # 2. Check sibling skill config fallback
    sibling_cfg = Path("/Users/young/.gemini/config/skills/nba-audio-trim-align/minimax_config.json")
    if sibling_cfg.exists():
        with open(sibling_cfg, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError("Could not find minimax_config.json. Please configure config/minimax_config.json based on minimax_config.example.json.")

def synthesize_text(
    text: str,
    output_mp3_path: str,
    output_wav_path: Optional[str] = None,
    config: Optional[dict] = None
) -> bool:
    """Synthesize text via MiniMax T2A v2 API."""
    if not config:
        config = load_config()

    api_key = config.get("api_key")
    group_id = config.get("group_id")
    voice_id = config.get("voice_id", "young_nba_narrator_v1")
    model = config.get("model", "speech-02-hd")
    speed = config.get("speed", 1.0)
    vol = config.get("vol", 1.0)
    pitch = config.get("pitch", 0)

    url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": vol,
            "pitch": pitch
        },
        "audio_setting": {
            "sample_rate": 44100,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1
        }
    }

    print(f"🎙️ Sending synthesis request to MiniMax (model: {model}, voice: {voice_id}, text_len: {len(text)})...")
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    
    if resp.status_code != 200:
        print(f"❌ MiniMax HTTP error: {resp.status_code} - {resp.text}")
        return False

    data = resp.json()
    base_resp = data.get("base_resp", {})
    if base_resp.get("status_code", 0) != 0:
        print(f"❌ MiniMax API error: {base_resp.get('status_msg')}")
        return False

    # Extract audio data (hex-encoded in 'data.audio')
    audio_hex = data.get("data", {}).get("audio", "")
    if not audio_hex:
        print("❌ No audio data returned in response.")
        return False

    audio_bytes = bytes.fromhex(audio_hex)
    os.makedirs(os.path.dirname(os.path.abspath(output_mp3_path)), exist_ok=True)
    with open(output_mp3_path, "wb") as f:
        f.write(audio_bytes)
    print(f"✅ Voiceover MP3 saved: {output_mp3_path} ({len(audio_bytes)/(1024*1024):.2f} MB)")

    # Convert to 44.1kHz mono WAV if requested
    if output_wav_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_wav_path)), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-i", output_mp3_path,
            "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le",
            output_wav_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode == 0:
            print(f"✅ Converted WAV saved: {output_wav_path}")
        else:
            print(f"⚠️ FFmpeg WAV conversion warning: {res.stderr.decode()[:200]}")

    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 voice_synthesizer.py <input_tts.txt> <output.mp3> [output.wav]")
        sys.exit(1)

    in_txt = sys.argv[1]
    out_mp3 = sys.argv[2]
    out_wav = sys.argv[3] if len(sys.argv) > 3 else out_mp3.replace(".mp3", ".wav")

    with open(in_txt, "r", encoding="utf-8") as f:
        text_content = f.read()

    synthesize_text(text_content, out_mp3, out_wav)
