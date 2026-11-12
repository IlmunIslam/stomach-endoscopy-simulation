"""UserPromptSubmit hook: add a short rules reminder (max 300 chars) to substantive prompts.
Prompts under MIN_LEN characters ("ok", "yes", "continue") get nothing, to save tokens. Fails open."""
import json, sys

MIN_LEN = 12
REMINDER = ("Before any Blender edit write one line \"Rules applying: #..\" (PLAYBOOK numbers that fit this task). "
            "Measure before choosing a fix. Identify what draws an artefact (ray-cast hit.object) before editing. "
            "Setups only via tools/ scripts.")
assert len(REMINDER) <= 300

try:
    data = json.loads(sys.stdin.read() or "{}")
    prompt = str(data.get("prompt", "")).strip()
except Exception:
    sys.exit(0)
if len(prompt) >= MIN_LEN:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": REMINDER}}))
