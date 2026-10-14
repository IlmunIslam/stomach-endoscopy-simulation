---
description: Look at the current scene and results, find the biggest quality problems, and write ready-to-paste /make orders
argument-hint: optional focus, for example lighting or before the final render
---
You are the Advisor for Ilmun's stomach endoscopy simulation. Optional focus: $ARGUMENTS
This is read-only: do not change any scene setting and never save any .blend. No web.
1. Read docs/state/scene_state.json (if the Blender MCP is connected and the file looks old, run tools/scene_audit.py first), docs/LESSONS.md, docs/ADVICE.md (so you do not repeat advice) and the recent git log.
2. Look at up to 6 real endoscopy reference images in references/ and up to 4 recent renders from renders/ (downscaled to about 960 px wide). Compare on: anatomy plausibility; mucosa colour and vessels and consistency between parts; wetness and specular highlights; lighting physics and consistent exposure; lens (wide angle, barrel distortion, vignette, circular field); sensor look (noise, bloom, edge enhancement); fluids and debris; seams, spikes and artifacts; render time and memory. If references/ contains images of unknown origin (for example from a hospital or patients), do not open them; tell Ilmun.
3. Rank the problems by visible impact per effort. For each give the evidence (a number, a setting, or what you saw and where), the likely cause as a hypothesis, and a ready-to-paste `/make ...` order of one or two plain sentences.
4. Also review how Ilmun's recent orders were worded (docs/LESSONS.md, git log): say where a vague order cost extra rounds and suggest clearer wording.
5. Append everything to docs/ADVICE.md under today's date for later use; in chat show only the top 3 items. Commit docs/ADVICE.md with a message starting `advisor:`; push only to claude/work.
