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
1. Restate the goal and what good looks like; read docs/PLAYBOOK.md.
2. Ground any visible anatomy in a reference image or Ilmun's pointer; if there is none, ask where.
3. Research if needed (researcher).
4. Implement in small steps with .npy backups.
5. Check frames 361/531/731/971 (numbers plus at most 4 downscaled images).
6. Reviewer.
7. Present in at most 8 lines, including what is still wrong and one suggested next order.
8. Recorder before presenting (summary of what was tried, what failed, what worked), and again after Ilmun's reply only if he gave a verdict or feedback worth recording.

The Stop hook (.claude/hooks/stop_check.py) nudges once per turn if 4+ Blender code calls happened without reviewer and recorder.
