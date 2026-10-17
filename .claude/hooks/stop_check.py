"""Stop hook: block once if Blender work happened this turn without reviewer and recorder subagent calls.
Disable: create the file .claude/hooks/STOP_CHECK_OFF (delete it to re-enable)."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REASON = ("Blender work happened this turn: call the reviewer before presenting visual or geometry work "
          "and the recorder after, then finish.")


def blocks(entry):
    c = (entry.get("message") or {}).get("content")
    return c if isinstance(c, list) else []


def is_user_prompt(entry):
    if entry.get("type") != "user" or entry.get("isSidechain"):
        return False
    c = (entry.get("message") or {}).get("content")
    if isinstance(c, str):
        return True
    return isinstance(c, list) and any(b.get("type") == "text" for b in c if isinstance(b, dict))


def main():
    if os.path.exists(os.path.join(HERE, "STOP_CHECK_OFF")):
        return
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return
    if data.get("stop_hook_active"):
        return
    path = data.get("transcript_path")
    if not path or not os.path.exists(path):
        return
    entries = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except ValueError:
                pass
    start = 0
    for i, e in enumerate(entries):
        if is_user_prompt(e):
            start = i
    n_blender, agents = 0, set()
    for e in entries[start:]:
        if e.get("type") != "assistant":
            continue
        for b in blocks(e):
            if not isinstance(b, dict) or b.get("type") != "tool_use":
                continue
            name = b.get("name", "")
            if name.endswith("execute_blender_code"):
                n_blender += 1
            elif name in ("Agent", "Task"):
                agents.add((b.get("input") or {}).get("subagent_type"))
    if n_blender >= 4 and not ({"reviewer", "recorder"} <= agents):
        print(json.dumps({"decision": "block", "reason": REASON}))


main()
