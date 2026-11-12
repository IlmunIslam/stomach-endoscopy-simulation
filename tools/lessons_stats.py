"""Count rule violations in docs/LESSONS.md (+ docs/lessons-archive/*.md) and keep the rule files tidy.

    python -I -B tools/lessons_stats.py [--root DIR] [--dry]

1. Counts, per PLAYBOOK rule number, the failure entries (severity not n/a) of the form
   `- YYYY-MM-DD | task | what | cause | PLAYBOOK 3 and 12 | severity` that cite the rule.
   Accepted citations: `PLAYBOOK 3, 12`, `PB 3 and 12`, `rule 3`. Failures that cite no number are listed.
2. Writes docs/RULE_STATS.md (table) and docs/RULE_STATS.json (counts + the baseline of the last reorder).
3. Reorders docs/PLAYBOOK.md by count (desc, then rule number) ONLY when some count differs from the baseline by 3+.
   Rule numbers never change, so older citations stay valid.
4. If docs/LESSONS.md is over LIMIT bytes: merges exact duplicates and entries sharing date+task+rule+severity,
   then moves the oldest entries to docs/lessons-archive/YYYY-MM.md until it is under KEEP_TARGET * LIMIT.
Stdlib only. Never touches a .blend or the scene.
"""
import argparse
import collections
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIMIT = 12000              # bytes; LESSONS.md above this is consolidated
KEEP_TARGET = 0.85
REORDER_DELTA = 3
PLAYBOOK_MAX = 5500        # characters; only warned about
CHAIN = re.compile(r"(?:PLAYBOOK|PB|rules?)\s*#?\s*(\d+(?:\s*(?:,|and|&|/|\+)\s*#?\d+)*)", re.I)
DATE = re.compile(r"^- (\d{4})-(\d{2})-(\d{2})\b")


def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def parse_entry(line):
    """Return dict(date, task, rule, sev, line) for a structured entry, else None."""
    if not DATE.match(line):
        return None
    parts = line[2:].split(" | ")
    if len(parts) < 6:
        return None
    return {"date": parts[0].strip(), "task": parts[1].strip(), "rule": parts[-2], "sev": parts[-1].strip(), "line": line}


def rule_numbers(field):
    nums = set()
    for m in CHAIN.finditer(field):
        nums |= {int(n) for n in re.findall(r"\d+", m.group(1))}
    return nums


def all_entry_lines(root):
    files = [os.path.join(root, "docs", "LESSONS.md")] + sorted(glob.glob(os.path.join(root, "docs", "lessons-archive", "*.md")))
    for p in files:
        for ln in read(p).split("\n"):
            if ln.startswith("- "):
                yield ln


def count(root):
    counts, last, uncited, total = collections.Counter(), {}, [], 0
    for ln in all_entry_lines(root):
        e = parse_entry(ln)
        if e is None or e["sev"].lower().startswith("n/a"):
            continue
        total += 1
        nums = rule_numbers(e["rule"])
        if not nums:
            uncited.append("%s %s" % (e["date"], e["task"]))
        for n in nums:
            counts[n] += 1
            last[n] = max(last.get(n, ""), e["date"])
    return counts, last, uncited, total


def parse_playbook(text):
    head, blocks, cur = [], [], None
    for ln in text.split("\n"):
        m = re.match(r"(\d+)\. ", ln)
        if m:
            cur = [int(m.group(1)), [ln]]
            blocks.append(cur)
        elif cur is None:
            head.append(ln)
        else:
            cur[1].append(ln)
    for b in blocks:
        while b[1] and not b[1][-1].strip():
            b[1].pop()
    return head, blocks


def reorder_playbook(path, counts):
    head, blocks = parse_playbook(read(path))
    blocks.sort(key=lambda b: (-counts.get(b[0], 0), b[0]))
    write(path, "\n".join(head).rstrip("\n") + "\n" + "\n".join("\n".join(b[1]) for b in blocks) + "\n")
    return [b[0] for b in blocks]


