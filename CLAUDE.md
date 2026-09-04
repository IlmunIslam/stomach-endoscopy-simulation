# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Non-negotiable rules

These override everything else in this file, and every instinct to be helpful by doing more.

1. **Never save. Ever.** Saving is the user's job, done by them after their own review. Do not call
   `bpy.ops.wm.save_mainfile`, `save_as_mainfile`, autosave, "just a quick checkpoint", or any variant — not even to
   protect work, not even before something risky. If a save seems necessary, say so and stop. The only exception is an
   explicit, specific instruction to save in that moment, and it does not carry over to the next action.
2. **Only touch what you are told to touch.** Named object, named file, named setting — that and nothing adjacent. Do
   not tidy, rename, reorganize, fix an unrelated problem you noticed, or "while I was in there" anything. Report what
   you notice; let the user decide.
3. **Only do what you have permission for.** Permission is per-action and does not generalize. Approval to inspect is
   not approval to modify; approval to modify one object is not approval to modify another. When the next step isn't
   explicitly covered, ask before acting.
4. **Ignore schedules and timelines.** Dates, weeks, and progress tracking are not your concern and must not drive any
   suggestion or action. Do not propose work because a plan says it's due.
5. **Don't survey this folder.** At the start of a session, read this file and nothing else. No listing the tree, no
   opening the `.docx` files, no scanning `.blend`/`.fbx`/texture files, no "getting oriented" pass — that burns tokens
   and tells you nothing this file doesn't. The work happens in the **live Blender session over MCP**, so go straight
   there. Open a file on disk only when the current task actually needs that specific file, and only that one.

Reading, inspecting, screenshotting, and reporting are always fine. Anything that changes scene state or writes to disk
is not, without being asked for it directly.

## What this is

This is **not a software codebase** — there is no build, lint, or test step, and no source tree. It is a Blender
asset-production folder for an **endoscopic stomach simulation**: anatomical interior surfaces are generated from
reference endoscopy images in 3D AI Studio, cleaned up in Blender, merged into a pre-existing stomach shell, and
finally exported to Unity for real-time simulation.

Two Word docs in this folder (`stomach_workflow_plan.docx`, `Endoscopic_Simulation_Schedule.docx`) describe the
pipeline and naming conventions. Everything still useful in them is already summarized below, so per rule 5 don't open
them by default — only if the user asks about their contents. Their week-by-week plans and status tables are stale and
out of scope per rule 4; never take "what to do next" from them.

## Live Blender connection (MCP)

A `blender` MCP server is configured at **user scope** in `~/.claude.json`, so it applies here automatically:

```
uv --directory C:\blender_mcp\mcp run blender-mcp
```

It talks to the official Blender MCP add-on, which listens on **127.0.0.1:9876** inside the running Blender process.
When it works you get 26 tools (`get_objects_summary`, `execute_blender_code`, screenshot/render helpers, bundled
Blender API + manual docs). Operational facts learned the hard way:

- **Never bind port 9876 yourself.** On Windows `SO_REUSEADDR` lets a second listener bind an already-bound port, so a
  helper server silently hijacks traffic from the real add-on and produces baffling symptoms.
- The server **requires the 1.x MCP SDK** — `mcp` 2.x removed `mcp.server.fastmcp`, which `blmcp` imports. This is
  pinned as `mcp[cli]>=1.2.0,<2` in `C:\blender_mcp\mcp\pyproject.toml` and `requirements.txt`. Don't loosen it.
- A cold `uv` run that has to download dependencies can exceed the 30s MCP connect timeout. Warm it with
  `uv --directory C:\blender_mcp\mcp sync` before blaming the config.
- `get_screenshot_of_window_as_image` returns a **fully black image if the Blender window is minimized**. Ask for the
  window to be restored, or use an OpenGL viewport render instead.

Health check: `claude mcp list`.

## Working with the scene

