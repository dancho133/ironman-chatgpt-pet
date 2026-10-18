#!/usr/bin/env python3
"""
Standalone Spritesheet Validator for ChatGPT Pets (v1 & v2 standards).
Validates dimensions, grid allocations, frame transparency, and RGB residue.
"""

import argparse
import json
import sys
from pathlib import Path
from PIL import Image
import numpy as np

CELL_WIDTH = 192
CELL_HEIGHT = 208
COLS = 8

V1_ROWS = 9
V2_ROWS = 11

V1_HEIGHT = 1872
V2_HEIGHT = 2288
EXPECTED_WIDTH = 1536

# Active frames per row
FRAMES_PER_ROW_V1 = [6, 8, 8, 4, 5, 8, 6, 6, 6]
FRAMES_PER_ROW_V2 = [6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]

ROW_NAMES = [
    "Row 0: Idle",
    "Row 1: Walk / Pacing",
    "Row 2: Run / Dash",
    "Row 3: Rest / Sit",
    "Row 4: Thinking / Processing",
    "Row 5: Action / Working / Typing",
    "Row 6: Success / Celebration",
    "Row 7: Failure / Error / Confused",
    "Row 8: Sleep / Nap",
    "Row 9: Cursor Tracking Angles 1-8 (v2)",
    "Row 10: Cursor Tracking Angles 9-16 (v2)",
]


def validate_spritesheet(image_path: Path, expected_version: int = None) -> dict:
    result = {
        "file": str(image_path),
        "valid": False,
        "sprite_version": None,
        "width": 0,
        "height": 0,
        "cell_width": CELL_WIDTH,
        "cell_height": CELL_HEIGHT,
        "active_frames": 0,
        "transparent_cells": 0,
        "transparent_rgb_residue_pixels": 0,
        "errors": [],
        "warnings": [],
    }

    if not image_path.exists():
        result["errors"].append(f"File not found: {image_path}")
        return result

    try:
        im = Image.open(image_path)
    except Exception as e:
        result["errors"].append(f"Failed to open image: {e}")
        return result

    w, h = im.size
    result["width"] = w
    result["height"] = h

    if w != EXPECTED_WIDTH:
        result["errors"].append(f"Invalid width: {w}px (expected exactly {EXPECTED_WIDTH}px)")

    version = None
    if h == V2_HEIGHT:
        version = 2
    elif h == V1_HEIGHT:
        version = 1
    else:
        result["errors"].append(
            f"Invalid height: {h}px (expected {V1_HEIGHT}px for v1 or {V2_HEIGHT}px for v2)"
        )

    if expected_version is not None and version != expected_version:
        result["errors"].append(
            f"Detected sprite version {version}, but expected v{expected_version}"
        )

    if version is None:
        return result

    result["sprite_version"] = version
    rows = V2_ROWS if version == 2 else V1_ROWS
    active_spec = FRAMES_PER_ROW_V2 if version == 2 else FRAMES_PER_ROW_V1
    result["frames_per_row"] = active_spec

    if im.mode != "RGBA":
        result["errors"].append(f"Invalid image mode: {im.mode} (expected RGBA with alpha channel)")
        return result

    arr = np.array(im)
    alpha = arr[:, :, 3]

    # Check for transparent RGB residue (alpha == 0 with RGB != 0)
    zero_alpha = alpha == 0
    rgb_sum = arr[:, :, 0].astype(int) + arr[:, :, 1].astype(int) + arr[:, :, 2].astype(int)
    residue_count = int(np.sum(zero_alpha & (rgb_sum > 0)))
    result["transparent_rgb_residue_pixels"] = residue_count
    if residue_count > 0:
        result["warnings"].append(
            f"{residue_count} transparent pixels have non-zero RGB values (recommended to zero RGB for clean alpha compression)"
        )

    total_active = 0
    total_transparent = 0

    for r in range(rows):
        expected_active = active_spec[r]
        for c in range(COLS):
            cell_alpha = alpha[r * CELL_HEIGHT : (r + 1) * CELL_HEIGHT, c * CELL_WIDTH : (c + 1) * CELL_WIDTH]
            has_pixels = np.any(cell_alpha > 0)
            opaque_all = np.all(cell_alpha == 255)

            if opaque_all:
                result["errors"].append(
                    f"Row {r}, Col {c} is completely opaque. ChatGPT Pets requires transparent background."
                )

            if c < expected_active:
                total_active += 1
                if not has_pixels:
                    row_label = ROW_NAMES[r] if r < len(ROW_NAMES) else f"Row {r}"
                    result["errors"].append(
                        f"Missing artwork in active cell: Row {r} Col {c} ({row_label})"
                    )
            else:
                total_transparent += 1
                if has_pixels:
                    max_a = int(np.max(cell_alpha))
                    count_nz = int(np.sum(cell_alpha > 0))
                    result["errors"].append(
                        f"Artwork found in unused cell: Row {r} Col {c} ({count_nz} non-zero pixels, max alpha {max_a}; must be 100% transparent)"
                    )

    result["active_frames"] = total_active
    result["transparent_cells"] = total_transparent
    result["valid"] = len(result["errors"]) == 0

    return result


def main():
    parser = argparse.ArgumentParser(description="Validate ChatGPT Pets spritesheet (v1 / v2)")
    parser.add_argument("file", type=Path, help="Path to spritesheet PNG or WebP")
    parser.add_argument("--v1", action="store_true", help="Enforce v1 standard (1536x1872, 9 rows)")
    parser.add_argument("--v2", action="store_true", help="Enforce v2 standard (1536x2288, 11 rows)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    expected_ver = 1 if args.v1 else (2 if args.v2 else None)
    res = validate_spritesheet(args.file, expected_ver)

    if args.json:
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["valid"] else 1)

    print("=" * 64)
    print("         ChatGPT Pets Spritesheet Validation Report")
    print("=" * 64)
    print(f"File:            {res['file']}")
    print(f"Dimensions:      {res['width']}x{res['height']} px")
    print(f"Standard:        v{res['sprite_version'] if res['sprite_version'] else 'Unknown'}")
    print(f"Active Frames:   {res['active_frames']}")
    print(f"Empty Cells:     {res['transparent_cells']}")
    print(f"Residue Pixels:  {res['transparent_rgb_residue_pixels']}")
    print("-" * 64)

    if res["warnings"]:
        print("WARNINGS:")
        for w in res["warnings"]:
            print(f"  [!] {w}")
        print("-" * 64)

    if res["errors"]:
        print("ERRORS:")
        for e in res["errors"]:
            print(f"  [X] {e}")
        print("=" * 64)
        print("RESULT: FAILED (valid=False)")
        print("=" * 64)
        sys.exit(1)
    else:
        print("=" * 64)
        print("RESULT: PASSED (valid=True) - Spritesheet is 100% compliant!")
        print("=" * 64)
        sys.exit(0)


if __name__ == "__main__":
    main()
