#!/usr/bin/env python3
"""
Master 3D Octane-Rendered Anime Funko-Pop / Nendoroid Iron Man (Tony Stark)
Sprite Sheet Builder (v2 1536x2288 and v1 1536x1872) for ChatGPT Pets.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFilter

CELL_W = 192
CELL_H = 208
COLS = 8
ROWS_V1 = 9
ROWS_V2 = 11
def lut_map(lum: np.ndarray, stops: list[tuple[float, tuple[float, float, float]]]) -> np.ndarray:
    out = np.zeros((*lum.shape, 3), dtype=np.float32)
    for i in range(len(stops) - 1):
        t0, c0 = stops[i]
        t1, c1 = stops[i + 1]
        mask = (lum >= t0) & (lum <= t1 if i == len(stops) - 2 else lum < t1)
        if np.any(mask):
            w = np.clip((lum[mask] - t0) / max(1e-5, t1 - t0), 0.0, 1.0)[:, None]
            c0_arr = np.array(c0, dtype=np.float32)[None, :]
            c1_arr = np.array(c1, dtype=np.float32)[None, :]
            out[mask] = c0_arr * (1.0 - w) + c1_arr * w
    return out


def clean_transparent_rgb(img: Image.Image) -> Image.Image:
    arr = np.array(img, dtype=np.uint8)
    low_alpha = arr[:, :, 3] < 8
    arr[low_alpha] = (0, 0, 0, 0)
    return Image.fromarray(arr, mode="RGBA")


def extract_and_recolor_master(
    img_path: Path,
    mode: str = "open",  # 'open', 'closed', 'wave', 'fly_r', 'fail', 'work'
) -> Image.Image:
    im = Image.open(img_path).convert("RGB")
    W, H = im.size
    arr = np.array(im, dtype=np.float32)
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    max_c = np.maximum(np.maximum(R, G), B)
    min_c = np.minimum(np.minimum(R, G), B)
    sat = (max_c - min_c) / np.maximum(1.0, max_c)
    lum = (0.299 * R + 0.587 * G + 0.114 * B) / 255.0
    blue_excess = (B - R) / 255.0

    # 1. Border-Connected Flood-Fill Background Extraction
    bg_candidate = ((lum > 0.875) & (sat < 0.075) & (blue_excess < 0.045)) | (
        (yy > 868) & (sat < 0.11) & (blue_excess < 0.055) & (lum > 0.65)
    )

    if mode == "work":
        in_hologram = (xx >= 265) & (xx <= 495) & (yy >= 485) & (yy <= 630)
        bg_candidate = bg_candidate & (~in_hologram)

    labeled, _num = ndimage.label(bg_candidate)
    border_labels = (
        set(np.unique(labeled[0, :]))
        | set(np.unique(labeled[-1, :]))
        | set(np.unique(labeled[:, 0]))
        | set(np.unique(labeled[:, -1]))
    )
    border_labels.discard(0)
    is_bg = np.isin(labeled, list(border_labels))

    leg_arm_gaps = bg_candidate & (yy > 620) & (yy < 875) & (lum > 0.90) & (sat < 0.04)
    is_bg = is_bg | leg_arm_gaps

    is_flying = mode == "fly_r"
    flame_zone = (yy > 530) if is_flying else (yy > 760)
    flame_halo = (~is_bg) & flame_zone & (lum > 0.76) & (blue_excess > 0.035)

    alpha = np.where(is_bg, 0.0, 1.0).astype(np.float32)
    if np.any(flame_halo):
        flame_alpha = np.clip((blue_excess[flame_halo] - 0.025) * 4.8, 0.0, 1.0)
        alpha[flame_halo] = flame_alpha

    cutoff_y = 945 if is_flying else 884
    alpha[yy > cutoff_y] = 0.0

    interior = ndimage.binary_erosion(alpha > 0.5, iterations=2)
    alpha_blur = ndimage.gaussian_filter(alpha, sigma=1.0)
    alpha = np.where(interior, 1.0, alpha_blur)
    alpha[alpha < 0.04] = 0.0

    # 2. Physically-Based Metallic Red & Champagne Gold Recoloring
    red_stops = [
        (0.00, (32, 4, 8)),
        (0.18, (118, 10, 18)),
        (0.38, (196, 18, 28)),
        (0.62, (240, 38, 48)),
        (0.84, (255, 120, 125)),
        (1.00, (255, 235, 235)),
    ]
    gold_stops = [
        (0.00, (55, 34, 8)),
        (0.20, (152, 102, 20)),
        (0.45, (228, 172, 46)),
        (0.70, (252, 216, 94)),
        (0.88, (255, 242, 158)),
        (1.00, (255, 253, 232)),
    ]
    red_rgb = lut_map(lum, red_stops)
    gold_rgb = lut_map(lum, gold_stops)

    is_closed = mode in ("closed", "fly_r")

    is_cyan_glow = ((G > 160) & (B > 180) & ((B - R) > 40)) | flame_halo
    if mode == "work":
        in_hologram = (xx >= 265) & (xx <= 495) & (yy >= 485) & (yy <= 630)
        is_cyan_glow = is_cyan_glow | in_hologram

    if mode == "fail":
        in_smoke = (xx > 650) & (yy > 410) & (yy < 580)
    else:
        in_smoke = np.zeros_like(lum, dtype=bool)

    warm_excess = (R - B) / 255.0
    if not is_closed:
        in_face_hair = ((xx - 505.0) ** 2 / (242.0 ** 2) + (yy - 365.0) ** 2 / (225.0 ** 2)) < 1.0
        is_warm_bio = in_face_hair & (warm_excess > 0.038)
        in_inner_face = ((xx - 505.0) ** 2 / (182.0 ** 2) + (yy - 418.0) ** 2 / (132.0 ** 2)) < 1.0
        is_protected_bio = is_warm_bio | in_inner_face
    else:
        is_protected_bio = np.zeros_like(lum, dtype=bool)

    if is_closed:
        if mode == "closed":
            cx_h, cy_h = 502.0, 345.0
            in_mask_area = ((xx - cx_h) ** 2 / (186.0 ** 2) + (yy - (cy_h + 25.0)) ** 2 / (170.0 ** 2)) < 1.0
            in_forehead_shield = (yy < 292) & (np.abs(xx - cx_h) < 88 - (yy - 160) * 0.18)
            is_helmet_gold = in_mask_area & (~in_forehead_shield) & (lum > 0.14)
            is_body_gold = (yy > 515) & (lum > 0.49) & (sat < 0.22)
            gold_mask = is_helmet_gold | is_body_gold
        else:
            cx_h, cy_h = 605.0, 360.0
            in_mask_area = ((xx - cx_h) ** 2 / (186.0 ** 2) + (yy - (cy_h + 28.0)) ** 2 / (166.0 ** 2)) < 1.0
            dx_rot = (xx - 615.0) * 0.94 + (yy - 235.0) * 0.34
            dy_rot = -(xx - 615.0) * 0.34 + (yy - 235.0) * 0.94
            in_forehead_shield = (dy_rot < 68.0) & (np.abs(dx_rot) < 84.0 - dy_rot * 0.22)
            is_helmet_gold = in_mask_area & (~in_forehead_shield) & (lum > 0.14)
            is_body_gold = (yy > 510) & (lum > 0.49) & (sat < 0.22)
            gold_mask = is_helmet_gold | is_body_gold
    else:
        is_top_crest = (yy < 165) & (np.abs(xx - 502.0) < 115) & (lum > 0.18)
        is_silver_armor = (lum > 0.49) & (sat < 0.22) & (~is_protected_bio)
        gold_mask = is_top_crest | is_silver_armor

    gold_weight = ndimage.gaussian_filter(gold_mask.astype(np.float32), sigma=2.2)
    armor_rgb = red_rgb * (1.0 - gold_weight[:, :, None]) + gold_rgb * gold_weight[:, :, None]

    recolor_mask = (~is_protected_bio) & (~is_cyan_glow) & (~in_smoke) & (alpha > 0.01)
    rm_smooth = ndimage.gaussian_filter(recolor_mask.astype(np.float32), sigma=1.5)[:, :, None]

    final_rgb = arr * (1.0 - rm_smooth) + armor_rgb * rm_smooth

    if np.any(flame_halo):
        final_rgb[flame_halo, 0] = np.clip(arr[flame_halo, 0] * 0.22, 0, 255)
        final_rgb[flame_halo, 1] = np.clip(arr[flame_halo, 1] * 0.88 + 30, 0, 255)
        final_rgb[flame_halo, 2] = 255.0

    rgba = np.zeros((H, W, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.clip(final_rgb, 0, 255).astype(np.uint8)
    rgba[:, :, 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)
    out_img = Image.fromarray(rgba, mode="RGBA")

    # 3. Add Glowing Arc Reactor on Chest + Soft Anime Tony Stark Goatee
    fx_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dfx = ImageDraw.Draw(fx_layer)

    rx, ry = (546, 626) if is_flying else (502, 596)
    dfx.ellipse([rx - 34, ry - 34, rx + 34, ry + 34], fill=(15, 165, 255, 90))
    dfx.ellipse([rx - 22, ry - 22, rx + 22, ry + 22], fill=(35, 225, 255, 215))
    dfx.polygon([(rx - 17, ry - 10), (rx + 17, ry - 10), (rx, ry + 18)], fill=(235, 254, 255, 255))
    dfx.ellipse([rx - 9, ry - 9, rx + 9, ry + 9], fill=(255, 255, 255, 255))

    if not is_closed:
        beard_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        db = ImageDraw.Draw(beard_layer)
        bx = 502
        by = 456 if mode == "wave" else (464 if mode == "fail" else 468)
        db.polygon(
            [
                (bx - 40, by + 6),
                (bx - 15, by - 5),
                (bx, by - 2),
                (bx + 15, by - 5),
                (bx + 40, by + 6),
                (bx + 34, by + 12),
                (bx + 14, by + 5),
                (bx - 14, by + 5),
                (bx - 34, by + 12),
            ],
            fill=(42, 25, 20, 210),
        )
        cy_chin = 506 if mode == "wave" else 500
        db.polygon(
            [
                (bx - 24, cy_chin - 2),
                (bx - 6, cy_chin - 7),
                (bx + 6, cy_chin - 7),
                (bx + 24, cy_chin - 2),
                (bx + 16, cy_chin + 9),
                (bx - 16, cy_chin + 9),
            ],
            fill=(42, 25, 20, 220),
        )
        beard_layer = beard_layer.filter(ImageFilter.GaussianBlur(radius=1.6))
        out_img.alpha_composite(beard_layer)

    out_img.alpha_composite(fx_layer)
    return out_img


def shift_gaze_on_open_master(
    master_open: Image.Image,
    master_fail: Image.Image,
    gx: float,
    gy: float,
    blink: bool = False,
) -> Image.Image:
    """
    Preserves 100% of the Octane 3D eye rendering by warping/translating the actual
    Octane 3D iris pixels inside the eye socket, or compositing the 3D closed eyes from master_fail!
    """
    im = master_open.copy()
    if blink:
        # Composite the soft 3D closed eyes from master_fail onto master_open!
        arr_open = np.array(im, dtype=np.float32)
        arr_fail = np.array(master_fail, dtype=np.float32)
        H, W, _ = arr_open.shape
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        eye_band = ((xx - 502.0) ** 2 / (145.0 ** 2) + (yy - 404.0) ** 2 / (42.0 ** 2)) < 1.0
        w = ndimage.gaussian_filter(eye_band.astype(np.float32), sigma=6.0)[:, :, None]
        blended = arr_open * (1.0 - w) + arr_fail * w
        return Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8), mode="RGBA")

    if abs(gx) < 0.02 and abs(gy) < 0.02:
        return im

    arr = np.array(im, dtype=np.float32)
    out = arr.copy()
    H, W, _ = arr.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # Smooth local displacement field inside each eye socket so the real 3D Octane iris shifts cleanly!
    dx = gx * 12.5
    dy = gy * 9.0
    for ex, ey in [(430.0, 404.0), (569.0, 404.0)]:
        dist2 = ((xx - ex) / 36.0) ** 2 + ((yy - ey) / 32.0) ** 2
        falloff = np.exp(-dist2 * 1.65) * (dist2 < 1.35)
        src_x = np.clip(np.round(xx - dx * falloff).astype(np.int32), 0, W - 1)
        src_y = np.clip(np.round(yy - dy * falloff).astype(np.int32), 0, H - 1)
        region = dist2 < 1.25
        out[region] = arr[src_y[region], src_x[region]]

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), mode="RGBA")


def place_in_cell_with_particles(
    sprite_1024: Image.Image,
    dx: float = 0.0,
    dy: float = 0.0,
    angle_deg: float = 0.0,
    phase: float = 0.0,
    particle_mode: str = "hover",
    particle_count: int = 22,
    extra_thruster_boost: float = 1.0,
) -> Image.Image:
    crop_box = (106, 86, 918, 898)
    cropped = sprite_1024.crop(crop_box)
    if abs(angle_deg) > 0.1:
        cropped = cropped.rotate(angle_deg, resample=Image.Resampling.BICUBIC, expand=False)

    target_size = 172
    scaled = cropped.resize((target_size, target_size), resample=Image.Resampling.LANCZOS)

    cell = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    fx_back = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    fx_front = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
    db = ImageDraw.Draw(fx_back)
    df = ImageDraw.Draw(fx_front)

    px_paste = int(round((CELL_W - target_size) / 2.0 + dx))
    py_paste = int(round(16.0 + dy))

    cx = CELL_W // 2 + int(dx)
    boot_y = py_paste + 154

    if extra_thruster_boost > 0.2 and particle_mode != "none":
        pulse = 1.0 + 0.25 * math.sin(phase * 2.0 * math.pi)
        for side in (-1, 1):
            bx = cx + side * 12
            by = min(198, boot_y)
            r_glow = int(7 * extra_thruster_boost * pulse)
            db.ellipse([bx - r_glow, by - 4, bx + r_glow, min(203, by + r_glow + 4)], fill=(18, 175, 255, 95))
            ring_y = min(202, by + int(((phase * 2.0) % 1.0) * 8))
            df.ellipse([bx - 5, ring_y - 2, bx + 5, ring_y + 2], outline=(210, 250, 255, 210))

    if particle_count > 0 and particle_mode != "none":
        for i in range(particle_count):
            p_ph = (phase + i * 0.127) % 1.0
            ang = i * 2.39996 + phase * 2.0 * math.pi
            is_gold = i % 3 == 0
            c_core = (255, 250, 215, 250) if is_gold else (235, 254, 255, 250)
            c_glow = (255, 190, 45, 145) if is_gold else (25, 215, 255, 155)

            if particle_mode == "fly_r":
                px = int(cx - 16 - p_ph * 52 + 6 * math.sin(ang))
                py = int(boot_y - 22 + (i % 6) * 6 + p_ph * 16 + 4 * math.cos(ang))
            elif particle_mode == "fly_l":
                px = int(cx + 16 + p_ph * 52 + 6 * math.sin(ang))
                py = int(boot_y - 22 + (i % 6) * 6 + p_ph * 16 + 4 * math.cos(ang))
            else:
                ring_r = 18.0 + (i % 4) * 9.5
                px = int(cx + ring_r * math.cos(ang * 0.85))
                py = int(boot_y + 6 - p_ph * 68.0)

            px = max(10, min(CELL_W - 10, px))
            py = max(116, min(201, py))

            rad = 1.2 + 0.9 * math.sin(p_ph * math.pi)
            r_i = max(1, int(round(rad)))
            df.ellipse([px - r_i - 1, py - r_i - 1, px + r_i + 1, py + r_i + 1], fill=c_glow)
            df.ellipse([px - r_i + 1, py - r_i + 1, px + r_i - 1, py + r_i - 1], fill=c_core)

    cell.alpha_composite(fx_back)
    cell.alpha_composite(scaled, (px_paste, py_paste))
    cell.alpha_composite(fx_front)
    return clean_transparent_rgb(cell)


def build_all(source_dir: Path = Path("source_renders"), out_dir_path: Path = Path("assets")) -> None:
    out_dir = Path("/working_dir/c_09c5abb54b1bb6d6/artifacts/file_generation/ttl=63d/output")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Extracting and recoloring 6 Octane 3D master renders...")
    m_open = extract_and_recolor_master(IMG_OPEN, "open")
    m_closed = extract_and_recolor_master(IMG_CLOSED, "closed")
    m_wave = extract_and_recolor_master(IMG_WAVE, "wave")
    m_fly_r = extract_and_recolor_master(IMG_FLY_R, "fly_r")
    m_fly_l = m_fly_r.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    m_work = extract_and_recolor_master(IMG_WORK, "work")
    m_fail = extract_and_recolor_master(IMG_FAIL, "fail")
    m_open_blink = shift_gaze_on_open_master(m_open, m_fail, 0.0, 0.0, blink=True)

    atlas_v2 = Image.new("RGBA", (COLS * CELL_W, ROWS_V2 * CELL_H), (0, 0, 0, 0))

    # Row 0: idle (6 frames)
    idle_masters = [m_open, m_open, m_open_blink, m_open, m_closed, m_closed]
    idle_dy = [0.0, -2.0, -3.5, -2.0, -1.0, 0.0]
    for c in range(6):
        cell = place_in_cell_with_particles(
            idle_masters[c],
            dy=idle_dy[c],
            phase=c / 6.0,
            particle_mode="hover",
            particle_count=24,
            extra_thruster_boost=0.9,
        )
        atlas_v2.paste(cell, (c * CELL_W, 0 * CELL_H))

    # Row 1: running-right (8 frames)
    for c in range(8):
        ph = c / 8.0
        dy = -2.0 + 3.0 * math.sin(ph * 2 * math.pi)
        ang = -2.5 * math.cos(ph * 2 * math.pi)
        cell = place_in_cell_with_particles(
            m_fly_r,
            dx=2.0,
            dy=dy,
            angle_deg=ang,
            phase=ph,
            particle_mode="fly_r",
            particle_count=34,
            extra_thruster_boost=1.25,
        )
        atlas_v2.paste(cell, (c * CELL_W, 1 * CELL_H))

    # Row 2: running-left (8 frames)
    for c in range(8):
        ph = c / 8.0
        dy = -2.0 + 3.0 * math.sin(ph * 2 * math.pi)
        ang = 2.5 * math.cos(ph * 2 * math.pi)
        cell = place_in_cell_with_particles(
            m_fly_l,
            dx=-2.0,
            dy=dy,
            angle_deg=ang,
            phase=ph,
            particle_mode="fly_l",
            particle_count=34,
            extra_thruster_boost=1.25,
        )
        atlas_v2.paste(cell, (c * CELL_W, 2 * CELL_H))

    # Row 3: waving (4 frames)
    wave_angles = [0.0, -2.5, 2.5, 0.0]
    wave_dy = [0.0, -2.0, -2.5, 0.0]
    for c in range(4):
        cell = place_in_cell_with_particles(
            m_wave,
            dy=wave_dy[c],
            angle_deg=wave_angles[c],
            phase=c / 4.0,
            particle_mode="hover",
            particle_count=26,
            extra_thruster_boost=0.85,
        )
        atlas_v2.paste(cell, (c * CELL_W, 3 * CELL_H))

    # Row 4: jumping (5 frames)
    jump_masters = [m_open, m_closed, m_closed, m_open, m_open]
    jump_dy = [2.0, -10.0, -16.0, -8.0, 0.0]
    jump_pcounts = [16, 0, 0, 0, 16]
    jump_boost = [0.5, 0.0, 0.0, 0.0, 0.5]
    for c in range(5):
        cell = place_in_cell_with_particles(
            jump_masters[c],
            dy=jump_dy[c],
            phase=c / 5.0,
            particle_mode="hover" if jump_pcounts[c] > 0 else "none",
            particle_count=jump_pcounts[c],
            extra_thruster_boost=jump_boost[c],
        )
        atlas_v2.paste(cell, (c * CELL_W, 4 * CELL_H))

    # Row 5: failed (8 frames)
    for c in range(8):
        ph = c / 8.0
        dy = 1.5 * math.sin(ph * 2 * math.pi)
        ang = 1.5 * math.cos(ph * 2 * math.pi)
        cell = place_in_cell_with_particles(
            m_fail,
            dy=dy,
            angle_deg=ang,
            phase=ph,
            particle_mode="none",
            particle_count=0,
            extra_thruster_boost=0.0,
        )
        atlas_v2.paste(cell, (c * CELL_W, 5 * CELL_H))

    # Row 6: waiting (6 frames)
    wait_masters = [m_open, m_wave, m_wave, m_open, m_open_blink, m_open]
    for c in range(6):
        ph = c / 6.0
        cell = place_in_cell_with_particles(
            wait_masters[c],
            dy=-2.0 * math.sin(ph * 2 * math.pi),
            angle_deg=2.0 * math.sin(ph * 2 * math.pi),
            phase=ph,
            particle_mode="hover",
            particle_count=20,
            extra_thruster_boost=0.8,
        )
        atlas_v2.paste(cell, (c * CELL_W, 6 * CELL_H))

    # Row 7: running / active task work (6 frames)
    for c in range(6):
        ph = c / 6.0
        gaze_work = shift_gaze_on_open_master(m_work, m_fail, 0.35 * math.sin(ph * 2 * math.pi), 0.15)
        cell = place_in_cell_with_particles(
            gaze_work,
            dy=-2.0 * math.sin(ph * 2 * math.pi),
            phase=ph,
            particle_mode="hover",
            particle_count=28,
            extra_thruster_boost=0.95,
        )
        atlas_v2.paste(cell, (c * CELL_W, 7 * CELL_H))

    # Row 8: review (6 frames)
    for c in range(6):
        ph = c / 6.0
        gaze_rev = shift_gaze_on_open_master(
            m_work if c in (1, 2, 3, 4) else m_open, m_fail, 0.45 * math.cos(ph * 2 * math.pi), 0.2
        )
        cell = place_in_cell_with_particles(
            gaze_rev,
            dy=-1.5 * math.sin(ph * 2 * math.pi),
            angle_deg=-2.0 * math.sin(ph * 2 * math.pi),
            phase=ph,
            particle_mode="hover",
            particle_count=20,
            extra_thruster_boost=0.8,
        )
        atlas_v2.paste(cell, (c * CELL_W, 8 * CELL_H))

    # Rows 9 & 10: 16 Clockwise Look Directions (000 = up, 090 = right, 180 = down, 270 = left)
    for idx in range(16):
        deg = idx * 22.5
        rad = math.radians(deg)
        gx = math.sin(rad)
        gy = -math.cos(rad)
        row_idx = 9 + (idx // 8)
        col_idx = idx % 8
        looked = shift_gaze_on_open_master(m_open, m_fail, gx, gy, blink=False)
        cell = place_in_cell_with_particles(
            looked,
            dx=gx * 1.5,
            dy=gy * 1.2,
            angle_deg=-gx * 2.2,
            phase=0.0,
            particle_mode="hover",
            particle_count=14,
            extra_thruster_boost=0.85,
        )
        atlas_v2.paste(cell, (col_idx * CELL_W, row_idx * CELL_H))

    atlas_v2 = clean_transparent_rgb(atlas_v2)
    atlas_v1 = atlas_v2.crop((0, 0, COLS * CELL_W, ROWS_V1 * CELL_H))

    v2_png = out_dir / "ironman_funko_anime_v2_spritesheet.png"
    v2_webp = out_dir / "ironman_funko_anime_v2_spritesheet.webp"
    v1_png = out_dir / "ironman_funko_anime_v1_spritesheet.png"

    atlas_v2.save(v2_png, format="PNG", optimize=True)
    atlas_v2.save(v2_webp, format="WEBP", lossless=True)
    atlas_v1.save(v1_png, format="PNG", optimize=True)

    showcase = Image.new("RGBA", (320 * 3, 340 * 2), (18, 20, 26, 255))
    for idx, sp in enumerate([m_open, m_closed, m_wave, m_fly_r, m_work, m_fail]):
        thumb = sp.crop((106, 86, 918, 898)).resize((300, 300), Image.Resampling.LANCZOS)
        px = (idx % 3) * 320 + 10
        py = (idx // 3) * 340 + 20
        showcase.paste(thumb, (px, py), thumb)
    showcase_path = out_dir / "ironman_funko_anime_showcase.png"
    showcase.save(showcase_path, format="PNG")
    print("Saved all outputs successfully!")




def main():
    parser = argparse.ArgumentParser(description="Build ChatGPT Pets Iron Man Spritesheet from 3D Renders")
    parser.add_argument("--source-dir", type=Path, default=Path("source_renders"), help="Directory containing master 3D render poses")
    parser.add_argument("--out-dir", type=Path, default=Path("assets"), help="Output directory for spritesheets and showcase")
    args = parser.parse_args()

    required_renders = [
        "watermarked_img_8696603795617303220.jpg",
        "watermarked_img_3248917049044536173.jpg",
        "watermarked_img_2552612298112778207.jpg",
        "watermarked_img_14898378355863852025.jpg",
        "watermarked_img_2810960109273726636.jpg",
        "watermarked_img_8850624452338638387.jpg",
    ]
    missing = [f for f in required_renders if not (args.source_dir / f).exists()]
    if missing:
        print(f"Notice: Raw 3D source renders in '{args.source_dir}' are missing {len(missing)} files:")
        for m in missing:
            print(f"  - {m}")
        print("Production-ready spritesheets are pre-built in 'assets/'.")
        print("To re-render from custom poses, place matching JPEG renders in 'source_renders/'.")
        return

    build_all(source_dir=args.source_dir, out_dir_path=args.out_dir)


if __name__ == "__main__":
    main()
