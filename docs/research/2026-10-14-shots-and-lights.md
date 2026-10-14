# Phase 0 part 4 — shots, lights, scale, shape keys, unresolved images — 2026-10-14

**Connected Blender: 5.1.2** (`bpy.app.version_string`). **Frame before: 971, `is_dirty` False. Frame after every call: 971, `is_dirty` False.** Under the one-time exception I changed the frame and, for the renders, `render.filepath`, `resolution_percentage`, `eevee.taa_render_samples` and `image_settings.file_format`; each was restored in a `finally` block and read back (filepath `S:\works\Blender creations\Stomach all parts\`, 100%, 40 samples, PNG). Nothing saved. No image/video opened. Source: `execute_blender_code` unless noted.

## TL;DR
- The four shots are different parts: 361 = PART_W1_GEJ_ZLine (99% of rays), 531 = Stomach (100%), 731 = Stomach 78.5% + PART_W5_Antrum 21.3%, **971 = PART_9_Duodenal bulb (100%), not the antrum**.
- Tip light is keyed 76.8 / 500 / 163.9 / 26.1 W while the wall distance changes 2.6–3.9 / 5.8–14.2 / 1.4–4.5 / 0.62–2.1 units, so most of the power spread is distance compensation; the resulting 25% renders have mean luminance 0.31 / 0.19 / 0.54 / 0.36.
- Four lights are `hide_viewport` True and `hide_render` False (two 1000 W points, two 12 W areas) and are included in these renders; their inverse-square share at the shots is unoccluded-estimate only.
- Part boundaries: W1/W3 coincide (0.0001), but gaps exist elsewhere (Duodenal–Antrum 0.41, Esophagus–W1 0.20, Duodenal–Stomach 0.21, Antrum–Stomach 0.0175 units).
- `Stomach_Baked` / `Stomach_HDRP` have 1 user each but no shader node uses them; their files exist in `E:\works\Blender creations\Textures\`, one folder above where the .blend looks. `Colon_image` was not found under `E:\works`.

## Task 1 — Shots (facts)
Method: 48 x 27 = 1,296 rays from Cam_Endoscope through the 90° x 16:9 frustum (`Scene.ray_cast` on the evaluated depsgraph). Ray cast sees only objects present in the evaluated viewport depsgraph, so objects hidden in the view layer (PART_11_Colon, Cylinder, which are render-enabled) cannot be hit; they are listed separately by bounding box. "BBox share" = clamped screen-space bounding-box area (an upper bound, not coverage). Distances are scene units from the camera origin to the hit point.

| Frame | Camera location | Ray-hit share by object | Material slot share (of rays) | Centre-ray hit | Distance min / p10 / median / p90 / max |
|---|---|---|---|---|---|
| 361 | (12.677, 0.811, 41.925) | PART_W1_GEJ_ZLine 0.992; Esophagus Tube 0.008 | MAT_W1_GEJ_ZLine 0.992; MAT_Esophagus_Tube 0.008 | W1, 3.3495 | 2.587 / 2.641 / 2.822 / 3.150 / 3.900 |
| 531 | (12.852, 3.290, 33.615) | Stomach 1.000 | MAT_W3_Fundus_Mucosa 1.000 | Stomach, 13.4358 | 5.847 / 6.860 / 8.727 / 11.933 / 14.162 |
| 731 | (13.695, -5.095, 25.414) | Stomach 0.785; PART_W5_Antrum 0.213; PART_9_Duodenal bulb 0.002 | MAT_W3_Fundus_Mucosa 0.785; MAT_Antrum_Mucosa 0.179; MAT_W6_Pylorus_Ring 0.034; MAT_DuodenalBulb_Mucosa 0.002 | Antrum, 2.4126 | 1.400 / 1.570 / 2.064 / 2.577 / 4.546 |
| 971 | (13.082, -8.771, 26.488) | PART_9_Duodenal bulb 1.000 | MAT_DuodenalBulb_Mucosa 1.000 | Duodenal bulb, 1.8903 | 0.622 / 0.716 / 1.263 / 1.954 / 2.109 |

No ray missed in any frame (0 of 1,296). Distance along the view axis (centre ray) is the "centre-ray" column.

Bounding-box projection (render-enabled meshes with part of the box in front of the camera; share is the bbox proxy, `*` = hidden in the view layer, so not ray-castable):
- 361: PART_W1_GEJ_ZLine 1.00, PART_W3_Fundus 1.00, Stomach 0.905, Esophagus Tube 0.024, Cylinder* 0.014.
- 531: PART_W3_Fundus 0.95, PART_11_Colon* 0.584, Cylinder* 0.431, Stomach 0.361, PART_9_Duodenal bulb 0.025, PART_W5_Antrum 0.015.
- 731: Stomach 0.909, PART_W5_Antrum 0.658, PART_9_Duodenal bulb 0.542, PART_11_Colon* 0.135, Esophagus Tube 0.018.
- 971: PART_9_Duodenal bulb 0.546, Stomach 0.262, Cylinder* 0.031, PART_11_Colon* 0.02.
(Boxes overlap parts that lie behind others; W3 overlapping W1 and Stomach in the box does not mean it is visible.)

Light energy at each frame (W) — all lights, as evaluated at that frame:

| Frame | Light_Endoscope_Tip | Light (POINT) | Light.001 (POINT) | Light_Fill_1 (AREA) | Light_Fill_2 (AREA) |
|---|---|---|---|---|---|
| 361 | 76.79 | 1000 | 1000 | 12 | 12 |
| 531 | 500 | 1000 | 1000 | 12 | 12 |
| 731 | 163.88 | 1000 | 1000 | 12 | 12 |
| 971 | 26.11 | 1000 | 1000 | 12 | 12 |

Lights with `hide_viewport` True and `hide_render` False: **Light, Light.001, Light_Fill_1, Light_Fill_2** (energies in the table above; none animated). Light_Endoscope_Tip is `hide_viewport` False, `hide_render` False.

Interpretation (hypothesis)
- Unoccluded inverse-square illuminance proxy (power / distance², tip at its offset 0.15 m, hidden points at their distance from the camera ~31 and ~24.5 units; area lights ignored): at 971 tip ≈ 26/(1.26)² ≈ 16 vs Light.001 ≈ 1.7 (~10%); at 531 tip ≈ 500/(8.7)² ≈ 6.6 vs Light.001 ≈ 2.5 (~35%). The stomach walls probably occlude much of that. Confidence: low; I did not test occlusion.
- The tip keys look like a manual auto-exposure compensating for distance (power rises with wall distance). Confidence: medium.

## Task 2 — Numbers-only renders (25% = 480 x 270, 16 samples, EEVEE, all `hide_render` False lights, camera Cam_Endoscope)
Files: `renders/audit/shot_f361_25pct.png`, `shot_f531_25pct.png`, `shot_f731_25pct.png`, `shot_f971_25pct.png`. Stats from `tools/render_stats.py` (Rec.709 luminance of stored 0–1 values).

| Frame | Render time (s) | File size (B) | Mean | p1 | p50 | p99 | p99.9 | Share ≥ 0.98 | Share ≤ 0.02 | Firefly proxy |
|---|---|---|---|---|---|---|---|---|---|---|
| 361 | 54.85 | 162,980 | 0.3116 | 0.0463 | 0.3133 | 0.5637 | 0.7989 | 0.000054 | 0.000193 | 0 |
| 531 | 58.12 | 175,822 | 0.1895 | 0.1014 | 0.1843 | 0.3209 | 0.3559 | 0 | 0 | 0 |
| 731 | 44.78 | 204,703 | 0.5394 | 0.2714 | 0.5481 | 0.6980 | 0.7956 | 0.00027 | 0 | 0 |
| 971 | 44.75 | 234,165 | 0.3604 | 0.1462 | 0.2738 | 0.6806 | 0.8129 | 0.000386 | 0 | 0 |
Settings restored and read back after the renders (above). Process memory not measured this time.

Interpretation
- Mean luminance spans 0.19–0.54 (2.8x) across the four shots; p99 spans 0.32–0.70. No clipping beyond ≤0.04% of pixels ≥ 0.98 and no fireflies by the proxy.

## Task 3 — Shape keys, boundaries (frame 971 geometry unless noted)
Shape keys (all keys are relative to `Basis`; no key has a vertex group; none muted). Animated frames/values from the Key datablock's F-curves; "at" = value at frames 361/531/731/971.

| Object | Key (current value @971) | Animated | Values at 361 / 531 / 731 / 971 |
|---|---|---|---|
| PART_W1_GEJ_ZLine | Open (0) | 22 keys, frames 1–1514, range 0–1 | 0.397 / 0 / 0 / 0 |
| | Squeeze (0) | 13 keys, 1–1610, 0–0.85 | 0 / 0 / 0 / 0 |
| | Breath (-0.143) | 13 keys, 200–1604, -0.773–0.786 | -0.289 / -0.698 / -0.497 / -0.143 |
| | Pulse (0.003) | 68 keys, 200–1621, 0–0.977 | 0.62 / 0.097 / 0.031 / 0.003 |
| | CardiaOpen (0.206) | not animated | 0.206 |
| PART_W5_Antrum | Pylorus_Close (0) | 18 keys, 1–1630, 0–1 | 0 / 0 / 0 / 0 |
| | Pylorus_Open (0.55) | 18 keys, 1–1630, 0–1 | 0.45 / 0.45 / 0.509 / 0.55 |
| PART_W0_Hypopharynx | Key 1 (0) | no | 0 |
| PART_W2_Cardia_Retroflexed | Key 1 (0) | no | 0 |
| Esophagus Tube | Key 1–4 (0) | no | 0 |
| Breathing tube | Key 1–14 (0) | no | 0 |
| Stomach, W3, W4, Duodenal, Colon, Cylinder | none (Stomach has Basis only) | | |
Note: PART_W5_Antrum's Basis value is 0 and PART_W1's Basis value 1 (Basis is the reference key).

Boundary edges (evaluated mesh at frame 971, objects not hidden in view layer / not render-disabled) and face counts:

| Object | Faces (base) | Faces (evaluated) | Boundary edges (evaluated) |
|---|---|---|---|
| Stomach | 293,098 | 293,098 | 665 |
| PART_W3_Fundus | 50,755 | 51,178 | 491 |
| PART_W1_GEJ_ZLine | 11,680 | 11,680 | 320 |
| PART_W5_Antrum | 19,017 | 19,017 | 274 |
| PART_9_Duodenal bulb | 46,626 | 46,626 | 269 |
| Esophagus Tube | 13,998 | **55,992** | 520 |
| PART_W0_Hypopharynx | 36,562 | 36,562 | 0 |
| Breathing tube | 128 | 128 | 64 |
| PART_W2 / PART_W4 / PART_11_Colon / Cylinder / Scope_Shaft | 31,400 / 86,400 / 598,650 / 1,056 / 0 | hidden → evaluated boundary not computed (base-mesh values are in part 3) | |

Minimum distance between boundary vertices of different parts (scene units, world space, frame 971; smallest 14 pairs of those evaluated):
PART_W1_GEJ_ZLine–PART_W3_Fundus **0.0001**; PART_W5_Antrum–Stomach **0.0175**; Esophagus Tube–PART_W1_GEJ_ZLine 0.1984; PART_9_Duodenal bulb–Stomach 0.2063; Breathing tube–Esophagus Tube 0.3979; PART_9_Duodenal bulb–PART_W5_Antrum **0.4105**; Esophagus Tube–Stomach 0.5188; PART_W1–Stomach 0.7364; PART_W3–Stomach 0.9773; Esophagus Tube–PART_W3 2.256; Duodenal–W3 5.907; W3–Antrum 6.012; Esophagus–Duodenal 12.233; Esophagus–Antrum 12.252. W0 has no boundary. Gaps depend on the animated shape keys; I read only frame 971 (could not check other frames without more frame changes).

Interpretation (hypothesis)
- Coincident (≈0.0001) means W1 and W3 boundaries are stitched at 971; the Duodenal–Antrum gap of 0.41 units is large relative to the camera distance of 0.62–2.1 units at frame 971. Confidence: medium that a visible seam/gap region exists near the bulb; I have not viewed it.

## Task 4 — Scale
- `scene.unit_settings`: system METRIC, scale_length 1.0, length_unit METERS.
- Cam_Endoscope: PERSP, 18 mm on 36 mm sensor, FOV **90.0°** horizontal (sensor fit AUTO).
- Tip light radius **0.02** scene units (= 0.02 m under METRIC/scale 1), positioned 0.15 units ahead of the camera origin.
- Object dimensions (x, y, z; scene units, `object.dimensions`): Stomach 11.319 x 14.983 x 28.209; PART_W3_Fundus 11.478 x 9.736 x 18.713; Esophagus Tube 5.042 x 13.529 x 28.168; PART_11_Colon 19.971 x 15.716 x 31.155; Cylinder 2.684 x 8.376 x 66.743; PART_W4_Rugae_Panel 8.961 x 20.738 x 3.391; PART_W1_GEJ_ZLine 2.908 x 5.124 x 6.284; PART_W0_Hypopharynx 2.775 x 4.202 x 3.204; PART_9_Duodenal bulb 2.514 x 2.935 x 3.569; PART_W5_Antrum 1.779 x 2.368 x 1.836; PART_W2_Cardia_Retroflexed 0.816 x 1.017 x 0.904; Breathing tube 1.625 x 3.654 x 1.689.
- Camera-to-surface distance statistics: Task 1 table (0.62–14.16 units overall; medians 2.82 / 8.73 / 2.06 / 1.26).
- Ratios: tip radius / median wall distance = 0.0071 (f361), 0.0023 (f531), 0.0097 (f731), 0.016 (f971).

Interpretation (hypothesis): if one unit is 1 m, the stomach is 28 m long; the scene is clearly not metric-real, so the 0.02 radius is a relative size (0.07% of the stomach length), which makes the tip light a near-point source at every shot. Confidence: medium (scale intent unknown).

## Task 5 — Unresolved images
Filename search under `E:\works` (names only; nothing opened):
- `Stomach_Baked*`: `E:\works\Blender creations\Textures\Stomach_Baked.png`, `Stomach_BakedNormal.png`, `Stomach_BakedDiffuse.png`, `Stomach_BakedGlossy.png`, `Stomach_BakedGlossyLight.png`, `Stomach_baked_key.png`, plus `(Solidified-inside)` variants; Unity copies in `E:\works\Stomach_URP\Assets\Materials\` (Diffuse/Glossy/Normal `(Solidified-inside)` + .meta).
- `Stomach_HDRP*`: `E:\works\NBSoft Completed Projects\Stomach_HDRP.zip`, `E:\works\Unity Projects\Stomach_HDRP\Stomach_HDRP.sln` (project, not an image). The datablock's file name `Stomach_GlossyHDRP.png` exists at `E:\works\Blender creations\Textures\Stomach_GlossyHDRP.png` and in `E:\works\Unity Projects\Stomach_HDRP\Assets\`.
- `Colon_image*`: **no match** under `E:\works` (`E:\works\VR-Colon` exists).

Datablocks (users / fake user / usage):
- `Colon_image.png`: users 1, fake user False; one Image Texture node `Image Texture` in material `material_0` (1 user, on PART_11_Colon) wired to `Principled BSDF` → **Base Color**.
- `Stomach_Baked` (`//Textures\Stomach_BakedNormal.png`): users 1, fake user False; **no material node uses it**.
- `Stomach_HDRP` (`//Textures\Stomach_GlossyHDRP.png`): users 1, fake user False; **no material node uses it**.
- The single user of the latter two is not a shader node; what holds it (for example an image editor) was not identified: could not check.
- The relative path `//Textures` resolves to `E:\works\Blender creations\Stomach all parts\Textures\` (does not exist); the files are at `E:\works\Blender creations\Textures\`, one directory up.

## Task 6 — Contradictions with `2026-10-14-visual-hypotheses.md`
| Item | Verdict | Basis |
|---|---|---|
| V1 inconsistent look | **Supported, refined** | Different materials per shot (W1, W3/Stomach, W3+Antrum+Pylorus, Duodenal) and tip power 26–500 W; but the power largely tracks distance, and measured mean luminance spreads 0.19–0.54. |
| V2 one strong light near camera | **Not contradicted; partly qualified** | Tip is the only viewport-visible light; the four `hide_viewport` lights are render-enabled and included in these renders. Their share is an unoccluded estimate only. |
| V3 rectilinear lens | **Not contradicted** | PERSP 18 mm, FOV 90°, no distortion/vignette nodes (unchanged). |
| V4 colour management | **Not contradicted** | Unchanged. Rendered means are 0.19–0.54 with ≤ 0.04% pixels ≥ 0.98. |
| V5 thorn-like spikes at 731 | **Modifier cause still not supported** | At 731 Stomach is 78.5% of rays at 1.4–4.5 units; Stomach has Basis only (no shape keys) and both displace modifiers at strength 0; Esophagus Tube's GN folds quadruple its faces (13,998 → 55,992) but is 0.8% / 1.8% of the view. Cause unidentified. |
| V5 serrated opening near 361 | **Consistent with data, not proven** | At 361 the shot is 99.2% PART_W1_GEJ_ZLine at 2.6–3.9 units, with animated keys at that frame: Open 0.397, Breath -0.289, Pulse 0.62; W1 has 320 boundary edges and 11,680 faces. |
| V6 antrum fur-like bump at 971 | **Contradicted on the object**: at 971 the frame is 100% PART_9_Duodenal bulb (MAT_DuodenalBulb_Mucosa), distance 0.62–2.1 units; the antrum is not in view (it is 21% of rays only at 731). The bump chain that applies at 971 is the duodenal one (Bump.001 strength 1.0, distance 0.01, noise mapping scale 35, detail 5), so the antrum-material bump values in part 3 are relevant to 731, not 971. |
| V7 small hard highlights | **Not contradicted** | Tip radius 0.02 vs median wall distance 1.26–8.73 gives a near-point source (ratio 0.002–0.016); coat roughness 0.04–0.1 on these materials (part 3). |
| "Hidden" objects | **Unchanged** | PART_11_Colon and Cylinder (render-enabled, view-layer hidden) project into the frame at 531 (colon bbox 0.58), 731 and 971; whether they show in finals is not testable by ray cast: could not check. |

## Could not check
- Whether PART_11_Colon / Cylinder visibly appear in the final render (excluded from the viewport depsgraph).
- Boundary gap distances at frames other than 971.
- Occlusion of the hidden lights by the stomach walls.
- What holds the single user of `Stomach_Baked` / `Stomach_HDRP`.
- Process memory during these renders; any visual content (no image viewed).
