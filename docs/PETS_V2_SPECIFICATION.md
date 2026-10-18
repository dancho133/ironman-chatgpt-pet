# ChatGPT Pets Protocol: Full Technical Specification (v2 & v1 Standards)

This document provides the definitive technical specification and atlas architecture rules for custom animated companions (**ChatGPT Pets**) running in **ChatGPT Desktop / Work Mode**.

---

## 1. Atlas Architecture & Grid Geometry

The ChatGPT Pets runtime uses an image atlas (spritesheet) with a fixed uniform cell grid. The engine extracts individual frames by computing cell bounding boxes from column and row indices:

$$	ext{box} = (c \cdot 192,\, r \cdot 208,\, (c+1) \cdot 192,\, (r+1) \cdot 208)$$

### 1.1 Standards Comparison: v1 vs v2

| Parameter | Standard v1 (Classic) | Standard v2 (Extended / Cursor Tracking) |
| :--- | :--- | :--- |
| **Canvas Width** | **1536 px** | **1536 px** |
| **Canvas Height** | **1872 px** | **2288 px** |
| **Grid Dimensions** | **8 columns × 9 rows** (72 cells) | **8 columns × 11 rows** (88 cells) |
| **Cell Size (W × H)** | **192 × 208 px** | **192 × 208 px** |
| **Total Active Frames** | **57 frames** | **73 frames** (57 core + 16 cursor tracking) |
| **Unused (Transparent) Cells** | **15 cells** | **15 cells** |
| **Color Mode** | **RGBA** (8-bit per channel) | **RGBA** (8-bit per channel) |
| **Supported Formats** | PNG, WebP (lossless) | PNG, WebP (lossless) |
| **Max File Size** | 20 MB (20,971,520 bytes) | 20 MB (20,971,520 bytes) |

---

## 2. Animation Rows Specification

Every row corresponds to a specific behavioral state. Active frames must be packed consecutively starting from **column 0**. Any remaining cells in that row **must be 100% transparent** (`alpha == 0`).

| Row Index | Name | Active Frames | Unused (Empty) Cells | Target FPS | Loop Type | Description |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| **Row 0** | **Idle** | **6** (cols 0–5) | 2 (cols 6–7) | 8–10 FPS | Loop | Default resting state; subtle breathing, visor glint, repulsor hum. |
| **Row 1** | **Walk / Pacing** | **8** (cols 0–7) | 0 | 10–12 FPS | Loop | Pacing across workspace floor or hovering gently forward. |
| **Row 2** | **Run / Dash** | **8** (cols 0–7) | 0 | 12–15 FPS | Loop | High-speed dash or rocket boost flight. |
| **Row 3** | **Rest / Sit** | **4** (cols 0–3) | 4 (cols 4–7) | 4–6 FPS | Ping-Pong / Hold | Sitting down, resting armor, power-save stance. |
| **Row 4** | **Thinking / Processing** | **5** (cols 0–4) | 3 (cols 5–7) | 6–8 FPS | Loop | Active reasoning, F.R.I.D.A.Y. HUD holograms, Tony calculating. |
| **Row 5** | **Action / Working** | **8** (cols 0–7) | 0 | 10–12 FPS | Loop | Rapid typing, repulsor adjustments, gadget fabrication. |
| **Row 6** | **Success / Celebration** | **6** (cols 0–5) | 2 (cols 6–7) | 8–10 FPS | One-Shot | Task accomplished: celebratory fist pump, salute, thruster burst. |
| **Row 7** | **Failure / Confused** | **6** (cols 0–5) | 2 (cols 6–7) | 6–8 FPS | One-Shot | Error encountered: armor sputter, helmet scratching, steam release. |
| **Row 8** | **Sleep / Nap** | **6** (cols 0–5) | 2 (cols 6–7) | 4–5 FPS | Loop | Extended inactivity: Tony dozing off, arc reactor gentle pulse. |
| **Row 9** | **Cursor Tracking (000°–157.5°)** | **8** (cols 0–7) | 0 | Responsive | Gaze Matrix | Directional gaze angles 1 through 8 (North to South-East). |
| **Row 10** | **Cursor Tracking (180°–337.5°)** | **8** (cols 0–7) | 0 | Responsive | Gaze Matrix | Directional gaze angles 9 through 16 (South to North-North-West). |

---

## 3. Cursor Tracking Geometry (v2 Only)

Rows 9 and 10 provide 16 discrete look directions in clockwise order starting from **straight up (000°)** with increments of **22.5°**:

