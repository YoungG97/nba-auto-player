#!/usr/bin/env python3
"""
NBA TTS Script Cleaner
======================
Cleans raw player biography scripts into fluent, natural spoken Chinese scripts
specifically optimized for MiniMax / EdgeTTS speech synthesis.

Strict Rules Established:
1. Strips all section titles & labels (引言部分：, 关键词部分：, 基本信息部分：, etc.)
2. Strips keyword titles & bracketed descriptors before colon (e.g. '腰王（反重力弹簧人）：' -> only keep narrative text).
3. Strips bullet points, English name pronunciations, imperial units, and award years in parentheses (e.g. '（2020年）').
4. Converts numbers followed by 次/个 to Chinese characters ('2次' -> '两次', '2个赛季' -> '两个赛季').
5. Converts metric units ('1.88 m' -> '1米88', '79 KG' -> '79公斤').
6. Strips chronological season-by-season game logs and latest news game chronicle sections completely.
7. CRITICAL RULE: Preserves 100% of the author's original words, English proper nouns (G6, Rocco), verbs, quotes, and colloquial particles intact!
"""

import re
import sys
import os

def clean_tts_script(raw_text: str) -> str:
    """Clean raw script into TTS-optimized spoken narrative."""
    lines = raw_text.strip().splitlines()
    cleaned_paragraphs = []
    
    current_section = None
    skip_season_chronicle = False
    
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
            
        # Strip markdown bolding / headers for pattern matching
        norm_line = re.sub(r'[*#_]', '', line).strip()
        
        # Check Section Headers
        if re.search(r'^(引言|引言部分|导语)[：:]?', norm_line):
            current_section = 'intro'
            skip_season_chronicle = False
            continue
        elif re.search(r'^(关键词|关键词部分)[：:]?', norm_line):
            current_section = 'keywords'
            skip_season_chronicle = False
            continue
        elif re.search(r'^(基本信息|基本信息部分)[：:]?', norm_line):
            current_section = 'bio'
            skip_season_chronicle = False
            continue
        elif re.search(r'^(职业生涯经历及成就|职业生涯经历及成就部分)[：:]?', norm_line):
            current_section = 'career'
            skip_season_chronicle = False
            continue
        elif re.search(r'^(结尾|结语|总结)[：:]?', norm_line):
            current_section = 'outro'
            skip_season_chronicle = False
            continue

        # Check for season chronicle headers (e.g. '2019-20赛季（最佳新秀）' or '2026-27赛季（最新动态）')
        if re.search(r'^(20\d\d[-–—]\d\d?赛季|20\d\d[-–—]20\d\d年?\s*[(（]?[^）)]*[)）]?|最新动态)', norm_line):
            # Once we hit season-by-season detailed chronicles, we skip until the outro
            skip_season_chronicle = True
            continue

        if skip_season_chronicle:
            continue

        # Process by section
        if current_section == 'intro':
            # Skip introductory label like '先来认识一下...'
            cleaned_paragraphs.append(clean_text_sentence(norm_line))
            
        elif current_section == 'keywords':
            # Remove keyword label before colon e.g. "腰王（反重力弹簧人）：" or "汤神 / 佛祖（G6汤）："
            colon_match = re.search(r'^[-*•\s]*(.+?)[：:]\s*(.+)$', norm_line)
            if colon_match:
                content = colon_match.group(2).strip()
                cleaned_paragraphs.append(clean_text_sentence(content))
            else:
                if not re.search(r'^(先来几个关键词|让你快速记住他)', norm_line):
                    cleaned_paragraphs.append(clean_text_sentence(norm_line))
                    
        elif current_section == 'bio':
            # Basic info handling
            # Strip English aliases, imperial units
            if re.search(r'^(姓名|生日|国籍|身高|体重|球场上司职)[：:]', norm_line):
                # Clean specific fields
                val = re.sub(r'^(姓名|生日|国籍|身高|体重|球场上司职)[：:]\s*', '', norm_line)
                val = re.sub(r'[(（][^)）]*(?:Ja Morant|Klay|Temetrius|Alexander|磅|英尺|英寸)[^)）]*[)）]', '', val).strip()
                val = clean_units(val)
                field_name = re.match(r'^(姓名|生日|国籍|身高|体重|球场上司职)', norm_line).group(1)
                cleaned_paragraphs.append(f"{field_name}：{val}")
            else:
                cleaned_paragraphs.append(clean_text_sentence(norm_line))
                
        elif current_section == 'career':
            # Team header or honors
            # Strip bullet points
            norm_line = re.sub(r'^[-*•\s]+', '', norm_line)
            # Strip year in brackets e.g. （2020年） or （2022年、2023年）
            norm_line = re.sub(r'[(（]\s*20\d\d年?(?:[、,，\s]*20\d\d年?)*\s*[)）]', '', norm_line)
            # Clean units & counts
            cleaned_paragraphs.append(clean_text_sentence(norm_line))
            
        elif current_section == 'outro':
            cleaned_paragraphs.append(clean_text_sentence(norm_line))
            
        else:
            # Default fallback
            cleaned_paragraphs.append(clean_text_sentence(norm_line))

    # Join and final polish
    full_text = "\n\n".join([p for p in cleaned_paragraphs if p.strip()])
    return full_text

def clean_units(text: str) -> str:
    """Convert metric units and numbers to natural spoken text."""
    # Convert height: 1.88 m / 1.88米 -> 1米88
    text = re.sub(r'1\.(\d{2})\s*(?:m|米)?', r'1米\1', text)
    # Convert weight: 79 KG / 79公斤 -> 79公斤
    text = re.sub(r'(\d+)\s*(?:KG|kg|公斤)', r'\1公斤', text)
    # Convert counts: 2次 -> 两次, 2个 -> 两个, 1次 -> 1次 (or keep)
    text = re.sub(r'\b2次\b', '两次', text)
    text = re.sub(r'\b2个', '两个', text)
    text = re.sub(r'(\d+)次', lambda m: '两次' if m.group(1) == '2' else m.group(0), text)
    text = re.sub(r'(\d+)个', lambda m: '两个' if m.group(1) == '2' else m.group(0), text)
    return text

def clean_text_sentence(text: str) -> str:
    """Apply unit and count cleaning while strictly preserving vocabulary and symbols."""
    text = clean_units(text)
    # Ensure double quotes, commas, and exclamation marks are preserved cleanly
    return text.strip()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        in_file = sys.argv[1]
        with open(in_file, "r", encoding="utf-8") as f:
            raw = f.read()
        cleaned = clean_tts_script(raw)
        out_file = sys.argv[2] if len(sys.argv) > 2 else in_file.replace(".txt", "_TTS口播文案.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(cleaned)
        print(f"Cleaned TTS script saved to: {out_file}")
    else:
        print("Usage: python3 tts_script_cleaner.py <raw_script.txt> [output_tts.txt]")
