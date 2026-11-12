# Portable Blender rules

Rules distilled from a long-running Blender MCP project, with subject-specific wording removed.

**How the counts were made.** "Violations" = rows in the source lessons log whose severity is not `n/a`
(i.e. a failure, not a "what worked" note) and whose "rule that would have prevented it" column cites the matching
rule. 88 failure rows were scanned. Rules were counted by script, then adjusted by hand where one rule was split or
merged. Treat the numbers as a lower bound: a row that cites two rules counts once for each, and older free-text
entries without the structured format are not counted.

## A. Safety

1. **Never save, revert or reopen the user's working file; keep your own backups and undo from them.**
   WHY: a revert or lost save destroys unreviewed work, and only the user knows what they approved.
   Violations: 2

2. **Before any merge, delete, cover, reassign or rebuild, copy the data (mesh copy, per-face material index, vertex and face counts) and assert the counts afterwards. Position-only backups cannot restore topology or slot assignments.**
   WHY: topology edits are irreversible from coordinate backups alone.
   Violations: 4

3. **Save the user's current selection (indices) before editing or changing mode, and treat it as the best signal for where the problem is.**
   WHY: a mode switch loses the selection, and photos or metrics rarely locate a defect as precisely as the user's own pick.
   Violations: 2

4. **Dry-run every destructive selection: pick faces by island or ID, never by a size or coordinate threshold; print per-group counts and assert them before applying.**
   WHY: thresholds silently swallow neighbouring parts, and in layered geometry each deletion only exposes the next layer.
   Violations: 3

5. **Dry-run merges and welds (count what would be removed), weld only coincident pairs, then smooth. Never smooth before welding.**
   WHY: a loose merge tolerance collapsed hundreds of vertices, and smoothing unwelded boundaries opens new cracks.
   Violations: 2

6. **List any backup datablocks or temp files you leave behind, with their paths, in your report so the user can purge them before saving.**
   WHY: leftover fake-user backups end up inside the user's saved file.
   Violations: 1

## B. Process

7. **Do not invent content. Any new visible feature or animated key must cite a reference, a timed source frame, or a place the user pointed at; otherwise ask.**
   WHY: plausible-looking invention is the most common reviewer rejection and costs whole rounds.
   Violations: 6

8. **Measure first, then choose the fix: read the user's selection, plot a section or profile, cast rays for depth and normals, and measure the "before" value. Never use an estimated baseline.**
   WHY: fixes picked from guesses took several rounds, while measured ones worked first time.
   Violations: 14

9. **Before a rebuild-or-patch verdict, list at least two options (including keep-and-fix) and what the references allow.**
   WHY: a rebuild verdict given with no alternatives was rejected by the reviewer.
   Violations: 1 (included in the count for rule 8)

10. **Map the user's direction words ("up", "opposite", "left") to the actual view and gizmo, and read any documented reference, before rotating or moving anything. When a reference contradicts the user's words, ask. Record the user's decision so later rounds do not reverse it.**
    WHY: direction words are ambiguous, and an orientation applied on words alone had to be questioned afterwards.
    Violations: 2

11. **Find out how a feature is built before editing it: base mesh, modifiers, shape keys, materials, driver or time gates. A modifier or vertex group may do nothing if the effect is baked into the base geometry.**
    WHY: edits aimed at the wrong layer had no visible effect.
    Violations: 3

12. **Identify what actually draws an artefact before editing: ray-cast to `hit.object` and the material slot, or toggle visibility one object at a time in a clay view and restore it. Selection outlines and curve overlays are not geometry. Report full object names, never truncated suffixes.**
    WHY: features were repeatedly attributed to the wrong object, and similar names made the report ambiguous.
    Violations: 13 (rule 11 and this rule are cited together; the true split is unknown)

13. **Before moving one object, list every neighbour whose geometry sits inside or passes through it. After moving, re-check all overlaps, not only the joint, and count neighbour vertices inside the solid.**
    WHY: a move changes every overlap, and self-intersection tests on one object miss neighbours.
    Violations: 2

