# Phase 0 part 3 — texture paths, VRAM, visual hypotheses (data only) — 2026-10-14

**Connected session:** Blender **5.1.2** (`bpy.app.version_string`), `frame_current` **971**, `is_dirty` **False** (it read True after my part-2 timing runs; I did not save, so something else cleared it, for example a save or reload on your side — could not check). Blender 5.2.2 was not used. Read-only: no frame, setting or path was changed; no image/video was opened. Source: `execute_blender_code` read-only queries unless stated.

## TL;DR
- "11 missing" no longer holds as a statement about *usable* textures: all 11 paths still fail `os.path.exists`, but 8 of the 11 are packed in the .blend (which explains textures in your viewport); only 3 are genuinely unresolved (Colon_image.png, Stomach_Baked, Stomach_HDRP), and the `E:` substitute does not exist for them either.
- Texture memory is small (~50 MiB at 8-bit, or ~25 MiB if the unused W1 set is not resident); it cannot explain 1.8/2.0 GiB VRAM by itself.
- The Endoscope Tip light is keyed on every frame between 3 and 500 W: 76.8 W at 361, 500 W at 531, 163.9 W at 731, 26.1 W at 971. Material colour ramps and SSS/coat/specular values also differ per part (V1 confirmed in data).
- The four other lights are hidden in the viewport (`hide_viewport`) but render-enabled (`hide_render` False): your Rendered viewport and the final render may light the scene differently (hypothesis: viewport honours `hide_viewport`).
- Stomach displace modifiers have strength 0 and all materials use BUMP displacement, so the "thorn-like spikes" are not produced by those modifiers (V5 not supported on that point).

## Hypotheses under test (from the brief, treated as hypotheses)
V1 inconsistent look between parts (terracotta 361, dark brown 531, pale pink 731, saturated red 971). V2 lighting looks like one strong light near the camera. V3 near-rectilinear lens, no distortion/vignette. V4 colour management/exposure. V5 serrated silhouette near frame 361 and thorn-like spikes at 731. V6 dense fur-like micro-bump on the antrum at 971. V7 small hard highlight streaks, not a broad wet sheen.

## Task 1 — Paths (facts)
Counts of datablocks with paths: images 11 file-based (+1 Render Result viewer), libraries 0, movie clips 0, sounds 0, cache files 0, volumes 0, fonts 0. Sequencer: `scene.sequence_editor` exists; strips not enumerated (could not check). "E-cand" = path with `S:` replaced by `E:`.