def consolidate(root, dry):
    path = os.path.join(root, "docs", "LESSONS.md")
    text = read(path)
    if len(text.encode("utf-8")) <= LIMIT:
        return "LESSONS.md %d bytes, under %d: no consolidation" % (len(text.encode("utf-8")), LIMIT)
    lines = text.rstrip("\n").split("\n")
    head = [l for l in lines if not l.startswith("- ")]
    entries = [l for l in lines if l.startswith("- ")]
    n0 = len(entries)
    seen, uniq = set(), []
    for l in entries:                                   # exact duplicates
        k = re.sub(r"\s+", " ", l).strip()
        if k not in seen:
            seen.add(k)
            uniq.append(l)
    merged, index = [], {}
    for l in uniq:                                      # same date+task+rule+severity -> one entry
        e = parse_entry(l)
        if e is None:
            merged.append(l)
            continue
        key = (e["date"], e["task"], e["rule"], e["sev"])
        if key in index:
            p = merged[index[key]].split(" | ")
            q = l[2:].split(" | ")
            p[2] += " // " + q[2]
            p[3] += " // " + q[3]
            merged[index[key]] = " | ".join(p)
        else:
            index[key] = len(merged)
            merged.append(l)

    def size(es):
        return len(("\n".join(head + es) + "\n").encode("utf-8"))
    moved = []
    while merged and size(merged) > LIMIT * KEEP_TARGET:
        moved.append(merged.pop(0))
    by_month = collections.defaultdict(list)
    for l in moved:
        m = DATE.match(l)
        by_month["%s-%s" % (m.group(1), m.group(2)) if m else "undated"].append(l)
    if not dry:
        for mon, ls in by_month.items():
            ap = os.path.join(root, "docs", "lessons-archive", mon + ".md")
            old = read(ap).rstrip("\n")
            write(ap, (old + "\n" if old else "") + "\n".join(ls) + "\n")
        write(path, "\n".join(head + merged) + "\n")
    return "consolidated: %d entries -> %d kept, %d archived, %d bytes" % (n0, len(merged), len(moved), size(merged))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(HERE))
    ap.add_argument("--dry", action="store_true", help="print only, change no file")
    a = ap.parse_args()
    root = a.root
    pb_path = os.path.join(root, "docs", "PLAYBOOK.md")
    json_path = os.path.join(root, "docs", "RULE_STATS.json")
    out = []
    counts, last, uncited, total = count(root)
    try:
        prev = json.loads(read(json_path) or "{}")
    except ValueError:
        prev = {}
    baseline = {int(k): v for k, v in (prev.get("baseline") or {}).items()}
    if not baseline:
        baseline = dict(counts)
        new_baseline = True
    else:
        new_baseline = False
    rules = sorted({n for n in list(counts) + list(baseline)} | {b[0] for b in parse_playbook(read(pb_path))[1]})
    moved = [n for n in rules if abs(counts.get(n, 0) - baseline.get(n, 0)) >= REORDER_DELTA]
    if moved and not new_baseline:
        out.append("count changed by %d+ for rule(s) %s: " % (REORDER_DELTA, moved) + ("would reorder PLAYBOOK" if a.dry else "PLAYBOOK reordered: %s" % reorder_playbook(pb_path, counts)))
        baseline = dict(counts)
    else:
        out.append("no rule count changed by %d+: PLAYBOOK order kept" % REORDER_DELTA)
    titles = {b[0]: re.sub(r"^\d+\.\s*", "", b[1][0])[:60] for b in parse_playbook(read(pb_path))[1]}
    rows = ["| rule | violations | last | rule text |", "|---|---|---|---|"]
    for n in sorted(rules, key=lambda n: (-counts.get(n, 0), n)):
        rows.append("| %d | %d | %s | %s |" % (n, counts.get(n, 0), last.get(n, "-"), titles.get(n, "")))
    md = ["# Rule stats (generated by tools/lessons_stats.py; do not edit)", "",
          "Failure entries counted: %d (archive included). Failures citing no rule number: %d%s" % (
              total, len(uncited), (" -> " + "; ".join(uncited[:6])) if uncited else ""), ""] + rows
    if not a.dry:
        write(os.path.join(root, "docs", "RULE_STATS.md"), "\n".join(md) + "\n")
        write(json_path, json.dumps({"counts": {str(k): v for k, v in sorted(counts.items())},
                                     "baseline": {str(k): v for k, v in sorted(baseline.items())}}, indent=1) + "\n")
    out.append(consolidate(root, a.dry))
    pb = read(pb_path)
    if len(pb) > PLAYBOOK_MAX:
        out.append("WARNING: PLAYBOOK.md is %d chars (max %d): merge or drop the weakest rule" % (len(pb), PLAYBOOK_MAX))
    out.append("failures %d, uncited %d; top: %s" % (total, len(uncited), ", ".join("#%d=%d" % (n, c) for n, c in counts.most_common(5))))
    print("\n".join(out))


if __name__ == "__main__":
    sys.exit(main())
