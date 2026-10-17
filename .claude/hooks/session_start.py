"""SessionStart hook: inject .claude/TEAM.md and docs/PLAYBOOK.md (each cut to 6000 chars) as additionalContext."""
import json, os, sys

LIMIT = 6000
root = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
parts = []
for rel, title in ((".claude/TEAM.md", "TEAM"), ("docs/PLAYBOOK.md", "PLAYBOOK")):
    p = os.path.join(root, *rel.split("/"))
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            txt = f.read()
    except OSError:
        continue
    if len(txt) > LIMIT:
        txt = txt[:LIMIT] + "\n[...cut at 6000 characters]"
    parts.append("## %s (%s)\n%s" % (title, rel, txt))
try:
    sys.stdin.read()
except Exception:
    pass
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n\n".join(parts)}}))
