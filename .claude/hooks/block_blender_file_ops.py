"""PreToolUse hook: stop agents from reverting, opening or saving the working .blend through Blender code tools.
Blocks (exit 2) execute_blender_code* calls whose code contains revert_mainfile, open_mainfile, read_homefile,
read_factory_settings, or save_mainfile / save_as_mainfile without copy=True."""
import json, re, sys

ALWAYS = ("revert_mainfile", "open_mainfile", "read_homefile", "read_factory_settings")
SAVES = ("save_mainfile", "save_as_mainfile")
MSG = ("Blocked: agents must not revert, open or save the working .blend (it can discard Ilmun's unsaved work). "
       "Use your own .npy coordinate backups to undo, or ask Ilmun.")

try:
    data = json.loads(sys.stdin.read() or "{}")
except ValueError:
    sys.exit(0)
if "execute_blender_code" not in str(data.get("tool_name", "")):
    sys.exit(0)
ti = data.get("tool_input")
code = ti.get("code", "") if isinstance(ti, dict) and isinstance(ti.get("code"), str) else json.dumps(ti)
if any(k in code for k in ALWAYS) or (any(k in code for k in SAVES) and not re.search(r"copy\s*=\s*True", code)):
    print(MSG, file=sys.stderr)
    sys.exit(2)
sys.exit(0)
