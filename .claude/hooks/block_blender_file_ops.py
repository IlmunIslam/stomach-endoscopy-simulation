"""PreToolUse hook: stop agents from reverting, opening or saving the working .blend through Blender code tools.
Scans the WHOLE serialized tool_input (not one named field) of execute_blender_code* calls and blocks (exit 2) if it contains
revert_mainfile, open_mainfile, read_homefile, read_factory_settings, or save_mainfile / save_as_mainfile without copy=True.
Fails closed: any parse problem or unexpected error also exits 2 with the reason on stderr."""
import json, re, sys


def main():
    ALWAYS = ("revert_mainfile", "open_mainfile", "read_homefile", "read_factory_settings")
    SAVES = ("save_mainfile", "save_as_mainfile")
    raw = sys.stdin.read()
    if not raw.strip():
        return "hook got empty input, cannot tell what the call does"
    data = json.loads(raw)
    if not isinstance(data, dict):
        return "hook input is not a JSON object"
    if "tool_input" not in data:
        return "hook input has no tool_input (keys: %s)" % sorted(data.keys())
    name = str(data.get("tool_name", ""))
    if name and "execute_blender_code" not in name:
        return None
    # serialize both raw and unescaped so quoting/escaping cannot hide a keyword
    blob = json.dumps(data["tool_input"], ensure_ascii=False) + "\n" + json.dumps(data["tool_input"])
    hit = [k for k in ALWAYS if k in blob]
    if not hit and any(k in blob for k in SAVES) and not re.search(r"copy\s*=\s*True", blob):
        hit = [k for k in SAVES if k in blob]
    if hit:
        return ("Blocked: agents must not revert, open or save the working .blend (it can discard Ilmun's unsaved work). "
                "Found %s. Use your own .npy coordinate backups to undo, or ask Ilmun." % ", ".join(hit))
    return None


try:
    problem = main()
except BaseException as exc:  # fail closed on anything unexpected, including bad JSON
    problem = "hook error, blocking to be safe: %s: %s" % (type(exc).__name__, exc)
if problem:
    print(problem, file=sys.stderr)
    sys.exit(2)
sys.exit(0)
