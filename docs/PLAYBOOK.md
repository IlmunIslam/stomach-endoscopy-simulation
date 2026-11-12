# PLAYBOOK: ordered by violation count (docs/RULE_STATS.md). Numbers are fixed, cite them. Evidence: docs/PLAYBOOK_EVIDENCE.md
12. Measure before fixing: read Ilmun's selection, plot one slice, cast rays (depth, normal.view). Before a rebuild verdict list 2+ options incl. keep-and-fix. Map "up/opposite" to the camera view and gizmo, read docs/knowledge, then measure in the part's frame. Log his decisions.
3. Find how a feature is built (base mesh, modifiers, shape keys, materials, GN time gates) before editing. Ray-cast hit.object + material slot to name what draws an artefact; overlays/outlines are not geometry. BVH from every object the edit reaches. Use full object names.
6. After a geometry, light or shading change re-check the 4 canonical frames (tools/canonical_check.py), the target frame and frames where it shows through openings. Masks keyed to one axis or depth spill: check every area they reach.
9. Reviewer before presenting. Quote SAME/PASS/clearance only from a run, else label "Lead-reported". List residual defects as open.
14. Cameras: measure per-frame unwrapped roll and perpendicular-ray clearance (canonical_check.path_check) before judging images. Rebuild the BVH per frame when shape keys animate. Re-fit and re-check the path after moving a part.
1. No invented anatomy or motion: cite a reference image, a timed video frame or Ilmun's pointer, else ask.
7. Moves of 1+ unit can black frames; even 0.5-0.8 can bulge. Check move size, clamp per vertex, prefer harmonic smoothing to per-vertex remaps.
10. After any gap (reload, crash, compaction, mode change) check bpy.data.filepath, is_dirty and key values. Builders idempotent with a re-apply note. Test a new material and render it in separate calls. bmesh: check mode, write keys with me.vertices, assert mesh == Basis.
17. Vague target: read his selection, render his viewport clean (restore render props), classify ray hits by object and distance, re-read the camera each pass. After 1 failed fix ask for a selected-vertex pointer.
13. Non-manifold or sparse rim, or 3 failed patches: stop patching; local rebuild or a covering sheet from ray hits. A seam that survives tone/offset matching is a silhouette step: change geometry.
4. A gap without boundary edges may be a through-slot between ordinary faces: use cross-sections or rays; in double sheets filter to the front sheet first.
11. Before reassign/merge/cover/delete: mesh.copy(), per-face material_index, (n_verts, n_faces); assert counts. .npy backups cannot restore topology.
16. Delete by island id, never by size or coordinate threshold; dry-run per-island counts and assert. Each deletion exposes the next layer.
2. Never revert, open or save the working .blend; own .npy backups before each edit.
8. Save Ilmun's selected vertex indices before editing or changing mode.
18. Merge: dry-run the removed count, weld coincident pairs only, then smooth, never before.
20. A render line rays do not explain: toggle objects one at a time in a clay view, restore after.
21. Before moving a mesh list neighbours inside its channel; after, re-check every overlap with pixel rays and push over-skin verts down.
15. New faces: compare normal vs radial with old faces and flip every mismatch as a full set.
19. Zero ray hits do not prove a gap closed (hairline slits): confirm with a dark-pixel cluster count on his render.
5. Apply geometry edits to every shape key (Basis, Pylorus_Close, Pylorus_Open).
22. Every material, node or modifier setup is built by an idempotent script in tools/, never only in the live session.
