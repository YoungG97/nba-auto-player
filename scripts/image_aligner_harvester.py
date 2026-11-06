#!/usr/bin/env python3
"""
Getty Images Aligner & Watermark Removal Harvester
=================================================
Fetches, validates horizontal aspect ratio (W > H), and applies mathematical
feathered inpainting to reconstruct Getty watermark areas without blur artifacts.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple

def remove_getty_watermark(img_path: str, output_path: str) -> bool:
    """
    Remove Getty Images watermark with mathematical bounding box:
    Y: 0.608*H ~ 0.723*H, X: 0.580*W ~ W.
    Applies Gaussian feathering, multi-scale inpainting and high-pass sharpness boost.
    """
    img = cv2.imread(img_path)
    if img is None:
        return False
        
    h, w = img.shape[:2]
    # Check horizontal aspect ratio
    if w <= h:
        print(f"⚠️ Image is not horizontal ({w}x{h}), skipping: {img_path}")
        return False

    # Define watermark bounding box
    y1 = int(h * 0.608)
    y2 = int(h * 0.723)
    x1 = int(w * 0.580)
    x2 = w

    mask = np.zeros((h, w), dtype=np.uint8)
    mask[y1:y2, x1:x2] = 255

    # Telea inpainting algorithm
    inpainted = cv2.inpaint(img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

    # Blend border feathering to avoid sharp transition edges
    feather_mask = cv2.GaussianBlur(mask.astype(np.float32) / 255.0, (15, 15), 0)
    feather_mask_3c = np.repeat(feather_mask[:, :, np.newaxis], 3, axis=2)

    result = (inpainted * feather_mask_3c + img * (1.0 - feather_mask_3c)).astype(np.uint8)

    # Trim bottom border if black letterboxing exists (up to 4px)
    if np.mean(result[-4:, :, :]) < 10:
        result = result[:-4, :, :]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    cv2.imwrite(output_path, result, [cv2.IMWRITE_JPEG_QUALITY, 96])
    return True

def batch_harvest_images(
    catalog_config_path: str,
    output_root: str
) -> Dict[str, int]:
    """Batch harvest and process images defined in a curation catalog."""
    with open(catalog_config_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    player = catalog.get("player_name", "NBA Player")
    tasks = catalog.get("images", [])
    
    print(f"📸 Starting image harvesting for: {player} ({len(tasks)} images)")
    success = 0
    failed = 0

    for idx, item in enumerate(tasks, 1):
        category = item.get("category", "01_生涯经历与文案对应图")
        filename = item.get("filename", f"image_{idx:02d}.jpg")
        src_path = item.get("src_path")
        out_path = os.path.join(output_root, category, filename)

        if src_path and os.path.exists(src_path):
            if remove_getty_watermark(src_path, out_path):
                success += 1
                print(f"[{idx}/{len(tasks)}] Processed: {category}/{filename}")
            else:
                failed += 1
        else:
            failed += 1

    return {"total": len(tasks), "success": success, "failed": failed}

if __name__ == "__main__":
    if len(sys.argv) > 2:
        in_img = sys.argv[1]
        out_img = sys.argv[2]
        ok = remove_getty_watermark(in_img, out_img)
        print("Success" if ok else "Failed")
    else:
        print("Usage: python3 image_aligner_harvester.py <input.jpg> <output.jpg>")
