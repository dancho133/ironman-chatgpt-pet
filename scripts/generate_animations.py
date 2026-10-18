#!/usr/bin/env python3
"""
Slice a ChatGPT Pets v2 Spritesheet into individual animated preview GIFs.
"""

import argparse
from pathlib import Path
from PIL import Image

CELL_WIDTH = 192
CELL_HEIGHT = 208

ANIMATIONS_SPEC = [
    ("idle", 0, 6, 120),
    ("walk", 1, 8, 100),
    ("run", 2, 8, 80),
    ("rest", 3, 4, 250),
    ("thinking", 4, 5, 150),
    ("action", 5, 8, 100),
    ("success", 6, 6, 120),
    ("failure", 7, 6, 150),
    ("sleep", 8, 6, 250),
]


def generate_gifs(spritesheet_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    im = Image.open(spritesheet_path).convert("RGBA")
    w, h = im.size

    print(f"Loading {spritesheet_path} ({w}x{h} px)...")

    for name, row, frame_count, duration in ANIMATIONS_SPEC:
        frames = []
        for c in range(frame_count):
            box = (c * CELL_WIDTH, row * CELL_HEIGHT, (c + 1) * CELL_WIDTH, (row + 1) * CELL_HEIGHT)
            frames.append(im.crop(box))
        out_file = output_dir / f"{name}.gif"
        frames[0].save(
            out_file,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            disposal=2,
        )
        print(f"  [+] Saved {out_file.name} ({frame_count} frames, {duration}ms)")

    # 360-degree cursor tracking (v2 only: 16 frames in rows 9 & 10)
    if h >= 2288:
        look_frames = []
        for idx in range(16):
            r = 9 + (idx // 8)
            c = idx % 8
            box = (c * CELL_WIDTH, r * CELL_HEIGHT, (c + 1) * CELL_WIDTH, (r + 1) * CELL_HEIGHT)
            look_frames.append(im.crop(box))

        look_file = output_dir / "cursor_tracking.gif"
        look_frames[0].save(
            look_file,
            save_all=True,
            append_images=look_frames[1:],
            duration=90,
            loop=0,
            disposal=2,
        )
        print(f"  [+] Saved {look_file.name} (16 look angles, 90ms)")

    print("All preview GIFs generated successfully!")


def main():
    parser = argparse.ArgumentParser(description="Extract animated GIFs from ChatGPT Pets spritesheet")
    parser.add_argument(
        "--spritesheet",
        type=Path,
        default=Path("assets/ironman_funko_anime_v2_spritesheet.png"),
        help="Path to spritesheet PNG",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("animations"),
        help="Directory to save GIF files",
    )
    args = parser.parse_args()
    generate_gifs(args.spritesheet, args.out_dir)


if __name__ == "__main__":
    main()