| Datablock | Raw path | Relative (`//`) | abspath exists | has_data | packed | users | E-cand exists |
|---|---|---|---|---|---|---|---|
| Colon_image.png (sRGB) | `S:\works\VR-Colon\Assets\Unity projects\VR-Colon\Assets\Imported\Colon_image.png` | no | False | False (0x0) | False | 1 | False |
| Stomach_Baked | `//Textures\Stomach_BakedNormal.png` → `E:\...\Stomach all parts\Textures\...` | yes | False | False (0x0) | False | 1 | n/a (already E:) |
| Stomach_HDRP | `//Textures\Stomach_GlossyHDRP.png` → `E:\...\Textures\...` | yes | False | False (0x0) | False | 1 | n/a |
| W1 BaseColor 2048² (sRGB) | `S:\works\Blender creations\Stomach all parts\W1_GEJ_ZLine\tripo_convert_9635a98a-....fbm\...BaseColor.jpg` | no | False | False | **True** | 1 | False |
| W1 Metallic 1024² / Roughness 1024² / Normal_Bake 512² (Non-Color) | same folder | no | False | False | **True** | 1 each | False |
| W0 BaseColor 2048² (sRGB) | `S:\works\Blender creations\Stomach all parts\W0_Hypopharynx\tripo_convert_c4496501-....fbm\...BaseColor.jpg` | no | False | False | **True** | 1 | False |
| W0 Metallic 1024² / Roughness 1024² / Normal_Bake 512² (Non-Color) | same folder | no | False | False | **True** | 1 each | False |
| Render output `scene.render.filepath` | `S:\works\Blender creations\Stomach all parts\` | no | False | n/a | n/a | n/a | **True** (`E:\works\Blender creations\Stomach all parts\`) |

Further facts
- `has_data` is False for all 8 packed tripo images in this reading (part 1 read True for the W0 four). `has_data` means pixels are currently loaded in memory, not that the file is available; packed data loads on demand. I cannot say why it differs between readings (hypothesis: image buffers are freed and reloaded as they are used).
- The tripo `.fbm` folders do not exist under `E:` either, so the packed copies are the only source of those pixels.
- Material usage: the 4 W0 images feed `tripo_mat_c4496501` (object PART_W0_Hypopharynx). The 4 "W1" images feed `tripo_mat_9635a98a.001`, which no object's material slots use (PART_W1_GEJ_ZLine uses procedural `MAT_W1_GEJ_ZLine`). `Colon_image.png` feeds `material_0` (PART_11_Colon). `Stomach_Baked` and `Stomach_HDRP` are used by no material.
- MCP `get_blendfile_summary_missing_files` (part 2): exactly those 3 unpacked images.

Interpretation
- The "11 missing" result holds only as "11 paths do not resolve on disk". The usable-texture picture is: 8 packed (W0 textured, W1 set unused), 1 missing texture on a hidden colon, 2 missing and unused.
- Hypothesis: textures visible in your viewport come from W0's packed images. Confidence: high.

## Task 2 — Texture memory estimate and heavy meshes
Assumption: decoded 8-bit RGBA uncompressed, `width x height x 4` bytes, no mipmaps (mipmaps add ~33%); all 11 are `is_float` False, so no x16 case applies. Images with size 0x0 count as 0.

| # | Image | Pixels | MiB | Used by material |
|---|---|---|---|---|
| 1 | W1 BaseColor | 2048x2048 | 16 | tripo_mat_9635a98a.001 (no object) |
| 2 | W0 BaseColor | 2048x2048 | 16 | tripo_mat_c4496501 |
| 3 | W1 Metallic | 1024x1024 | 4 | tripo_mat_9635a98a.001 |
| 4 | W1 Roughness | 1024x1024 | 4 | tripo_mat_9635a98a.001 |
| 5 | W0 Metallic | 1024x1024 | 4 | tripo_mat_c4496501 |
| 6 | W0 Roughness | 1024x1024 | 4 | tripo_mat_c4496501 |
| 7 | W1 Normal_Bake | 512x512 | 1 | tripo_mat_9635a98a.001 |
| 8 | W0 Normal_Bake | 512x512 | 1 | tripo_mat_c4496501 |
| 9–10 | Colon_image.png, Stomach_Baked | 0x0 | 0 | material_0 / none |

- Total, all 11: **50 MiB** (~67 MiB with mipmaps). Only the W0 set, which is on a material an object uses: 26 MiB.
- Meshes over 100k faces (base mesh, before modifiers): Stomach 274,877 v / 293,098 f, Subsurf_Rugae **viewport level 0, render level 1**; PART_11_Colon 299,707 v / 598,650 f, no modifiers, hidden in the view layer (`hide_get()` True). No other mesh exceeds 100k (PART_W4_Rugae_Panel 86,400 f, render-disabled). Only subsurf objects: Stomach (above) and Cylinder (viewport 1 / render 2, 1,056 f).
- Hypothesis: with textures at ~26–50 MiB, the 1.8 GiB VRAM figure is dominated by geometry (Stomach, plus the colon if drawn), EEVEE shadow/GI pools (`shadow_pool_size` 512, `gi_irradiance_pool_size` 16, `gi_cubemap_resolution` 512) and the viewport itself. Confidence: low; I did not measure VRAM per category (could not check).
- Hypothesis: at final render, Stomach's render subsurf level 1 multiplies its face count roughly x4 for quad faces (~1.2 M), not seen in the viewport (level 0). Confidence: low (face types not checked).

## Task 3 — Scene-data checks
Common facts: frame 971 live. Units METRIC, scale 1, meters. Sources: node-tree queries above.

### V1 Inconsistent look between parts — **CONFIRMED (data differs); frame→part mapping COULD NOT CHECK**
Per-object material and parameters (Principled values; "L" = driven by nodes):

| Object | Material | Base colour (ramp ends) | SSS wt / radius / scale | Roughness | Spec IOR lvl | IOR | Coat wt / rough | Sheen | Emission |
|---|---|---|---|---|---|---|---|---|---|
| PART_W0_Hypopharynx | tripo_mat_c4496501 | BaseColor image 2048² (sRGB) | 0 | Roughness image (Non-Color) | 0.5 | 1.5 | 0 / 0.03 | 0 | 0 |
| PART_W1_GEJ_ZLine | MAT_W1_GEJ_ZLine | eso ramp (0.88,0.62,0.58)→(1,0.31,0.28); gastric ramp (0.46,0.07,0.04)→(0.8,0.2,0.1) | 0.18 / (0.95,0.3,0.18) / 0.12 | L (ramps 0.1–0.26 eso, 0.2–0.36 gastric) | L (SPEC_LIP) | 1.4 | L / L | 0 | 0 |
| PART_W3_Fundus and Stomach | MAT_W3_Fundus_Mucosa | gastric ramp (0.46,0.14,0.11)→(0.8,0.36,0.28), times valley mix with (0.72,0.66,0.66) | 0.18 / (0.9,0.35,0.25) / 0.12 | L (ramp 0.26–0.42, minus 0.05 x attribute) | 0.9 | 1.4 | L (0.35 + 0.3 x attr) / L (0.24→0.10) | 0.06 | 0 |
| PART_W5_Antrum slot 0 | MAT_Antrum_Mucosa | ramps (0.2,0.05,0.06)→(0.86,0.45,0.4) and (1,0.51,0.45)→(1,0.31,0.33) | 0 / (1,0.2,0.1) / 0.05 | L (ramp 0.08–0.45) | 0.28 | 1.38 | 0.5 / 0.04 | 0.03 | 0 |
| PART_W5_Antrum slot 1 | MAT_W6_Pylorus_Ring | ramp (0.56,0.23,0.2)→(0.88,0.45,0.38) | 0.12 / (0.3,0.1,0.07) / 0.05 | L (Map Range, values not read) | 0.5 | 1.38 | 0.22 / 0.3 | 0 | 0 |
| PART_9_Duodenal bulb | MAT_DuodenalBulb_Mucosa | ramp (0.58,0.11,0.09)→(0.85,0.2,0.17) | 0.05 / (1,0.2,0.1) / 0.05 | L (ramp 0.06–0.3) | 0.3 | **1.0** | 0.55 / 0.05 | 0 | 0 |
| Esophagus Tube | MAT_Esophagus_Tube | ramp (0.88,0.62,0.58)→(1,0.31,0.28) | 0.18 / (1,0.2,0.1) / 0.12 | L | 0.9 | 1.4 | **1.0** / L (0.24→0.10, same map) | 0.05 | 0 |

- Parameters that differ between parts: base-colour ramps (every material), SSS weight (0 / 0.05 / 0.12 / 0.18), SSS radius, specular IOR level (0.28–0.9), IOR (1.0, 1.38, 1.4, 1.5), coat weight (0–1.0) and coat roughness (0.03–0.3), sheen (0–0.06), normal source (Bump chains with differing strength/distance; tangent normal map for W0). Identical across all: Metallic 0, Anisotropic 0, Alpha 1, transmission 0, emission 0 (except `material_0`), SSS method RANDOM_WALK, distribution MULTI_GGX, displacement method BUMP.
- Shared look inputs that vary per frame: **Light_Endoscope_Tip energy** (action `Endoscope_TipExposure_v15`, keyed every frame) is 76.8 W at frame 361, 500 W at 531, 163.9 W at 731, 26.1 W at 971 (range 3–500 W over 1–1630; 69.5 W at 1605). That is a 19x spread across your four frames.
- Interpretation (hypothesis): the stated colour differences are consistent with both the per-material colour ramps and the exposure keys; the data cannot say which dominates. Confidence: medium.
- Not checked: which object is in view at frames 361/531/731/971 (would need evaluating camera position vs. meshes; I did not change the frame).

### V2 Lighting looks like one strong light near the camera — **CONFIRMED for the viewport-visible lights; viewport/render discrepancy flagged**
| Light | Type | Power | Colour | Radius / size | Parent / position | Shadow | Visibility |
|---|---|---|---|---|---|---|---|
| Light_Endoscope_Tip | POINT | 26.11 W at f971 (3–500 W keyed) | (1, 0.94, 0.86), no temperature | radius 0.02 m | child of Cam_Endoscope, local (0,0,-0.15): 0.15 m ahead of camera | on, soft falloff on, filter 1.0, jitter off | hide_vp False, hide_get False, hide_render False |
| Light | POINT | 1000 W | white | radius 1.3924 m | world (-0.502, 0.153, -0.089); ~31 m from the camera at f971 | on | hide_vp **True**, hide_render False |
| Light.001 | POINT | 1000 W | white | radius 0 | (4.076, 1.005, 5.904); ~24.5 m | on | hide_vp **True**, hide_render False |
| Light_Fill_1 | AREA | 12 W | (1, 0.97, 0.95) | square 12 m | (29.383, -1.773, 51.109); ~30.3 m | on | hide_vp **True**, hide_render False |
| Light_Fill_2 | AREA | 12 W | (1, 0.97, 0.95) | square 12 m | (-2.475, -1.773, 39.109); ~21.2 m | on | hide_vp **True**, hide_render False |
- No SPOT lights (no spot size/blend). Specular/diffuse/volume factors 1.0 on all. Light linking: none (receiver and blocker collections empty on all five). Camera world position at frame 971: (13.082, -8.771, 26.488). Distances for the non-parented lights use their local = world locations (their `matrix_world` was not evaluated while hidden).
- Emissive objects: `material_0` on PART_11_Colon, Emission Strength 1.0, no linked emission colour (default white); PART_11_Colon is hidden in the view layer. No other emission.
- World: Background colour (0.05, 0.012, 0.008), strength 1.0. No world lighting nodes beyond that.
- Interpretation (hypothesis): in the Rendered viewport only the tip light is active (`hide_viewport` hides objects in the viewport in all shading modes — Blender behaviour I did not test here), which matches "one strong light near the camera". A final render also includes the four hidden lights (`hide_render` False), so look can differ between viewport and finals. Confidence: medium.

### V3 Lens — **CONFIRMED rectilinear; no distortion/vignette in scene data**
| Camera | Type | Lens / FOV | Sensor | Clip | DOF | Shift | Active |
|---|---|---|---|---|---|---|---|
| Cam_Endoscope | PERSP | 18 mm / 90.0° | 36 x 24, AUTO | 0.001–200 | off (focus 10, f/2.8 stored) | 0, 0 | yes (location/rotation animated) |
| Camera | PERSP | 50 mm / 39.6° | 36 x 24 | 0.1–100 | off | 0, 0 | no |
| Camera.001 | PERSP | 50 mm / 39.6° | 36 x 24 | 0.1–100 | off | 0, 0 | no |
- No lens-distortion or vignette node: `compositing_node_group` None; node groups present are 7 geometry-node groups (3 BACKUP_GN_*, GN_Esophagus_Folds, GN_Scope_Shaft, GN_W3_Cardia_Rugae). No vignette/bloom properties on `scene.eevee` in 5.1.2. A PERSP camera has no barrel distortion by construction.
- Interpretation: a real 140°-class endoscope image would carry fisheye-style distortion; this camera cannot. Fact only that none is configured.

### V4 Colour management and exposure — **settings are neutral; CONFIRMED no post chain**
AgX, look None, exposure 0, gamma 1, curves off, dither 1.0, film filter 1.5, `use_compositing` True but no compositor nodes (no glare/bloom); view-layer passes: combined and cryptomatte accurate only. Per-frame exposure variation comes only from the tip light keys (V1).

### V5 Geometry artifacts — **modifier cause NOT SUPPORTED; visual itself COULD NOT CHECK**
Modifier stacks in order:
- Stomach: Subsurf_Rugae (view 0 / render 1, quality 3) → Displace_Rugae (strength **0**, mid 0.5, direction NORMAL, texture Rugae_Displace_Tex CLOUDS scale 0.55 depth 4, object coords) → Displace_Micro (strength **0**, texture Micro_Surface_Tex CLOUDS scale 0.12 depth 2).
- PART_W3_Fundus: Relax_Mucosa (SMOOTH factor 0.4, 2 iterations) → GN_Cardia_Rugae (group GN_W3_Cardia_Rugae, Socket_1 0.4657, Socket_3 0.5; both animated).
- Esophagus Tube: GN_Esophagus_Folds (Socket_1 = 1). Cylinder: Subdivision (view 1/render 2) → Curve. PART_Scope_Shaft: GN_Shaft (0 base verts).
- No Shrinkwrap, Remesh, Decimate or Solidify modifier exists on any object (orphan actions `StomachAction.00x` reference a Decimate that is gone).
- All materials use displacement method BUMP, so no material changes the silhouette.

Geometry (base mesh; loose/non-manifold from bmesh):
| Object | Verts / faces | Smooth faces | Loose v / e | Non-manifold edges (boundary) |
|---|---|---|---|---|
| Stomach | 274,877 / 293,098 | 283,085 | 0 / 25 | 2,479 (665) |
| PART_W3_Fundus | 25,623 / 50,755 | all | 0 / 0 | 491 (491) |
| PART_W1_GEJ_ZLine | 11,840 / 11,680 | all | 0 / 0 | 320 (320) |
| PART_W5_Antrum | 18,633 / 19,017 | all | 0 / 0 | 275 (274) |
| PART_W0_Hypopharynx | 36,560 / 36,562 | all | 0 / 0 | 0 |
| PART_9_Duodenal bulb | 23,454 / 46,626 | all | 0 / 0 | 269 (269) |
| PART_W2_Cardia_Retroflexed (render off) | 31,400 / 31,400 | all | 0 / 0 | 0 |
| PART_W4_Rugae_Panel (render off) | 87,001 / 86,400 | **0** | 0 / 0 | 1,200 (1,200) |
| Esophagus Tube | 14,128 / 13,998 | all | 0 / 0 | 260 (260) |
| PART_11_Colon | 299,707 / 598,650 | all | 0 / 0 | 734 (734) |
- Shape keys at frame 971: W1 Breath -0.143 (a negative value), Pulse 0.003, CardiaOpen 0.206, Open 0, Squeeze 0; W5 Pylorus_Open 0.55, Pylorus_Close 0.
- Interpretation (hypothesis): the stitched parts are open meshes with exposed boundary edges (W1 320, W3 491, W5 274); an open rim seen edge-on against the dark world would show mesh-resolution stepping. Stomach spikes cannot come from its displace modifiers (strength 0); candidates are the mesh itself (25 loose edges, non-uniform density) or `GN_W3_Cardia_Rugae`. Confidence: low. Frame-to-object mapping and the actual look not checked.

### V6 Dense micro-bump on the antrum — **CONFIRMED that high-frequency bump exists; cause COULD NOT CHECK**
| Material | Bump nodes (strength / distance) | Height source | Noise scale / detail | Mapping scale | Texture coords |
|---|---|---|---|---|---|
| MAT_Antrum_Mucosa (slot 0) | Bump 0.65 / 0.04 → Bump.001 0.2 / 0.603 (chained; second drives Normal) | Noise.001 (scale 1.76, detail 10, distortion 0.48); Noise.003 (**scale 28, detail 8**, rough 0.5) | as stated | Mapping.001 (0.4, 4, 0.4); Mapping (1.5, 1, 1.5) | via Mapping nodes |
| MAT_W6_Pylorus_Ring (slot 1) | Bump 0.75 / 0.006 | Noise (**scale 190**, detail 3) | scale 190 | none | Object |
| MAT_W3_Fundus_Mucosa (W3 and Stomach) | BUMP 1.0 / 0.02 | H_TOTAL = 0.5 x coarse (mapping 2.2) + 0.5 x fine (mapping 13) | detail 2 | 2.2 and 13 | Object |
| MAT_W1_GEJ_ZLine | none (Normal unlinked) | n/a | n/a | MAP_VELVET 38, MAP_RAC 9.5 (colour/velvet only) | attribute-driven |
| MAT_DuodenalBulb_Mucosa | Bump 0 / 0.02; Bump.001 1.0 / 0.01 | Noise.003 (mapping 35) | detail 5 | 35 | via Mapping |
- Interpretation (hypothesis): the Pylorus-ring material (slot 1 of the antrum object) has the finest noise (190) and the Antrum material a second chained bump at scale 28 with detail 8; either could read as fur at close range. Which faces use slot 1 was not checked. Confidence: low–medium.

### V7 Highlights small hard streaks, not broad wet sheen — **PARTLY CONFIRMED in data**
- Roughness (base) ranges: Antrum 0.08–0.45; W3/Stomach 0.26–0.42 (minus up to 0.05); W1 0.1–0.36; Esophagus driven by a pool ramp (values not read); Duodenal 0.06–0.3; Pylorus ring via Map Range (values not read); W0 from texture.
- Coat roughness: 0.03 (W0 default off), 0.04 Antrum, 0.05 Duodenal, 0.24→0.10 for W3/Esophagus map, 0.3 Pylorus ring. Coat weight 0.35–1.0 on most mucosa materials, 0.22 on the pylorus ring. Coat IOR 1.33 on W3/Esophagus, 1.5 elsewhere.
- IOR 1.0–1.5 (Duodenal 1.0). Anisotropy 0 on every material I read (W1 not read for anisotropy). No sheen above 0.06.
- Roughness noise: every roughness is noise/ramp-driven (not constant).
- Lights: the only viewport-visible light is a 0.02 m radius point 0.15 m ahead of the camera.
- Interpretation (hypothesis): low coat roughness (0.04–0.1) plus a very small light source is the combination that produces small sharp highlights; broad sheen would need a larger source or higher roughness. Whether the final render's extra lights change that was not tested. Confidence: medium.

## Objects CLAUDE.md calls hidden (plus Cylinder and BézierCurve)
| Object | hide_viewport | hide_get() | hide_render |
|---|---|---|---|
| PART_11_Colon | False | **True** | False |
| Cylinder | False | **True** | False |
| BézierCurve | False | **True** | False |
| NurbsPath | False | **True** | False |
(From part 2, A5; same session, not re-read this time. Not render-hidden, so the colon and the cylinder would render if in view.)

## Could not check
- Which parts are in camera view at frames 361/531/731/971 (frame not changed).
- Roughness ranges of MAT_Esophagus_Tube, MAT_W6_Pylorus_Ring and the exact W3 `ROUGH_POOL`; W1 anisotropy; which faces use the antrum's second material slot.
- Whether `hide_viewport` lights are really absent from the Rendered viewport (expected Blender behaviour, not tested).
- Real VRAM breakdown, strips in the sequence editor, and who cleared `is_dirty`.
- Any visual outcome — no image was viewed.
