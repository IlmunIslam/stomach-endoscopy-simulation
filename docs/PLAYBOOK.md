# PLAYBOOK: rules learned the hard way (max 40 lines; promote from docs/LESSONS.md)
1. Never invent anatomy: any new visible feature must cite a reference image or a place Ilmun pointed at, otherwise ask.
   Evidence: invented vein object, 2026-10-17 (~01:20).
2. Never revert, open or save the working .blend; save own .npy backups before each edit and undo from them.
   Evidence: agent used File > Revert twice, 2026-10-15 (~16:56).
3. Find out how a feature is built before editing it: base mesh, modifiers (GN time gates vs camera distance), shape keys, materials; thin render lines may be curve overlays or selection outline, so check the object first.
   Evidence: rugae are base geometry, displace strength 0, so a modifier vertex group did nothing (docs/LESSONS.md 2026-10-18 shards+shaft); 2026-10-20 antrum cracks round 2 render lines were overlays, and 2026-10-20 antrum pylorus arm lines were misread as antrum geometry.
4. A gap with no boundary edges can be a through-slot between ordinary faces: use cross-sections or rays. In a double-sheet skirt every edge has 2 faces, so filter boundary edges to the front sheet (one linked face, normal·axis>0.2) first.
   Evidence: pylorus slot found only after many loop overlays; 2026-10-20 antrum cracks round 2 (open-edge search found nothing; tools/fill_antrum_cracks.py, commit 19bd9a2, closed the V hole).
5. Apply geometry edits to every shape key (Basis, Pylorus_Close, Pylorus_Open) or the animation breaks.
   Evidence: ring shrink and slot weld were applied per key.
6. After geometry or lighting changes re-check frames 361, 531, 731, 971 with tools/render_stats.py; viewport captures alone miss regressions.
   Evidence: only frames 700-900 were checked on the antrum tasks.
7. Large moves (about 1 unit or more) can blacken frames or add ripples: check move size before applying.
   Evidence: unclamped smoothing moved outliers up to 7 units and blacked out frame 732.
8. Ilmun's selected vertices are the best location signal: save their indices before editing.
   Evidence: tools/antrum_vein_idx.npy pinpointed the strand that photos could not.
9. Run the independent reviewer before presenting (it was skipped on the vein/slot and seam tasks).
10. After any gap (Blender reload, context compaction, mode change) check bpy.data.filepath, is_dirty and key values (camera, locations, bakes) before continuing; write lessons to docs/LESSONS.md during the work. Before bmesh calls, check the object mode (a user-left Object mode makes edit-mode bmesh fail; use bmesh.new() + from_mesh).
    Evidence: silent reload reverted camera, bulb and energy bake (docs/LESSONS.md 2026-10-22); earlier session ran out of context mid-task; 2026-10-22 wedge fill, bmesh failed with 'mesh must be in editmode'.
11. Before any reassign, merge, cover or delete, save a mesh.copy(), each face's material_index and (n_vertices, n_faces); assert the counts before deleting. .npy position backups cannot restore topology or slot assignments.
    Evidence: docs/LESSONS.md 2026-10-17 antrum seam/crack entries (merge removed 346 verts; 157-face reassign left red patches); 2026-10-22 wedge fill eighth pass (cover bookkeeping).
12. Measure before guessing a fix: read Ilmun's selection and plot one slice (radius vs axial at one angle), plus ray depth and normal.view dots at the bad frames, before choosing a method; guessed fixes cost several rounds.
    Evidence: docs/LESSONS.md 2026-10-18 antrum crack round 2 (measured steps fixed it); 2026-10-17 strand glint guessed as coat; 2026-10-22 junction strip (spike, crumple and junk methods failed before the slice).
13. If rim edges are non-manifold (3-4 faces) and rim vertices are sparse, stop patching (welds, fills, ngons) and peeling or sinking faces; plan a local rebuild or a covering sheet from ray hits, and report its residual seam.
    Evidence: docs/LESSONS.md 2026-10-18 antrum crack round 2 (commit b8734f7); 2026-10-22 wedge notch 7th pass (54-face delete and sinking exposed junk; covering sheet with BK_notch backup).
14. Camera paths: measure roll per frame (unwrapped, not slerp across ~180 deg) and check axis clearance with perpendicular rays before judging from images.
    Evidence: docs/LESSONS.md 2026-10-18 camera path (roll ~165 deg, radial offset 0.06-0.6 vs lumen 0.028; tools/fix_camera_pyloric_path.py, commit 0d1f09b).
15. After generating faces, compare each new face normal with the old faces' side (sign of normal dot radial) and flip every mismatch as a full set, then check the streaks.
    Evidence: docs/LESSONS.md 2026-10-19 pyloric canal rebuild (minority flip gave wedge streaks; tools/rebuild_pyloric_canal.py, commit 9f51469).
16. Before deleting a suspect patch, isolate it (ray-cast the pixel grid to face ids, then check connected components); in a double-layered column each deletion only exposes the next layer.
    Evidence: docs/LESSONS.md 2026-10-18 shards+shaft (16-face strip was the shard; 175- and 6-face deletions made it worse; commit a20a5e9).
17. When the target is vague ("the gap"), read the user's current selection, render his viewport clean (overlays off, under temp_override, restoring render.filepath and resolution), classify pixel-ray hits by object and distance (a far-layer hit is a see-through hole), and ask for a selected-vertex pointer after one failed fix, not a chain of metrics.
    Evidence: docs/LESSONS.md 2026-10-19 antrum gap (four fixes, no visible change); 2026-10-22 wedge gap (old selection and overlay render had reported success; far-layer hits found the wedge); 2026-10-22 fifth pass (camera moved between turns, old sheet missed the hole; re-read camera and refit each pass); sixth pass (camera closer again, old fit still covered; LESSONS 2026-10-22).
18. Merges and smoothing: dry-run the removed-vert count first, weld only coincident pairs, then smooth; never smooth before welding.
    Evidence: docs/LESSONS.md 2026-10-20 antrum pylorus notch (0.025 merge removed 422 verts) and 2026-10-17 seam/crack (1.2e-3 removed 346).
19. Zero ray hits do not prove a gap is closed: hairline slits and inside-wall seams pass rays, so confirm on the user-viewport render with a dark-pixel cluster count.
    Evidence: docs/LESSONS.md 2026-10-19 antrum gap (ray-casts showed no see-through) and 2026-10-20 antrum skirt inside view (0 open px, slit visible).
20. When a render shows a line or step that rays do not explain, isolate the drawing object by toggling visibility one object at a time in a clay/matcap view, restoring each after, before editing; do not assume ray agreement with the picture. Evidence: docs/LESSONS.md 2026-10-21 antrum ring re-skin (crease and pink step unchanged after cover smoothing and deletions).
21. After moving one mesh, re-check every overlap with neighbours (not only the joint) using pixel rays from the user view, then push over-skin verts down. Evidence: docs/LESSONS.md 2026-10-22 bulb flange (commit 37fd79f).
