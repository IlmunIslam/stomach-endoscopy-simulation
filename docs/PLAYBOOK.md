# PLAYBOOK: rules learned the hard way (max 40 lines; promote from docs/LESSONS.md)
1. Never invent anatomy: any new visible feature must cite a reference image or a place Ilmun pointed at, otherwise ask.
   Evidence: invented vein object, 2026-10-17 (~01:20).
2. Never revert, open or save the working .blend; save own .npy backups before each edit and undo from them.
   Evidence: agent used File > Revert twice, 2026-10-15 (~16:56).
3. Find out how a feature is built before editing it: base mesh, modifiers, shape keys, materials.
   Evidence: rugae are base geometry, displace strength 0, so a modifier vertex group did nothing.
4. A gap or slit with no boundary edges can be a through-slot between ordinary faces: use cross-sections or rays and plot loops in local coordinates.
   Evidence: pylorus slot found only after many loop overlays.
5. Apply geometry edits to every shape key (Basis, Pylorus_Close, Pylorus_Open) or the animation breaks.
   Evidence: ring shrink and slot weld were applied per key.
6. After geometry or lighting changes re-check frames 361, 531, 731, 971 with tools/render_stats.py; viewport captures alone miss regressions.
   Evidence: only frames 700-900 were checked on the antrum tasks.
7. Large moves (about 1 unit or more) can blacken frames or add ripples: check move size before applying.
   Evidence: unclamped smoothing moved outliers up to 7 units and blacked out frame 732.
8. Ilmun's selected vertices are the best location signal: save their indices before editing.
   Evidence: tools/antrum_vein_idx.npy pinpointed the strand that photos could not.
9. Run the independent reviewer before presenting.
   Evidence: it was skipped on the vein/slot and seam tasks.
10. Write lessons to docs/LESSONS.md during the work, because context gets compacted.
    Evidence: the earlier session ran out of context mid-task.
11. Before any reassign, merge or delete, save a mesh.copy() and each face's material_index; .npy position backups cannot restore topology or slot assignments.
    Evidence: docs/LESSONS.md 2026-10-17 antrum seam/crack entries (merge removed 346 verts; 157-face reassign left red patches).
12. Measure before guessing a fix: ray-cast depth and face normal.view dots at the bad frames first; guessed fixes cost several rounds.
    Evidence: docs/LESSONS.md 2026-10-18 antrum crack round 2 (measured steps fixed it); 2026-10-17 strand glint guessed as coat.
13. If rim edges are non-manifold (3-4 faces) and rim vertices are sparse, stop patching (welds, fills, ngons); plan a local rebuild of the wall.
    Evidence: docs/LESSONS.md 2026-10-18 antrum crack round 2 (four patch methods failed on the red dart; commit b8734f7).
14. Camera paths: measure roll per frame (unwrapped, not slerp across ~180 deg) and check axis clearance with perpendicular rays before judging from images.
    Evidence: docs/LESSONS.md 2026-10-18 camera path (roll ~165 deg, radial offset 0.06-0.6 vs lumen 0.028; tools/fix_camera_pyloric_path.py, commit 0d1f09b).
