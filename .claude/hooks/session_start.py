"""SessionStart hook: inject TEAM.md (max 4000 chars), the whole docs/PLAYBOOK.md, docs/STATE.md and the last 8 entries
of docs/LESSONS.md as additionalContext. Total budget about 12000 chars: the LESSONS lines are shortened to fit.
`python session_start.py --sizes` also prints the section sizes to stderr (for dry tests)."""
import json, os, sys

BUDGET = 12000
TEAM_MAX = 4000
TAIL = 8
root = os.environ.get("CLAUDE_PROJECT_DIR") or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def read(rel):
    try:
        with open(os.path.join(root, *rel.split("/")), encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return ""


def section(title, rel, body):
    return "## %s (%s)\n%s" % (title, rel, body) if body else ""


team = read(".claude/TEAM.md")
if len(team) > TEAM_MAX:
    team = team[:TEAM_MAX] + "\n[...cut at %d chars]" % TEAM_MAX
playbook = read("docs/PLAYBOOK.md")
state = read("docs/STATE.md")
lines = [l for l in read("docs/LESSONS.md").split("\n") if l.startswith("- ")][-TAIL:]
fixed = [section("TEAM", ".claude/TEAM.md", team), section("PLAYBOOK", "docs/PLAYBOOK.md", playbook),
         section("STATE", "docs/STATE.md", state)]
used = sum(len(s) for s in fixed) + 4 * len(fixed) + 60
per = max(70, (BUDGET - used) // max(1, len(lines)))
tail = "\n".join(l if len(l) <= per else l[:per - 3] + "..." for l in lines)
fixed.append(section("LESSONS tail (full text: docs/LESSONS.md)", "last %d" % len(lines), tail))
text = "\n\n".join(s for s in fixed if s)
try:
    sys.stdin.read()
except Exception:
    pass
if "--sizes" in sys.argv:
    sys.stderr.write("TEAM %d, PLAYBOOK %d, STATE %d, LESSONS tail %d, TOTAL injected %d (budget %d)\n"
                     % (len(team), len(playbook), len(state), len(tail), len(text), BUDGET))
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