14. **Check move size before applying: large moves (about 1 unit or more) can blacken or ripple the result, and even sub-unit offsets can bulge or flap. Clamp per-vertex displacement and prefer harmonic or implicit smoothing to per-vertex remaps.**
    WHY: unclamped smoothing flew outliers 7 units, and per-vertex remaps made spikes.
    Violations: 6

15. **After two or three failed patches on one region, or when the rim edges are non-manifold and sparse, stop patching. Plan a local rebuild or a covering sheet. A seam that survives tone and offset matching is a silhouette step: change the geometry, not the colour.**
    WHY: repeated patching on topology that cannot be closed locally only peeled layers and cost many rounds.
    Violations: 5

16. **When the target is vague ("the gap"), read the user's selection and render their viewport clean (overlays off, restore any render path or resolution you changed). After one failed fix, ask for a selected-vertex pointer instead of chaining more metrics. Re-read the camera each pass.**
    WHY: fixes tuned to a proxy metric or a stale camera did not change what the user saw.
    Violations: 6

17. **After generating faces, compare each new face normal with its neighbours' side and flip every mismatch as a full set, then check for streaks.**
    WHY: flipping only a minority gave streaky shading.
    Violations: 1

## C. Verification

18. **Do not report a pass, "SAME", a clearance or any number you did not run or measure. Label it "lead-reported" or unverified, and list residual reviewer defects as open.**
    WHY: pass results were quoted before a run again and again, and later checks disagreed.
    Violations: 8

19. **Get an independent read-only review before presenting visual or geometry work, and fix real defects. Cap the number of rounds, and report honestly what is still wrong after the cap.**
    WHY: the reviewer repeatedly caught defects the author had missed.
    Violations: 8 (same rows as rule 18; the reviewer step was skipped or its verdict was pending)

20. **After a geometry or shading change, re-check a fixed set of regression views plus the view the change is for, plus any view where that geometry shows through openings. A viewport capture alone misses regressions.**
    WHY: checking only the target frames let regressions slip through elsewhere.
    Violations: 10

21. **Never key a shading mask to one axis or to depth alone. Check every area it reaches, in every view where it shows.**
    WHY: single-axis masks spilled onto unrelated areas.
    Violations: 3

22. **Zero detected defects do not prove a fix. A gap with no boundary edges can be a through-slot between ordinary faces. Rays miss hairline slits. Confirm on a clean render with a dark-pixel cluster count, or use cross-sections.**
    WHY: edge and ray searches reported "closed" while the user still saw the gap.
    Violations: 5

23. **For anything that moves or animates (cameras, rigs, shape-keyed parts), measure per-frame values (unwrapped roll, clearance from perpendicular rays) and rebuild spatial structures such as a BVH per frame when shapes animate. Check each animated state on the frames where it is visible.**
    WHY: a static BVH gave a false clearance, a slerp took the wrong arc near 180 degrees, and a part was animated where nothing looked at it.
    Violations: 7

24. **Apply geometry edits to every shape key, and write keys and base vertices together. Assert that mesh, Basis and expected values agree before and after any bmesh round trip.**
    WHY: a bmesh round trip restored stale vertices and shifted other keys while screenshots still looked identical.
    Violations: 1

## D. Scripting and MCP habits

25. **Keep builders as saved, idempotent scripts with a re-apply note. Do not leave node setups or edits that exist only in the live session.**
    WHY: after a crash, only scripted work could be re-applied in minutes; live-only work was lost.
    Violations: 4

26. **After any gap (reload, crash, context compaction, mode change), check the file path, dirty flag and key values before continuing.**
    WHY: a silent reload reverted several changes without notice.
    Violations: 1

27. **Test a new material or heavy feature and render it in separate calls, and keep a saved note first.**
    WHY: a new material feature and its render in one call crashed the app twice, and unsaved work was lost.
    Violations: 1

28. **Before a bmesh round trip, check the object mode (use `bmesh.new()` plus `from_mesh` if the user left Object mode).**
    WHY: `from_edit_mesh` failed with "mesh must be in editmode".
    Violations: 1
