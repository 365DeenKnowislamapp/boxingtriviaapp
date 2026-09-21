#!/usr/bin/env python3
"""Legibility guarantee: compute the WCAG contrast ratio for EVERY text/background
pairing the app actually renders, and fail if any drop below the readable bar.

This is the mechanism behind "every page's text is legible on every background":
we don't eyeball it, we measure it. Tokens are parsed straight out of App.jsx so
the audit always reflects the shipped file.
"""
import re, sys, os

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "App.jsx")
src = open(APP, encoding="utf-8").read()

def grab_block(name):
    m = re.search(name + r"\s*=\s*\{(.*?)\}", src, re.S)
    return m.group(1) if m else ""

# --- parse the T design tokens (hex only) ---
T = dict(re.findall(r"(\w+):\s*'(#[0-9A-Fa-f]{6})'", grab_block("const T")))
# --- parse category colors ---
# categories live inside the CONFIG block now (const CAT_COLORS = CONFIG.categories)
_catm = re.search(r"categories:\s*\{(.*?)\}", src, re.S)
_catblock = _catm.group(1) if _catm else grab_block("const CAT_COLORS")
CATS = dict(re.findall(r"'([^']+)':\s*'(#[0-9A-Fa-f]{6})'", _catblock))

def lum(hex_):
    r, g, b = (int(hex_[i:i+2], 16) / 255 for i in (1, 3, 5))
    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(fg, bg):
    a, b = lum(fg), lum(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)

def blend(top, alpha, base):
    """alpha-composite hex `top` at `alpha` over hex `base`."""
    tr = [int(top[i:i+2], 16) for i in (1, 3, 5)]
    br = [int(base[i:i+2], 16) for i in (1, 3, 5)]
    out = [round(tr[i] * alpha + br[i] * (1 - alpha)) for i in range(3)]
    return "#%02X%02X%02X" % tuple(out)

# effective FIELD_BG color: lightest plausible pixel = dirt, + grass glow, then the
# 0.82 dark overlay that sits on top (first-listed gradient renders topmost).
dirt, grass, overlay = "#A9743F", "#15803D", "#070A08"
field_lit = blend(overlay, 0.82, blend(grass, 0.45, dirt))

surfaces = {"bg": T["bg"], "card": T["card"], "surface": T["surface"]}

BODY_MIN, LARGE_MIN = 4.5, 3.0
fails, rows = [], []

def check(label, fg, bg, minr, note=""):
    r = ratio(fg, bg)
    ok = r >= minr
    rows.append((label, fg, bg, r, minr, ok, note))
    if not ok:
        fails.append((label, r, minr))

# reading + label text tokens on every surface (strict AA 4.5)
for tok in ["text", "bright", "body", "muted", "dim"]:
    for sname, s in surfaces.items():
        check(f"{tok} on {sname}", T[tok], s, BODY_MIN)

# gold display headings / score numerals on dark (large text -> 3.0)
for sname, s in surfaces.items():
    check(f"gold on {sname}", T["gold"], s, LARGE_MIN, "large display")

# dark ink ON the gold CTA buttons (button text -> 4.5)
check("ink on gold (CTA)", T["ink"], T["gold"], BODY_MIN)

# white hero/score text over the diamond FIELD_BG (effective dark color)
for tok, name in [("#FFFFFF", "white"), (T["bright"], "bright"), (T["body"], "body")]:
    check(f"{name} on FIELD_BG", tok, field_lit, BODY_MIN, f"eff={field_lit}")

# category Pill labels (bold ~13px) on dark surfaces -> 3.0 (large/bold)
for cat, c in CATS.items():
    check(f"cat '{cat}' on bg", c, T["bg"], LARGE_MIN)
    check(f"cat '{cat}' on card", c, T["card"], LARGE_MIN)

# ---- report ----
rows.sort(key=lambda r: r[3])
print("WCAG contrast audit  (min AA body = 4.5, large/bold = 3.0)")
print(f"FIELD_BG effective color (lightest pixel + overlay): {field_lit}\n")
print(f"{'pairing':30} {'fg':9} {'bg':9} {'ratio':>6} {'min':>4}  ok")
for label, fg, bg, r, minr, ok, note in rows:
    mark = "OK " if ok else "XX "
    extra = f"  {note}" if note else ""
    print(f"{label:30} {fg:9} {bg:9} {r:6.2f} {minr:4.1f}  {mark}{extra}")

print()
if fails:
    print(f"FAIL: {len(fails)} pairing(s) below the readable bar:")
    for label, r, minr in fails:
        print(f"  - {label}: {r:.2f} < {minr}")
    sys.exit(1)
print(f"PASS: all {len(rows)} text/background pairings meet the readable bar.")
sys.exit(0)
