"""qcore.py — build / validate / emit the baseball question bank.

Question shape authored in the level files (opts[0] is the correct answer;
the app shuffles options at render time):

    {"cat": "Rules", "q": "...", "opts": ["correct", "w1", "w2", "w3"], "fact": "..."}

qcore assigns contiguous ids, tags each with its level, validates hard
invariants, and emits RAW_Q.js in the exact format the app expects.
"""
import json
import re

# internal level ids must match the app engine's keys (kept identical to the
# soccer engine so the daily-pool logic keeps working); only display LABELS
# change in the app.
LEVEL_ORDER = ["rookie", "allstar", "pro", "legends"]
LEVEL_TARGET = {"rookie": 200, "allstar": 200, "pro": 200, "legends": 150}

CATEGORIES = {
    "Rules", "Boxers", "Divisions", "Titles", "Records", "History",
    "Legends", "Moments", "Trainers", "Rivalries", "Styles", "Stats",
    "Venues", "Promoters",
}

# non-timeless / date-relative phrasing that could rot. Banned outright.
BANNED = re.compile(
    r"\b(currently|reigning|most recent|last season|this season|"
    r"defending champion|so far this|as of today|right now)\b",
    re.IGNORECASE,
)


def build(level_lists):
    """level_lists: dict lv -> [question dicts]. Returns flat list with ids+lv."""
    out = []
    nid = 1
    for lv in LEVEL_ORDER:
        for q in level_lists[lv]:
            item = {
                "id": nid,
                "cat": q["cat"],
                "lv": lv,
                "q": q["q"].strip(),
                "opts": [str(o).strip() for o in q["opts"]],
                "fact": q["fact"].strip(),
            }
            out.append(item)
            nid += 1
    return out


def validate(items):
    errs = []

    # per-level counts
    counts = {lv: 0 for lv in LEVEL_ORDER}
    for it in items:
        counts[it["lv"]] = counts.get(it["lv"], 0) + 1
    for lv in LEVEL_ORDER:
        if counts.get(lv, 0) != LEVEL_TARGET[lv]:
            errs.append(f"level {lv}: have {counts.get(lv,0)}, need {LEVEL_TARGET[lv]}")

    total = len(items)
    if total != sum(LEVEL_TARGET.values()):
        errs.append(f"total {total}, need {sum(LEVEL_TARGET.values())}")

    # contiguous ids 1..N
    ids = [it["id"] for it in items]
    if ids != list(range(1, total + 1)):
        errs.append("ids are not contiguous 1..N in order")

    # no duplicate question text (normalized)
    seen = {}
    for it in items:
        key = re.sub(r"\s+", " ", it["q"].lower()).strip()
        if key in seen:
            errs.append(f"dup question text at id {it['id']} (first at id {seen[key]})")
        else:
            seen[key] = it["id"]

    # per-question structural checks
    for it in items:
        if it["cat"] not in CATEGORIES:
            errs.append(f"id {it['id']}: unknown category '{it['cat']}'")
        if len(it["opts"]) != 4:
            errs.append(f"id {it['id']}: needs exactly 4 options, has {len(it['opts'])}")
        if len(set(it["opts"])) != 4:
            errs.append(f"id {it['id']}: options not all unique -> {it['opts']}")
        if not it["opts"] or not it["opts"][0]:
            errs.append(f"id {it['id']}: missing correct answer (opts[0])")
        if not it["q"]:
            errs.append(f"id {it['id']}: empty question")
        if not it["fact"]:
            errs.append(f"id {it['id']}: missing fact")
        blob = it["q"] + " " + " ".join(it["opts"]) + " " + it["fact"]
        m = BANNED.search(blob)
        if m:
            errs.append(f"id {it['id']}: banned non-timeless phrase '{m.group(0)}'")

    return errs


def emit_js(items):
    """Emit the RAW_Q array body (one question per line) matching the app format."""
    lines = ["const RAW_Q = ["]
    for it in items:
        opts = ", ".join(json.dumps(o, ensure_ascii=False) for o in it["opts"])
        lines.append(
            "{id:%d,cat:%s,lv:%s,q:%s,opts:[%s],fact:%s},"
            % (
                it["id"],
                json.dumps(it["cat"], ensure_ascii=False),
                json.dumps(it["lv"], ensure_ascii=False),
                json.dumps(it["q"], ensure_ascii=False),
                opts,
                json.dumps(it["fact"], ensure_ascii=False),
            )
        )
    lines.append("];")
    return "\n".join(lines)
