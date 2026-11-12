"""Stop hook v2: block ONCE per turn (when Blender code ran this turn) if
  (a) 4+ Blender code calls happened without both reviewer and recorder subagent calls, or
  (b) the final reply claims SAME, PASS, unchanged or checked but no canonical_check compare result file
      (compare_*.json in the results folder) is newer than the turn start.
Results folder: env CANONICAL_RESULTS_DIR, else results_dir in project_config.json, else <tempdir>/canonical_check/results.
Disable: create the file .claude/hooks/STOP_CHECK_OFF (delete it to re-enable). Fails open on any parse problem."""
import datetime, glob, json, os, re, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(HERE))
CLAIM = re.compile(r"\b(?:SAME|PASS)\b|(?i:\b(?:unchanged|checked)\b)")
R_AGENTS = ("Blender work happened this turn: call the reviewer before presenting visual or geometry work "
            "and the recorder after, then finish.")
R_CLAIM = ("The reply claims SAME/PASS/unchanged/checked but no canonical_check compare result is newer than this turn's "
           "start. Run snapshot + compare (tools/canonical_check.py), or relabel the claim 'not run / Lead-reported'.")


def results_dir():
    d = os.environ.get("CANONICAL_RESULTS_DIR")
    if d:
        return d
    try:
        with open(os.path.join(ROOT, "project_config.json"), encoding="utf-8") as f:
            d = json.load(f).get("results_dir")
    except (OSError, ValueError):
        d = None
    return d or os.path.join(tempfile.gettempdir(), "canonical_check", "results")


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


def epoch(ts):
    try:
        return datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


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
    n_blender, agents, final_text = 0, set(), ""
    for e in entries[start:]:
        if e.get("type") != "assistant" or e.get("isSidechain"):
            continue
        for b in blocks(e):
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                final_text = ""
                name = b.get("name", "")
                if name.endswith("execute_blender_code"):
                    n_blender += 1
                elif name in ("Agent", "Task"):
                    agents.add((b.get("input") or {}).get("subagent_type"))
            elif b.get("type") == "text":
                final_text += "\n" + str(b.get("text", ""))
    if n_blender == 0:
        return
    final_text = str(data.get("last_assistant_message") or final_text)
    reasons = []
    if n_blender >= 4 and not ({"reviewer", "recorder"} <= agents):
        reasons.append(R_AGENTS)
    t0 = epoch(entries[start].get("timestamp")) if entries else None
    if t0 is not None and CLAIM.search(final_text):
        fresh = [p for p in glob.glob(os.path.join(results_dir(), "compare_*.json")) if os.path.getmtime(p) >= t0 - 1]
        if not fresh:
            reasons.append(R_CLAIM)
    if reasons:
        print(json.dumps({"decision": "block", "reason": " ".join(reasons)}))


try:
    main()
except Exception:
    pass
