#!/usr/bin/env python3
"""Coverage numbers in this repo's prose must match DC Hub's LIVE canon.

★ WHY THIS REPO DRIFTS. dchub-desktop-extension is outside the mcp-server
manifest-drift pipeline (registry-refresh.yml / daily-manifest-sync.yml), and
Glama mirrors it as a second front door for Claude Desktop users. So its prose
rots in public with nothing pulling it forward.

★ WHY THE PREVIOUS GUARD DID NOT STOP THAT. It banned a hardcoded list of
retired literals and printed its own canon in the failure message:

    "canonical floor is 4,000+" deals      live canon 2,100+
    "canonical is 21,000+" facilities      live canon 20,500+
    "server exposes 73" tools              live canon 83

Every one of those was itself stale by 2026-09-05, and the README it was
guarding said "21,000+ facilities" and "4,000+ tracked M&A deals" — both wrong,
both green, because a ban-list can only catch the specific wrong numbers
someone thought of on the day they wrote it. A fence that hardcodes canon
becomes a second thing to keep in sync, and then starts asserting the stale
answer. It is the same defect it exists to prevent, one level up.

So this reads canon instead of restating it:
`https://dchub.cloud/api/v1/canon/phrases` — the same source the site's own
surfaces resolve from. Every count-shaped phrase in the prose must EQUAL the
live value for its unit. Numbers nobody anticipated are caught the same as the
ones we already know about.

Network policy: canon unreachable is UNMEASURED, not pass. The check falls back
to a dated pin and says so loudly, so a CI run that could not reach canon never
reads as a run that verified it — could-not-run is not ran-and-passed.

Deliberately NOT checked: the LENGTH of manifest.json's `tools[]`. This
extension declares a curated 14 and bridges to all of them at runtime; that
subset is a product decision, not drift. The prose INSIDE those entries is
checked like any other — a stale "21,000+ data-center facilities" sat in a tool
description precisely because an earlier version skipped the array wholesale.
A checker has to read everything the package publishes, not a convenient slice
of it.

Usage:  python3 scripts/check-canon-numbers.py [--self-test]
Exit 0 clean, 1 on drift, 2 if the prose cannot be read.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request

CANON_URL = "https://dchub.cloud/api/v1/canon/phrases"

# Last-known-good, with the date it was read. Only used when canon is
# unreachable, and never silently — see _canon().
PINNED = {"facilities": 24600, "markets": 300, "deals": 1600, "tools": 92}
PINNED_AT = "2026-09-25"

# (unit, pattern). Each pattern captures the number and is anchored on the NOUN,
# so "13 guided prompts" and "a curated 14-tool manifest" are not counts we own.
PATTERNS: list[tuple[str, str]] = [
    ("facilities", r"([\d,]+)\+?\s*(?:global\s+)?data.?cent(?:er|re)\s+facilit\w*"),
    ("markets", r"([\d,]+)\+?\s*(?:US\s+|global\s+|power\s+)*markets\b"),
    ("deals", r"([\d,]+)\+?\s*(?:tracked\s+)?(?:M&A\s+)?(?:transactions|deals)\b"),
    # The qualifier list is deliberate: "83 DC Hub tools" slipped past an
    # MCP-only version of this pattern and shipped a retired 73 in the manifest.
    ("tools", r"\b([\d,]+)\+?\s*(?:MCP\s+|DC\s+Hub\s+|live\s+)?tools\b"),
    # The README's "- **Tools:** 53" bullet (label before number) sat at 53
    # while the prose above was fixed, because every pattern here is
    # number-then-noun.
    ("tools", r"\bTools:\**\s*([\d,]+)"),
]


def _canon() -> tuple[dict, str]:
    """(canon, provenance). Falls back to the pin, loudly, never silently."""
    try:
        req = urllib.request.Request(
            CANON_URL, headers={"User-Agent": "dchub-desktop-extension-ci/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.load(r)
        got = {k: int(str(d[k]).replace(",", "").rstrip("+"))
               for k in ("facilities", "markets", "deals", "tools") if k in d}
        if len(got) == 4:
            return got, "live"
        print(f"::warning::canon endpoint returned only {sorted(got)} — "
              f"using the {PINNED_AT} pin for the rest")
        return {**PINNED, **got}, "partial"
    except Exception as e:  # noqa: BLE001
        print(f"::warning::UNMEASURED against live canon ({type(e).__name__}: "
              f"{str(e)[:120]}) — falling back to the {PINNED_AT} pin. This run "
              f"did NOT verify against {CANON_URL}.")
        return dict(PINNED), "pinned"


def find_counts(prose: str) -> list[tuple[str, str, int]]:
    """[(unit, matched_text, value)] for every count-shaped phrase found."""
    out = []
    for unit, pat in PATTERNS:
        for m in re.finditer(pat, prose, re.I):
            raw = m.group(1).replace(",", "")
            if raw.isdigit():
                out.append((unit, m.group(0).strip(), int(raw)))
    return out


def lint(prose: str, canon: dict) -> list[str]:
    bad = []
    for unit, text, value in find_counts(prose):
        want = canon.get(unit)
        if want is not None and value != want:
            bad.append(f"{unit}: {text!r} — canon is {want:,}")
    return bad


def _prose() -> str:
    try:
        prose = open("README.md", encoding="utf-8").read()
    except FileNotFoundError:
        print("::error::README.md not found")
        sys.exit(2)
    try:
        m = json.load(open("manifest.json", encoding="utf-8"))
        prose += "\n" + (m.get("description") or "")
        prose += "\n" + (m.get("long_description") or "")
        for t in (m.get("tools") or []):
            if isinstance(t, dict):
                prose += "\n" + (t.get("description") or "")
    except Exception as e:  # noqa: BLE001
        print(f"::warning::manifest.json unreadable ({e}) — checking README only")
    return prose


def _self_test() -> int:
    canon = {"facilities": 20500, "markets": 300, "deals": 2100, "tools": 83}
    bad = 0

    def ok(cond, label):
        nonlocal bad
        print(f"{'  ok  ' if cond else '  FAIL'} {label}")
        if not cond:
            bad += 1

    good = ("20,500+ data-center facilities across 170+ countries, 300+ power "
            "markets, and 2,100+ tracked M&A deals. 83 tools.")
    ok(lint(good, canon) == [], "CONTROL: fully canon-bound prose is clean")

    ok(any("deals" in v for v in lint(good.replace("2,100+", "4,000+"), canon)),
       "the retired 4,000+ deal count is caught")
    ok(any("facilities" in v for v in lint(good.replace("20,500+", "21,000+"), canon)),
       "the retired 21,000+ facility count is caught")
    ok(any("tools" in v for v in lint(good.replace("83 tools", "73 tools"), canon)),
       "the retired 73-tool count is caught")

    # The point of reading canon rather than a ban-list: a number nobody wrote
    # a rule for is caught the same as one we already knew about.
    ok(any("markets" in v for v in lint(good.replace("300+ power markets",
                                                     "412 power markets"), canon)),
       "an UNANTICIPATED wrong number is caught (no ban-list entry for it)")

    ok(any("tools" in v for v in lint("bridges to all 73 DC Hub tools", canon)),
       "a qualifier between the number and 'tools' does not hide the count")

    ok(any("tools" in v for v in lint("- **Tools:** 53 — query *and* cite", canon)),
       "a label-first 'Tools: N' bullet is checked too")

    ok(lint("13 guided prompts and a curated 14-tool manifest", canon) == [],
       "prompt counts and the curated tool subset are not coverage claims")

    # A pattern that matches nothing passes vacuously — assert we can SEE.
    ok(len(find_counts(good)) == 4,
       "all four units are actually extracted (a silent no-match would pass)")

    print(f"\n{bad} FAILED\n" if bad else "\nall checks passed\n")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return _self_test()
    prose = _prose()
    canon, provenance = _canon()
    found = find_counts(prose)
    bad = lint(prose, canon)
    if bad:
        print("::error::Coverage numbers disagree with DC Hub canon "
              f"({provenance}: {canon}):")
        for b in sorted(set(bad)):
            print(f"  x {b}")
        print("\nRead the live values: " + CANON_URL)
        return 1
    print(f"OK — {len(found)} coverage number(s) match canon ({provenance}): "
          + ", ".join(f"{u}={canon[u]:,}" for u in sorted(canon)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