```
                   0: 000.0° (N / Up)
            15: 337.5°          1: 022.5°
         14: 315.0°                2: 045.0° (NE)
       13: 292.5°                    3: 067.5°
   12: 270.0° (W)      [PET]       4: 090.0° (E / Right)
       11: 247.5°                    5: 112.5°
         10: 225.0°                6: 135.0° (SE)
            9: 202.5°           7: 157.5°
                   8: 180.0° (S / Down)
```

| Index | Row | Col | Angle (deg) | Compass | Look Vector $(g_x, g_y)$ | Head / Eye Shift |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0** | Row 9 | Col 0 | $0.0^\circ$ | **N (Up)** | $(0.00, -1.00)$ | Head tilted up, eyes looking directly up |
| **1** | Row 9 | Col 1 | $22.5^\circ$ | NNE | $(+0.38, -0.92)$ | Looking upper-right |
| **2** | Row 9 | Col 2 | $45.0^\circ$ | **NE** | $(+0.71, -0.71)$ | Looking diagonal upper-right |
| **3** | Row 9 | Col 3 | $67.5^\circ$ | ENE | $(+0.92, -0.38)$ | Looking mostly right, slight up |
| **4** | Row 9 | Col 4 | $90.0^\circ$ | **E (Right)** | $(+1.00, 0.00)$ | Looking directly right |
| **5** | Row 9 | Col 5 | $112.5^\circ$ | ESE | $(+0.92, +0.38)$ | Looking lower-right |
| **6** | Row 9 | Col 6 | $135.0^\circ$ | **SE** | $(+0.71, +0.71)$ | Looking diagonal lower-right |
| **7** | Row 9 | Col 7 | $157.5^\circ$ | SSE | $(+0.38, +0.92)$ | Looking mostly down, slight right |
| **8** | Row 10 | Col 0 | $180.0^\circ$ | **S (Down)** | $(0.00, +1.00)$ | Looking directly down |
| **9** | Row 10 | Col 1 | $202.5^\circ$ | SSW | $(-0.38, +0.92)$ | Looking mostly down, slight left |
| **10** | Row 10 | Col 2 | $225.0^\circ$ | **SW** | $(-0.71, +0.71)$ | Looking diagonal lower-left |
| **11** | Row 10 | Col 3 | $247.5^\circ$ | WSW | $(-0.92, +0.38)$ | Looking lower-left |
| **12** | Row 10 | Col 4 | $270.0^\circ$ | **W (Left)** | $(-1.00, 0.00)$ | Looking directly left |
| **13** | Row 10 | Col 5 | $292.5^\circ$ | WNW | $(-0.92, -0.38)$ | Looking upper-left |
| **14** | Row 10 | Col 6 | $315.0^\circ$ | **NW** | $(-0.71, -0.71)$ | Looking diagonal upper-left |
| **15** | Row 10 | Col 7 | $337.5^\circ$ | NNW | $(-0.38, -0.92)$ | Looking mostly up, slight left |

---

## 4. Transparency & Clean Alpha Rules

### 4.1 Unused Cells
A total of **15 cells** are unused across the atlas:
- Row 0: 2 cells (cols 6–7)
- Row 3: 4 cells (cols 4–7)
- Row 4: 3 cells (cols 5–7)
- Row 6: 2 cells (cols 6–7)
- Row 7: 2 cells (cols 6–7)
- Row 8: 2 cells (cols 6–7)

Every pixel in an unused cell **must have $\alpha = 0$**. If even one pixel has $\alpha > 0$, the OpenAI Pets preflight validator rejects the upload with error `artwork_in_unused_cell`.

### 4.2 Clean Alpha (Zero RGB Residue)
When transparent pixels contain hidden RGB values (e.g. `RGBA(255, 255, 255, 0)`), PNG / WebP compression engines can bleed those color values into semi-transparent border edges, creating an unsightly white or dark halo.

To prevent this:
```python
arr = np.array(image, dtype=np.uint8)
arr[arr[:, :, 3] < 8] = (0, 0, 0, 0)  # Zero out RGB wherever alpha is near-zero
clean_image = Image.fromarray(arr, mode="RGBA")
```

---

## 5. API Life Cycle

```
[Local Spritesheet]
       │
       ▼
validate_pet_spritesheet (Check dimensions, cell grid, alpha mask)
       │
       ▼ (valid=true)
prepare_pet_upload (Uploads asset & returns upload_session_id)
       │
       ▼
create_pet / update_pet (Consumes upload_session_id, sets name & description)
       │
       ▼
select_pet (Activates companion in ChatGPT Work / Desktop UI)
       │
       ▼
share_pet (Generates shareable public /s/sharepet_* URL)
```
