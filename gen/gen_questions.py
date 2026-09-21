#!/usr/bin/env python3
"""Assemble the 750-question bank -> RAW_Q.js.

Each level file over-authors; we slice deterministically to the exact target
(sorted as authored), so counts are guaranteed 200/200/200/150 and the free
subsets (first 20 rookie, first 10 veteran by id) are stable across replays.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qcore
import q_rookie, q_allstar, q_pro, q_legends

SRC = {
    "rookie": q_rookie.QUESTIONS,
    "allstar": q_allstar.QUESTIONS,
    "pro": q_pro.QUESTIONS,
    "legends": q_legends.QUESTIONS,
}

def main():
    level_lists = {}
    for lv in qcore.LEVEL_ORDER:
        target = qcore.LEVEL_TARGET[lv]
        pool = SRC[lv]
        if len(pool) < target:
            print(f"FAIL: level {lv} has {len(pool)} < target {target}")
            return 1
        level_lists[lv] = pool[:target]

    items = qcore.build(level_lists)
    errs = qcore.validate(items)
    if errs:
        print("FAIL: validation errors:")
        for e in errs[:40]:
            print("  -", e)
        print(f"  ...({len(errs)} total)" if len(errs) > 40 else "")
        return 1

    js = qcore.emit_js(items)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "RAW_Q.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write(js + "\n")

    counts = {lv: 0 for lv in qcore.LEVEL_ORDER}
    for it in items:
        counts[it["lv"]] += 1
    print(f"OK: {len(items)} questions, ids 1..{len(items)}, no dup text, level counts correct.")
    print("   level counts:", counts)
    print("   wrote", out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