- **Prefer read-only tools.** `get_objects_summary`, `get_object_detail_summary`, and the screenshot tools change
  nothing. Reach for `execute_blender_code` only when nothing read-only will do, and keep it non-mutating unless the
  user asked for a change.
- **Watch for incidental writes.** Some operations dirty the file as a side effect (e.g. setting
  `scene.render.filepath` for an OpenGL grab). Restore any property you had to change, and mention that you touched it.
- **Don't trigger full renders casually.** The scene is on **Cycles / CPU, 64 samples, 1920×1080** with a 2 GB GPU, so
  `render_viewport_to_path` takes minutes. For a quick visual, run `bpy.ops.render.opengl(write_still=True)` under a
  `temp_override` on a `VIEW_3D` area — it writes a PNG, not the .blend.
- **If a save is ever explicitly requested**, use `save_as_mainfile(..., copy=True)` so the session keeps pointing at
  the working file; a plain Save As re-points it, and every later Ctrl+S then silently writes to the snapshot instead.
- Meshes are large (`PART_11_Colon` alone is ~300k verts / ~600k tris). Inspect progressively; don't dump whole scenes.

Read a saved `.blend` without touching the live session — the safest way to answer questions about file contents:

```
& "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" -b "<file>.blend" --python <script.py> --factory-startup
```

Blender **5.1** and **5.0** are both installed under `C:\Program Files\Blender Foundation\`. The live file is authored
in 5.1.2.

## File and naming conventions

**Shell versions** — `Stomach_Shell_v{N}_{W#}_{Region}_done.blend`, one version per completed anatomical part. The
current working file is `Stomach_Shell_v7_Manual edit done.blend`. `.blend1` files are Blender's rolling auto-backups,
not deliverables. `Colon.blend` and `Stomach.blend` are early standalone sources.

**Objects** — the convention from both docs is `PART_W[n]_[RegionName]`, used for Unity identification after export.
Note two existing deviations: `PART_9_Duodenal bulb` and `PART_11_Colon` drop the `W` and contain a space. Do not
rename them — flag it and leave it alone; Unity-side references may depend on the current names.

**Per-part folders** (`W0_Hypopharynx/`, `W1_GEJ_ZLine/`, `W2_Cardia_Retroflexed/`, `W5_Antrum/`, `W6_Pylorus/`) each
hold raw 3D AI Studio output in a consistent shape:

- `<hash>.fbx` (~2 MB) — low-poly/quick mesh
- `image_edited_<prompt-fragment>.fbx` (~70 MB) — the full-resolution generated mesh actually used
- `<hash>.zip` — the original download bundle
- `Color_<uuid>.jpg`, `NormalGL_<uuid>.jpg`, `ORM_<uuid>.jpg` — PBR maps. `W5_Antrum` has **only** the Color map.

Generated meshes keep their `tripo_mesh_<hash>` datablock names inside Blender, which is how you tell AI-generated parts
from hand-modeled ones (`Stomach`, `Esophagus Tube`, `Breathing tube` all use `Sphere*` datablocks).

**Merge quality rule** (from the workflow doc, independent of any schedule): finish and validate a part's merge before
moving to another part — don't carry a pending mesh issue forward.

## Scene facts worth knowing

Verify against the live scene rather than trusting this list; it is a snapshot, not a contract.

- Everything sits flat in one `Collection` — no nesting, no parenting anywhere.
- `Stomach` has a `Basis` shape key only, and no vertex groups.
- `PART_9_Duodenal bulb` was duplicated from the colon mesh (`human colon 1 meshed.001`), so the two are separate
  datablocks despite the shared lineage — editing one will not affect the other.
- `PART_11_Colon`, `Cylinder`, `BézierCurve`, and `NurbsPath` are hidden in the viewport.

## Reading the .docx files

There is no Word automation here; extract the text directly:

```python
import re, zipfile
xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8", "replace")
text = re.sub(r"<[^>]+>", "", re.sub(r"</w:p>", "\n", xml))
```
