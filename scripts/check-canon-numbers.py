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
surfaces resolve from. Numbers nobody anticipated are caught the same as the
ones we already know about.

★ THE RULE (owner decision, 2026-09-26). A published "+" number is a FLOOR, P,
compared with the live canon value C for its unit:
    P > C                        FAIL  — an overclaim is the real defect
    C*(1-FLOOR_TOLERANCE) <= P < C  PASS with a ::warning:: nudge to refresh
    P == C                       PASS
    P < C*(1-FLOOR_TOLERANCE)    FAIL  — too stale
Tools carry no "+" and stay an EXACT match; so does any count published without
a "+". Exact equality on floors made main red the day canon moved 24,600 ->
24,800 while the prose still said a true "24,600+".

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
PINNED = {"facilities": "withheld", "markets": 300, "deals": 1700, "tools": 94}
PINNED_AT = "2026-10-09"

# Canon publishes a non-numeric value (e.g. facilities = "corroborated count
# pending", frozen by the owner since 2026-09-29) when a count is WITHHELD.
# Any published number for a withheld unit is drift. Before this, int() raised
# on the string and the whole run fell back to the stale pin.
WITHHELD = "withheld"


def _canon_value(v):
    # strip() BEFORE rstrip("+"): "1,700+ " (trailing space) must read 1700,
    # not fall through to WITHHELD.
    raw = str(v).replace(",", "").strip().rstrip("+").strip()
    return int(raw) if raw.isdigit() else WITHHELD

# How far below canon a published "+" floor may sit before it is too stale.
FLOOR_TOLERANCE = 0.05

# Units whose published counts are always exact, "+" or not.
EXACT_UNITS = {"tools"}

# (unit, pattern). Each pattern captures the number and is anchored on the NOUN,
# so "13 guided prompts" and "a curated 14-tool manifest" are not counts we own.
PATTERNS: list[tuple[str, str]] = [
    ("facilities", r"([\d,]+)\+?\s*(?:global\s+)?data.?cent(?:er|re)\s+facilit\w*"),
    ("markets", r"([\d,]+)\+?\s*(?:US\s+|global\s+|power\s+)*markets\b"),
    # "2,000+ tracked data-center M&A transactions" sat in a tool description,
    # green, because "data-center" between "tracked" and "M&A" broke the match.
    ("deals", r"([\d,]+)\+?\s*(?:tracked\s+)?(?:data.?cent(?:er|re)\s+)?(?:M&A\s+)?(?:transactions|deals)\b"),
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
        got = {k: _canon_value(d[k])
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


def find_counts(prose: str) -> list[tuple[str, str, int, bool]]:
    """[(unit, matched_text, value, is_floor)] for every count-shaped phrase.

    is_floor is True when the number is published with a "+" directly after it.
    """
    out = []
    for unit, pat in PATTERNS:
        for m in re.finditer(pat, prose, re.I):
            raw = m.group(1).replace(",", "")
            if raw.isdigit():
                is_floor = prose[m.end(1):m.end(1) + 1] == "+"
                out.append((unit, m.group(0).strip(), int(raw), is_floor))
    return out


def check(prose: str, canon: dict) -> tuple[list[str], list[str]]:
    """(failures, warnings) under the floor rule in the module docstring."""
    bad, warn = [], []
    for unit, text, value, is_floor in find_counts(prose):
        want = canon.get(unit)
        if want is None:
            continue
        if want == WITHHELD:
            bad.append(f"{unit}: {text!r}: canon WITHHOLDS this count; "
                       f"publish no number")
            continue
        if unit in EXACT_UNITS or not is_floor:
            if value != want:
                bad.append(f"{unit}: {text!r} — canon is {want:,} (exact match required)")
        elif value > want:
            bad.append(f"{unit}: {text!r} — OVERCLAIM, canon is {want:,}+")
        elif value < want * (1 - FLOOR_TOLERANCE):
            bad.append(f"{unit}: {text!r} — too stale, more than "
                       f"{FLOOR_TOLERANCE:.0%} below canon {want:,}+")
        elif value < want:
            warn.append(f"{unit}: {text!r} — below canon {want:,}+ but within "
                        f"{FLOOR_TOLERANCE:.0%}; refresh it")
    return bad, warn


def lint(prose: str, canon: dict) -> list[str]:
    return check(prose, canon)[0]


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

    # Was "2,000+" against canon 2,100 — now inside FLOOR_TOLERANCE, so the
    # extraction is asserted with an overclaim instead.
    ok(any("deals" in v for v in lint(
        "Search 2,500+ tracked data-center M&A transactions.", canon)),
       "a 'data-center' qualifier before M&A does not hide the deal count")

    # ── Floor rule (owner decision 2026-09-26, FLOOR_TOLERANCE) ──
    bad_, warn_ = check(good.replace("20,500+", "19,500+"), canon)  # -4.9%
    ok(bad_ == [] and any("facilities" in w for w in warn_),
       "CONTROL: a floor inside tolerance passes, with a warning")
    bad_, warn_ = check(good.replace("20,500+", "19,400+"), canon)  # -5.4%
    ok(any("facilities" in v and "stale" in v for v in bad_),
       "a floor more than 5% below canon fails")
    ok(any("OVERCLAIM" in v for v in lint(good.replace("20,500+", "20,501+"), canon)),
       "a floor ONE above canon fails (overclaim has no tolerance)")
    ok(check(good, canon)[1] == [], "a floor equal to canon passes with no warning")
    ok(any("tools" in v for v in lint(good.replace("83 tools", "82 tools"), canon)),
       "tools stay EXACT: one below canon fails")
    ok(any("tools" in v for v in lint(good.replace("83 tools", "82+ tools"), canon)),
       "tools stay EXACT even when published with '+' (no floor tolerance)")
    ok(any("facilities" in v for v in lint(
        good.replace("20,500+ data", "20,000 data"), canon)),
       "a count published WITHOUT '+' stays exact")

    ok(lint("13 guided prompts and a curated 14-tool manifest", canon) == [],
       "prompt counts and the curated tool subset are not coverage claims")

    # ── Withheld counts (canon publishes a phrase, not a number) ──
    ok(_canon_value("corroborated count pending") == WITHHELD,
       "a non-numeric canon value reads as WITHHELD")
    ok(_canon_value("1,700+ ") == 1700 and _canon_value("300+") == 300
       and _canon_value(94) == 94,
       "numeric canon values parse (incl. a trailing space after '+')")
    held = {**canon, "facilities": WITHHELD}
    ok(any("facilities" in v and "WITHHOLDS" in v for v in lint(good, held)),
       "a published facility number fails when canon WITHHOLDS the count")
    ok(lint("Global facility map (corroborated count pending), 300+ power "
            "markets, 2,100+ tracked M&A deals. 83 tools.", held) == [],
       "CONTROL: the withheld phrase with no number is clean")

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
    bad, warn = check(prose, canon)
    for w in sorted(set(warn)):
        print(f"::warning::{w}")
    if bad:
        print("::error::Coverage numbers disagree with DC Hub canon "
              f"({provenance}: {canon}):")
        for b in sorted(set(bad)):
            print(f"  x {b}")
        print("\nRead the live values: " + CANON_URL)
        return 1
    print(f"OK — {len(found)} coverage number(s) within canon rule "
          f"(floor tolerance {FLOOR_TOLERANCE:.0%}, {provenance}): "
          + ", ".join(f"{u}={canon[u]:,}" if isinstance(canon[u], int)
                     else f"{u}={canon[u]}" for u in sorted(canon)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
