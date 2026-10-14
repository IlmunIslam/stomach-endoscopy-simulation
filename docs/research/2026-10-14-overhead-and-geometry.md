# Phase 0 part 5 — render overhead, GPU memory, spikes, hidden objects, boundaries — 2026-10-14

**Connected Blender: 5.1.2** (`bpy.app.version_string`). **Frame before: 971, `is_dirty` False. Frame after every call: 971, `is_dirty` False.** Temporary changes (frame, `frame_start`/`frame_end`, `render.filepath`, `resolution_percentage`, `eevee.taa_render_samples`, `image_settings.file_format`, plus two render handlers) were restored in `finally` blocks and read back: range 1–1630, filepath `S:\works\Blender creations\Stomach all parts\`, 100%, 40 samples, PNG, 0 handlers. Nothing saved. No image/video opened.

Session note: the blender.exe process is now PID 13168, started 15:53 on 2026-10-14, and it owns port 9876. Parts 1 used PID 5256, so Blender was restarted between sessions (this explains `is_dirty` False and the changed memory counters). Source: `execute_blender_code`, PowerShell, `Get-Counter` unless noted.

## TL;DR
- Render time is dominated by a fixed start-up cost, not by resolution or samples: frame 361 took 56.6 / 67.0 s at 10%/1 sample and 56.6 / 85.1 s at 25%/16 samples; in an 8-frame animation at 25%/16 the first frame took 76.05 s and frames 2–8 took 1.03–1.50 s each.
- `frame_set` costs 0.12–0.19 s; `view_layer.update()` after it measured 0.000 s.
- blender.exe dedicated GPU memory sampled 416–1,623 MiB (steady ~583 MiB, one-off spikes to ~1.6 GiB during first-frame set-up); the only adapter with dedicated usage reached 1,749 MiB.
- Stomach mesh data shows many sharply folded vertices (3,780 neighbouring-normal angles above 90°, 9,714 vertices above 5x median Laplacian displacement; worst 1.92 units); the Antrum is much smoother (24 edges above 90°). No multires, custom normals or sculpt data on either.
- PART_11_Colon has vertices inside Cam_Endoscope's frustum at frames 531 (57%) and 731 (0.7%), none at 361 and 971; whether it is occluded by the stomach wall was not tested.

## Task 1 — Per-render overhead (numbers only)
(a) `frame_set(f)` then `view_layer.update()`, seconds (perf_counter), two readings where measured twice:

| f | `frame_set` | `update()` |
|---|---|---|
| 361 | 0.153, 0.192 | 0.000 |
| 531 | 0.134 | 0.000 |
| 731 | 0.123 | 0.000 |
| 971 | 0.188, 0.177 | 0.000 |

(b) Frame 361, `bpy.ops.render.render(write_still=True)`, back-to-back, EEVEE:

| Resolution | Samples | Run 1 (s) | Run 2 (s) |
|---|---|---|---|
| 10% (192 x 108) | 1 | 56.63 | 66.99 |
| 25% (480 x 270) | 16 | 56.62 | 85.05 |

(c) One animation, frames 361–368, 25%, 16 samples, `renders/audit/anim_test/f_*.png` (git-ignored via `/renders/audit/`): total **84.91 s**.

| Frame | 361 | 362 | 363 | 364 | 365 | 366 | 367 | 368 |
|---|---|---|---|---|---|---|---|---|
| Time (s, `render_pre`→`render_post`) | 76.05 | 1.50 | 1.05 | 1.03 | 1.04 | 1.03 | 1.16 | 1.13 |

Gaps between frames: 0.02 s (361→362), 0.00 s for the rest; time before the first `render_pre`: 0.01 s. Frames 2–8 are faster than frame 1: yes, by ~50–75x. Frame range, output path, file format and all settings were restored (above).

Interpretation (hypothesis)
- Most of a single-frame render here is a fixed set-up cost (scene sync, shader/GI set-up) that does not scale with resolution or samples, and it is paid once per `render` call, not per frame of an animation. Confidence: high that the cost is fixed in these tests; the cause is unmeasured.
- Resolution/samples barely matter in this range; the run-to-run spread (56.6–85.1 s) at the same settings is as large as the difference between settings. I did not test 100%/40 samples.

## Task 2 — Work per frame (facts)
EEVEE (`scene.eevee`): `use_shadows` True, `shadow_ray_count` 1, `shadow_step_count` 6, `shadow_resolution_scale` 1, `shadow_pool_size` 512, `light_threshold` 0.01. `use_raytracing` **False** (method SCREEN, resolution scale 2, max roughness 0.5, denoise on, all inactive). `use_fast_gi` True, method GLOBAL_ILLUMINATION, 2 rays, 8 steps, resolution 2, `gi_diffuse_bounces` 3, `gi_cubemap_resolution` 512, `gi_visibility_resolution` 32, `gi_irradiance_pool_size` 16. Volumetrics: `volumetric_samples` 64, tile size 8, volumetric shadows off; **0 materials with volume nodes** (world has none), so volumetrics add no per-frame work. `taa_render_samples` 40, `use_taa_reprojection` True.

Counts
- Lights: 5, all with shadows on and all render-enabled (Light_Endoscope_Tip POINT, Light and Light.001 POINT, Light_Fill_1 and Light_Fill_2 AREA).
- Total faces of render-enabled meshes (base data): **1,071,570** (of which PART_11_Colon 598,650). Evaluated faces of render-enabled meshes that are not hidden in the view layer: **514,281** (colon and Cylinder excluded because they are not evaluated).
- Materials in use: 18 with users. All use render method DITHERED. Materials with Subsurface Weight > 0 or linked: 13 (MAT_W3_Fundus_Mucosa, MAT_W1_GEJ_ZLine, MAT_Esophagus_Tube, MAT_DuodenalBulb_Mucosa, MAT_GEJ_WhiteMucosa, MAT_W5_Antrum_Mucosa, MAT_W6_Pylorus_Ring, Stomach_Exterior, Stomach_Exterior_Cardia, tripo_mat_9635a98a.001, BACKUP_MAT_W3_Fundus_before_white, …); materials with transmission or refraction: **0**; materials with true displacement (method other than BUMP, or a Displacement node): **0**.
- Shader node count per material: MAT_W1_GEJ_ZLine 107; MAT_W3_Fundus_Mucosa 56; BACKUP_MAT_W3_Fundus_before_white 51; MAT_Scope_Tube 27; MAT_Esophagus_Tube 24; MAT_DuodenalBulb_Mucosa 22; MAT_Antrum_Mucosa 17; MAT_Pylorus_Mucosa 17; Stomach_Exterior 17; Stomach_Exterior_Cardia 17; tripo_mat_9635a98a.001 16; MAT_W5_Antrum_Mucosa 12; MAT_W6_Pylorus_Ring 12; tripo_mat_c4496501 7; MAT_GEJ_WhiteMucosa 6; Dots Stroke 5; material_0 3; Stomach_Exterior.001 2.

Interpretation: nothing in these settings scales with resolution except TAA samples, shadows (5 lights) and Fast GI; the two heaviest node trees (W1 107, W3 56) are the ones visible in two of the four shots. Confidence: low on any cost attribution (not profiled).

## Task 3 — GPU memory (Windows counters)
Counters used: `\GPU Process Memory(*)\Dedicated Usage` (instance for `pid_13168`) and `\GPU Adapter Memory(*)\Dedicated Usage`. Sampled by a background PowerShell loop during all renders of Task 1 (104 samples, 16:21:37–16:27:56, ~3.6 s apart because each query takes time; short spikes can be missed). The MX450 was not identified by name: of three adapter LUIDs only `…11d57` reported non-zero dedicated memory, so I treat it as the MX450 (**assumption**; the Iris Xe LUIDs read 0). Counters were available (no "could not check").
- Before (idle, 16:21:37): blender.exe 520 MiB; adapter 702 MiB.
- During renders: blender.exe min 416, steady 559–585, maximum **1,623 MiB** (16:24:38; another 1,589 MiB at 16:22:34 and 1,571 MiB at 16:27:38); adapter min 584, maximum **1,749 MiB** (16:27:38), otherwise ~720–790 MiB.
- After (16:27:56): blender.exe 559 MiB; adapter 726 MiB.
- `Total Committed` per adapter (single reading before): …11a44 511 MiB, …11cce 0, …11d57 1,243 MiB.
- VRAM size: 2 GiB (`AdapterRAM` of MX450, part 2).
Interpretation (hypothesis): the high readings coincide with render start-up (first frame of each render call), consistent with Task 1; the adapter peak of 1,749 MiB is within ~0.25 GiB of the 2 GiB card. Confidence: medium (coarse sampling, adapter attribution assumed).

## Task 4 — Spikes (frame 731 hypothesis; numbers only; evaluated meshes at frame 971; positions in world space)
Method: Laplacian distance = |vertex − mean of edge-connected neighbours| in world units; edge angle = angle between the vertex normals of an edge's two ends.

| | Stomach | PART_W5_Antrum |
|---|---|---|
| Vertices / edges | 274,877 / 567,981 | 18,633 / 37,649 |
| Laplacian p50 / p90 / p99 / p99.9 | 0.00784 / 0.02803 / 0.05198 / 0.11937 | 0.00099 / 0.00708 / 0.02170 / 0.03867 |
| Count above 5x median | **9,714** | 2,774 |
| Largest Laplacian (x median) | 1.92 (245x) | 0.093 (94x) |
| Edge normal angle p50 / p90 / p99 / p99.9 (deg) | 9.09 / 45.54 / 83.49 / 146.85 | 2.54 / 14.94 / 58.24 / 85.22 |
| Max angle / edges > 60° / edges > 90° | 179.5° / 30,942 / **3,780** | 130.7° / 331 / 24 |

20 largest outliers (vertex index: Laplacian distance, x median, world position):
- Stomach: 540: 1.921, 245x, (16.392, 4.782, 42.120); 539: 1.648, 210x, (13.768, 7.966, 40.543); 561: 1.616, 206x, (8.568, 1.391, 37.584); 434: 1.577, 201x, (10.383, 2.007, 38.890); 580: 1.520, 194x, (10.286, -4.353, 29.329); 530: 1.497, 191x, (17.518, -4.943, 27.594); 565: 1.469, 187x, (12.319, -4.902, 30.419); 806: 1.431, 183x, (9.648, 6.363, 43.761); 424: 1.414, 180x, (15.998, -5.254, 30.226); 421: 1.385, 177x, (15.029, 5.610, 42.718); 436: 1.381, 176x, (12.208, -2.803, 28.697); 411: 1.328, 169x, (17.560, -4.972, 24.934); 589: 1.292, 165x, (8.991, -3.529, 25.302); 745: 1.242, 158x, (15.978, -3.353, 27.319); 667: 1.196, 153x, (14.984, 10.099, 42.506); 460: 1.182, 151x, (10.035, -3.917, 22.984); 560: 1.178, 150x, (9.291, 3.921, 40.866); 808: 1.140, 146x, (15.778, 8.547, 41.681); 534: 1.075, 137x, (16.471, -3.487, 25.087); 430: 1.027, 131x, (13.538, -4.975, 31.054).
- PART_W5_Antrum: 6789: 0.0929, 94x, (15.017, -6.555, 27.491); 10512: 0.0901, 91x, (14.878, -6.685, 27.483); 7654: 0.0888, 90x, (14.931, -6.522, 27.578); 10513: 0.0859, 87x, (14.868, -6.680, 27.511); 10468: 0.0852, 86x, (14.821, -6.659, 27.561); 7656: 0.0721, 73x, (14.975, -6.540, 27.542); 10418: 0.0710, 72x, (14.958, -6.705, 27.396); 6791: 0.0602, 61x, (15.039, -6.562, 27.455); 10508: 0.0575, 58x, (14.923, -6.700, 27.427); 8344: 0.0563, 57x, (14.840, -6.543, 27.653); 6802: 0.0497, 50x, (15.060, -6.622, 27.366); 10470: 0.0491, 50x, (14.805, -6.656, 27.586); 9026: 0.0470, 48x, (14.824, -6.556, 27.662); 7655: 0.0442, 45x, (14.952, -6.529, 27.558); 7653: 0.0425, 43x, (14.913, -6.517, 27.598); 30: 0.0411, 42x, (12.747, -6.463, 27.365); 16576: 0.0402, 41x, (13.673, -6.976, 26.954); 442: 0.0397, 40x, (12.696, -6.558, 27.323); 6787: 0.0391, 40x, (14.990, -6.535, 27.502); 18605: 0.0384, 39x, (13.363, -7.602, 28.221).

Other facts
- Multires: none on either. Custom split normals: `has_custom_normals` False on both. Sculpt data: no sculpt-mask/face-set attributes on either. Attributes: Stomach has `sharp_face` (flat faces 293,098 − 283,085 smooth = 10,013), Antrum has `sharp_face` with all 19,017 faces smooth. No `sharp_edge` attribute on either.
- Modifiers: Stomach — Subsurf_Rugae (view 0 / render 1), Displace_Rugae and Displace_Micro (both strength 0); Antrum — none (shape key Pylorus_Open 0.55 at 971).
- Displacement method: MAT_W3_Fundus_Mucosa BUMP (Stomach); MAT_Antrum_Mucosa BUMP, MAT_W6_Pylorus_Ring BUMP (Antrum).
- Object scale: Stomach 1,1,1; Antrum 2.368 each axis (Laplacian values for the Antrum are therefore in world units after scaling).

Interpretation (hypothesis)
- The Stomach's neighbouring-normal angles (3,780 edges above 90°; 99.9th percentile 147°) and 9,714 vertices displaced far from their neighbours' mean indicate real sharp folds or spikes in the base mesh, independent of displace modifiers. A Laplacian of this kind is also large at legitimate fold crests and mesh boundaries (665 boundary edges), so it does not by itself prove visible thorns. Confidence: medium that the mesh contains sharp-vertex outliers; low that they are the frame-731 artifacts (I did not map them to the camera's view).
- Antrum outliers are a tight cluster near (14.9, −6.6, 27.5), around 10 vertices with 50–94x, and the mesh is otherwise smooth. Confidence: low as to visual effect.

## Task 5 — Hidden but render-enabled objects
Flags: PART_11_Colon and Cylinder — `hide_viewport` False, `hide_get()` **True**, `hide_render` False, no parent.

World-space bounding boxes (object matrix applied to the base-mesh box):
- PART_11_Colon: min (11.72, −13.31, 1.01), max (31.30, 8.41, 33.07); no modifiers.
- Cylinder: min (18.43, −37.65, 14.17), max (23.06, 29.54, 27.58) for the **undeformed** base mesh. Its modifier stack in order: Subdivision (SUBSURF, viewport level 1, render level 2) → Curve (CURVE, object BézierCurve, deform axis POS_X). The curve object is itself view-layer hidden and render-enabled; its two control points span x 20.83–21.37, y −36.84–29.41, z 20.41–21.78. The evaluated, curve-deformed extent was not measured (the object is not evaluated while hidden): could not check.

Cam_Endoscope projection of the 8 box corners (normalized x, y in frame = 0–1; depth positive in front; "corners in frame" = corners with 0≤x,y≤1 and depth>0):

| Object | Frame | x range | y range | depth range | Corners in frame | Centre distance |
|---|---|---|---|---|---|---|
| PART_11_Colon | 361 | −0.54–2.17 | −8.15–2.03 | −8.97–22.91 | 0 | 26.61 |
| | 531 | 0.21–51.54 | −2.00–34.60 | −1.18–37.00 | 2 | 19.56 |
| | 731 | −1.00–1.45 | −1.80–3.28 | −25.90–11.05 | 1 | 11.76 |
| | 971 | −1.74–1.01 | −2.22–2.47 | −24.57–6.74 | 1 | 14.15 |
| Cylinder (undeformed) | 361 | 0.37–0.69 | 0.18–1.81 | −28.58–36.47 | 4 | 23.06 |
| | 531 | −1.29–1.14 | −10.11–7.44 | −3.13–33.77 | 0 | 16.69 |
| | 731 | 0.26–0.59 | 0.79–1.66 | −33.33–25.88 | 0 | 8.45 |
| | 971 | 0.53–0.90 | 0.28–0.83 | −38.85–26.86 | 4 | 10.60 |
All eight bounding boxes overlap the frustum or straddle the camera plane (several have negative depth, meaning the box surrounds the camera), so the bounding-box test is not informative on its own.

Exact test for the colon (base mesh has no modifiers): fraction of its 299,707 vertices that project inside the frame with depth between clip start and end:

| Frame | Vertices in frustum | Share of colon | Min depth | Median depth |
|---|---|---|---|---|
| 361 | 0 | 0 | — | — |
| 531 | 171,929 | 0.5737 | 10.591 | 21.958 |
| 731 | 2,096 | 0.0070 | 5.945 | 7.847 |
| 971 | 0 | 0 | — | — |
Occlusion was not tested; at frame 531 the Stomach wall is hit by every ray at 5.85–14.16 units (part 4), and the colon's nearest in-frustum vertex is at depth 10.59.

Interpretation (hypothesis): at 531 and 731 the colon lies in the frustum but is probably behind the closed stomach wall; if the wall has open boundaries (665 on the Stomach) parts could show. Cylinder: not resolved. Confidence: low.

## Task 6 — Boundary-vertex minimum distances at 361 / 531 / 731 / 971 (evaluated meshes; 7 neighbouring parts; smallest pairs)
| Pair | 361 | 531 | 731 | 971 |
|---|---|---|---|---|
| PART_W1_GEJ_ZLine – PART_W3_Fundus | 0.0001 | 0.0002 | 0.0000 | 0.0001 |
| PART_W5_Antrum – Stomach | 0.0175 | 0.0175 | 0.0175 | 0.0175 |
| Esophagus Tube – PART_W1_GEJ_ZLine | 0.1984 | 0.1984 | 0.1984 | 0.1984 |
| PART_9_Duodenal bulb – Stomach | 0.2063 | 0.2063 | 0.2063 | 0.2063 |
| Breathing tube – Esophagus Tube | 0.3979 | 0.3979 | 0.3979 | 0.3979 |
| PART_9_Duodenal bulb – PART_W5_Antrum | 0.4105 | 0.4105 | 0.4105 | 0.4105 |
| Esophagus Tube – Stomach | 0.5188 | 0.5188 | 0.5188 | 0.5188 |
| PART_W3_Fundus – Stomach | 1.1028 | 0.4985 | 0.6685 | 0.9773 |
| PART_W1_GEJ_ZLine – Stomach | 0.7364 | 0.4989 | 0.6690 | 0.7364 |
Only the pairs involving PART_W1_GEJ_ZLine (shape keys Open/Squeeze/Breath/Pulse animated) and PART_W3_Fundus (GN_Cardia_Rugae animated) change; the W1–Stomach and W3–Stomach gaps vary 0.50–1.10 across the four frames. The pairs with Antrum, Duodenal, Esophagus and Breathing tube are constant. Pylorus_Open animates on the Antrum but did not change the Antrum–Stomach or Duodenal–Antrum minima.

Scale: `scene.unit_settings`: METRIC, scale_length 1.0, length_unit METERS. Cam_Endoscope FOV 90.000° (horizontal, = `angle`), vertical 67.38°.

## Conflicts / notes
- Part 1 recorded the MCP server as PID 5256; the session is now PID 13168 (restart). Memory counters from part 2 (PeakWorkingSet64 3.76 GiB) belong to the earlier process; the new process shows PeakWorkingSet 4,096 MiB at this point (peak since start; not specific to any single render).
- The task asked for `Get-Counter` "dedicated GPU memory" of blender.exe; values above are from the counter instances for PID 13168.

## Could not check
- Which adapter LUID is the MX450 (assumed from usage), and sub-4 s GPU spikes.
- Curve-deformed extent of the Cylinder; occlusion of the colon by the stomach wall; whether any listed Stomach outlier is visible in the frame-731 view.
- Render times at 100% / 40 samples (not run); the cause of the fixed start-up cost.
