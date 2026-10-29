# TEAM
Ilmun gives plain prompts. The Lead (the main session) works with him directly and does ALL Blender work, because the tight loop with Ilmun gave the best results. Specialists are called only when they help.

## Roster
- researcher (subagent, web, no Blender): use when anatomy, references or technique knowledge is missing. Ask ONE question; it returns a short sourced answer.
- scout (subagent, web, no Blender): use weekly or when Ilmun asks what could be added; it proposes, never installs.
- reviewer (subagent, read-only, fresh eyes): use BEFORE presenting any visual or geometry work. Give it the order, success criteria, before/after paths, numbers and reference paths. It returns PASS or FIX FIRST and a ranked defect list; fix real defects.
- recorder (subagent): use AFTER each task and after any failed attempt. Give it a short summary.
- learner (on demand via /learn): researches docs/knowledge/QUEUE.md topics and writes technique cards. Not used during a Blender task.

Subagents cannot call each other: one that needs another ends with "NEEDS: <agent>: <question>" and the Lead relays.

## Flow for a Blender request (serial, because there is one Blender)
1. Restate the goal and what good looks like; read docs/PLAYBOOK.md. Take the before-snapshot of frames 361, 531, 731 and 971 (small render plus numbers) with `tools/canonical_check.py` (`snapshot("before")`).
2. Ground any visible anatomy in a reference image or Ilmun's pointer; if there is none, ask where.
3. Research if needed (researcher).
4. Implement in small steps with .npy backups. For topology edits (delete, merge, cover, rebuild) also keep each backup as a datablock written to a side .blend outside the scene with `bpy.data.libraries.write(path, {datablocks})`; never delete these backups until Ilmun approves.
5. Check the same four frames with `snapshot("after")` and `compare("before", "after")` (numbers plus at most 4 downscaled images). Check every fix from the endoscope (scene) camera, not only Ilmun's viewport.
6. Reviewer. The Lead iterates (fix, re-check, reviewer) until the reviewer returns PASS, at most 4 rounds, before presenting. If 3 patches on one region have failed, stop patching and rebuild that region (PLAYBOOK 13).
7. Present only the final state, in at most 8 lines, with an honest status (PASS, or after 4 rounds what is still wrong and the reviewer's last defects), plus one suggested next order. Do not present intermediate rounds.
8. Recorder before presenting (summary of what was tried, what failed, what worked), and again after Ilmun's reply only if he gave a verdict or feedback worth recording.

The Stop hook (.claude/hooks/stop_check.py) nudges once per turn if 4+ Blender code calls happened without reviewer and recorder.
