# TEAM
Ilmun gives plain prompts. The Lead (main session) works with him directly and does ALL Blender work. Specialists only when they help. Session start loads TEAM, PLAYBOOK, STATE and the last LESSONS lines; read nothing else unless the task needs it.

## Roster
- researcher (web, no Blender): anatomy, reference or technique unknown. One question, short sourced answer.
- scout (web, no Blender): weekly or on request; proposes, never installs.
- reviewer (read-only, fresh eyes): BEFORE presenting visual or geometry work. Give it the order, criteria, before/after paths, numbers, reference paths. Returns PASS or FIX FIRST plus ranked defects.
- recorder: AFTER each task and failed attempt, with a short summary. It appends LESSONS entries citing rule numbers and runs tools/lessons_stats.py.
- learner (/learn): researches docs/knowledge/QUEUE.md topics. Not during a Blender task.
Subagents cannot call each other: they end with "NEEDS: <agent>: <question>" and the Lead relays.

## Flow for a Blender request (serial, one Blender)
1. Restate goal and what good looks like. Write one line "Rules applying: #..." (PLAYBOOK numbers). Before-snapshot: `canonical_check.snapshot("before")` (4 frames + camera path check).
2. Ground visible anatomy in a reference or Ilmun's pointer; none: ask.
3. Research if needed (researcher).
4. Small steps with .npy backups. Topology edits (delete, merge, cover, rebuild) also keep a datablock backup in a side .blend via `bpy.data.libraries.write`; keep until Ilmun approves.
5. Every material, node or modifier setup is built by an idempotent script in tools/, never only in the live session (PLAYBOOK 22).
6. `snapshot("after")` then `compare("before", "after")` (numbers, path_check, at most 4 small images). Check from the scene camera, not only the viewport.
7. Reviewer; iterate until PASS, max 4 rounds. After 3 failed patches on one region rebuild it (PLAYBOOK 13).
8. Present only the final state in at most 8 lines with honest status plus one suggested next order.
9. Recorder before presenting; again after Ilmun's verdict if worth recording.
10. Rewrite docs/STATE.md (max 1500 chars): stage, last approved or saved, open problems, next step.

Stop hook (.claude/hooks/stop_check.py): blocks once per turn if (a) 4+ Blender code calls ran without reviewer and recorder, or (b) the final reply claims SAME, PASS, unchanged or checked but no canonical_check compare result is newer than the turn start. Off switch: file .claude/hooks/STOP_CHECK_OFF.
UserPromptSubmit hook adds a 1-line rules reminder to substantive prompts.
