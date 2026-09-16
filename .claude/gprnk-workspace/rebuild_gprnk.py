"""
Rebuild the GPRNK index from BigKinds article counts.

This is the independent-reconstruction path, as opposed to build_gprnk.py, which
just reformats the co-authors' finished master workbook for publication. Here we
go back to the counts and recompute the index, following IMF WP 2021/251 §2.2
(Jung, Lee and Lee, "The Impact of Geopolitical Risk on Stock Returns: Evidence
from Inter-Korea Geopolitics"). The point is to be able to extend the series
without waiting for a new master.

    python rebuild_gprnk.py counts-template   write an empty counts.csv to fill
    python rebuild_gprnk.py fetch             query BigKinds -> counts.csv  [needs a key]
    python rebuild_gprnk.py build             counts.csv -> rebuilt.csv
    python rebuild_gprnk.py verify            rebuilt.csv vs the published series
    python rebuild_gprnk.py freeze            store base-period parameters

Run `verify` before trusting anything this produces. The reconstruction is only
useful if it lands on top of the published 370 months; if it does not, the
difference has to be chased down rather than published.

What is documented and what is inferred
---------------------------------------
Documented in the WP, implemented here exactly: the outlet list (fn. 9), the
Korean search terms (Table 1 Panel B), the topic restriction, and every step of
the arithmetic including the alpha = 0.1 transform, which no summary of the
paper mentions and without which nothing reproduces.

Inferred, and flagged at the call site: how the six secondary series
(negative/positive components, four subtopics) are built. The WP gives the
formula for the headline index only. SUBTOPIC_USES_TRANSFORM below is the one
free choice; verify decides it.

A caution before spending money on API calls
--------------------------------------------
The two papers use identical search terms but report very different article
counts -- default 1,039,297 (to 2020) against 1,441,420 (to 2024), while the
four categories grow by 84-142% over a period extension of 16%. BigKinds
backfills outlets (fn. 19: Chosun and Dong-a start 2018, Joongang 2008), so the
database underneath is not fixed. Today's query need not return the counts
either paper saw, and that is what `verify` is for.
"""

import csv
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]              # …/academic
HERE = Path(__file__).resolve().parent
COUNTS = HERE / "counts.csv"
REBUILT = HERE / "rebuilt.csv"
PARAMS = HERE / "base_params.json"
PUBLISHED = ROOT / "data" / "gprnk" / "GPRNK_monthly.csv"

# ── Sample definition (IMF WP 2021/251 fn. 9) ────────────────────────────────

OUTLETS = [
    # Ten national daily newspapers
    ("조선일보", "daily"), ("동아일보", "daily"), ("중앙일보", "daily"),
    ("경향신문", "daily"), ("국민일보", "daily"), ("문화일보", "daily"),
    ("서울신문", "daily"), ("세계일보", "daily"), ("한겨레", "daily"),
    ("한국일보", "daily"),
    # Five business and economics dailies
    ("매일경제", "business"), ("머니투데이", "business"), ("서울경제", "business"),
    ("한국경제", "business"), ("헤럴드경제", "business"),
    # Three national broadcasters
    ("KBS", "broadcast"), ("MBC", "broadcast"), ("SBS", "broadcast"),
]

# Right- vs left-leaning split (fn. 20). Only used for the slant robustness
# check; the other eleven outlets are unclassified there.
RIGHT_LEANING = {"조선일보", "동아일보", "중앙일보", "국민일보", "문화일보"}
LEFT_LEANING = {"경향신문", "한겨레"}

# BigKinds topic filter: politics, economics, international relations.
TOPICS = ["정치", "경제", "국제"]

# ── Search terms (IMF WP 2021/251 Table 1 Panel B) ───────────────────────────
#
# An article counts for a category when it carries the default keyword AND one
# of the topic terms AND one of the action/status terms AND none of the
# excluded terms. Newspapers also write North Korea in hanja, so the default
# keyword carries those forms too (fn. 10).

DEFAULT_TERMS = ["북한", "北韓", "北"]

CATEGORIES = {
    "threat": {
        "sign": "neg",
        "topic": ["핵", "미사일", "군사", "전쟁"],
        "action": ["위협", "긴장", "도발"],
        "exclude": ["평화"],
    },
    "sanction": {
        "sign": "neg",
        "topic": ["제재", "압박"],
        "action": ["반발", "불복", "비난"],
        "exclude": [],
    },
    "talks": {
        "sign": "pos",
        "topic": ["대화", "회담"],
        "action": ["재개", "합의", "협의"],
        "exclude": ["결렬", "무산", "거부"],
    },
    "economic_cooperation": {
        "sign": "pos",
        "topic": ["경제협력", "경협"],
        "action": ["추진", "기대"],
        "exclude": ["우려"],
    },
}

NEGATIVE = [k for k, v in CATEGORIES.items() if v["sign"] == "neg"]
POSITIVE = [k for k, v in CATEGORIES.items() if v["sign"] == "pos"]
CATEGORY_KEYS = list(CATEGORIES)

BASE_FROM, BASE_TO = "1995-01", "2016-12"       # standardisation base period
ALPHA = 0.1                                      # WP fn. 14

# The WP derives the headline index only. The published release also carries
# negative/positive components and the four subtopics; those are shares rather
# than net shares, so they are already positive and the transform may or may not
# have been applied. Flip this and re-run `verify` to see which reproduces.
SUBTOPIC_USES_TRANSFORM = False

# Standardising by a 1995-2016 SD is undefined for an outlet BigKinds only
# starts carrying later -- Chosun and Dong-a begin in 2018, after the base
# period closes entirely (fn. 19). The WP does not say what it does with them.
# It reports excluding the three late papers as a *robustness check* against a
# benchmark that includes them, which only works if they were standardisable,
# so either the paper used a different window for them or BigKinds had already
# backfilled by then. That ambiguity is unresolved, so make the choice explicit:
#
#   "drop"        leave the outlet out of the average entirely (conservative)
#   "own-window"  standardise it on whatever months it does cover
#   "error"       refuse to build
#
# `verify` is what settles this. Try "drop" first.
MISSING_BASE_POLICY = "drop"


def query_string(category: str) -> str:
    """Render one category as a BigKinds boolean query.

    Kept in one place because the exact syntax is the thing most likely to need
    adjusting against the API docs issued with a key.
    """
    def any_of(terms):
        return "(" + " OR ".join(terms) + ")"

    spec = CATEGORIES[category]
    parts = [any_of(DEFAULT_TERMS), any_of(spec["topic"]), any_of(spec["action"])]
    q = " AND ".join(parts)
    if spec["exclude"]:
        q += " NOT " + any_of(spec["exclude"])
    return q


def default_query_string() -> str:
    return "(" + " OR ".join(DEFAULT_TERMS) + ")"


# ── The construction (WP §2.2) ───────────────────────────────────────────────

_warned = set()


def net_share(n_neg: float, n_pos: float, n_total: float) -> float:
    """X_it = (N_neg - N_pos) / N_total."""
    return (n_neg - n_pos) / n_total if n_total else float("nan")


def to_positive(x: float, alpha: float = ALPHA) -> float:
    """X~_it = ½(x + sqrt(x² + alpha)).

    Monotone and convex; asymptotic to y = x as x -> +inf and to zero as
    x -> -inf. alpha = 0.1 is the paper's choice (fn. 14). Skipping this step is
    the single most likely reason a reconstruction fails to match.
    """
    return 0.5 * (x + math.sqrt(x * x + alpha))


def base_sigma(series_by_month: dict):
    """sigma_i: within-outlet SD of X~ over the base period, or None.

    Population SD, matching the usual convention for a fixed base window. If a
    rebuild sits a hair off the published series everywhere, try the sample SD
    here before looking anywhere else.

    Returns None when the outlet has no usable base-period coverage; see
    MISSING_BASE_POLICY for what happens then.
    """
    vals = [v for m, v in sorted(series_by_month.items())
            if BASE_FROM <= m <= BASE_TO and not math.isnan(v)]
    if len(vals) < 2:
        return None
    return statistics.pstdev(vals)


def own_window_sigma(series_by_month: dict):
    """Fallback sigma over whatever window the outlet does cover."""
    vals = [v for v in series_by_month.values() if not math.isnan(v)]
    return statistics.pstdev(vals) if len(vals) >= 2 else None


def build_index(counts: dict, categories, use_transform=True) -> dict:
    """Counts -> one index series, normalised to mean 100 over the base period.

    `counts` is {(month, outlet): {"total": n, "threat": n, ...}}.
    `categories` picks the numerator: the four keys for the headline index (net
    of positives), or a subset for a component or subtopic series.

    Outlets missing in a month are simply absent from that month's average --
    BigKinds starts three of the papers late (fn. 19), so N varies over time.
    """
    months = sorted({m for m, _ in counts})
    outlets = sorted({o for _, o in counts})

    headline = set(categories) == set(CATEGORY_KEYS)

    # X~ per outlet per month
    transformed = {o: {} for o in outlets}
    for (month, outlet), c in counts.items():
        if headline:
            x = net_share(sum(c[k] for k in NEGATIVE),
                          sum(c[k] for k in POSITIVE), c["total"])
        else:
            x = (sum(c[k] for k in categories) / c["total"]) if c["total"] else float("nan")
        transformed[outlet][month] = to_positive(x) if use_transform else x

    sigmas, no_base = {}, []
    for outlet, series in transformed.items():
        if not series:
            continue
        sigma = base_sigma(series)
        if sigma is None:
            no_base.append(outlet)
            if MISSING_BASE_POLICY == "error":
                raise ValueError(
                    f"{outlet} has no base-period coverage ({BASE_FROM}..{BASE_TO}); "
                    "set MISSING_BASE_POLICY to 'drop' or 'own-window'")
            if MISSING_BASE_POLICY == "own-window":
                sigma = own_window_sigma(series)
        if sigma:
            sigmas[outlet] = sigma
    if no_base:
        # build_all calls this seven times; say it once.
        key = tuple(sorted(no_base))
        if key not in _warned:
            _warned.add(key)
            print(f"  note: no base-period coverage for {', '.join(key)}"
                  f" -> {MISSING_BASE_POLICY}")

    # Average the standardised series across whichever outlets exist that month
    y = {}
    for month in months:
        vals = [transformed[o][month] / sigmas[o]
                for o in outlets
                if month in transformed[o]
                and not math.isnan(transformed[o][month])
                and sigmas.get(o)]
        if vals:
            y[month] = sum(vals) / len(vals)

    base = [v for m, v in y.items() if BASE_FROM <= m <= BASE_TO]
    if not base:
        raise ValueError("no base-period months in the aggregate series")
    mean_base = sum(base) / len(base)
    return {m: 100.0 * v / mean_base for m, v in y.items()}


def build_all(counts: dict) -> list:
    """Every published column, in the published order."""
    series = {
        "gprnk": build_index(counts, CATEGORY_KEYS, use_transform=True),
        "gprnk_negative": build_index(counts, NEGATIVE, SUBTOPIC_USES_TRANSFORM),
        "gprnk_positive": build_index(counts, POSITIVE, SUBTOPIC_USES_TRANSFORM),
    }
    for key in CATEGORY_KEYS:
        series[key] = build_index(counts, [key], SUBTOPIC_USES_TRANSFORM)

    cols = ["gprnk", "gprnk_negative", "gprnk_positive"] + CATEGORY_KEYS
    months = sorted(series["gprnk"])
    return [[m + "-01"] + [round(series[c].get(m, float("nan")), 4) for c in cols]
            for m in months], cols


# ── Counts I/O ───────────────────────────────────────────────────────────────

COUNTS_HEADER = ["month", "outlet", "total"] + CATEGORY_KEYS


def read_counts(path: Path = COUNTS) -> dict:
    if not path.exists():
        raise SystemExit(f"no {path.name}; run `counts-template` or `fetch` first")
    out, blank, bad = {}, 0, 0
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fields = ["total"] + CATEGORY_KEYS
            if any((row.get(k) or "").strip() == "" for k in fields):
                blank += 1                      # an unfilled template row
                continue
            try:
                values = {k: float(row[k]) for k in fields}
            except ValueError:
                bad += 1
                continue
            out[(row["month"], row["outlet"])] = values
    if blank or bad:
        print(f"  read {len(out)} rows; skipped {blank} unfilled"
              + (f", {bad} unparseable" if bad else ""))
    if not out:
        raise SystemExit(f"{path.name} has no filled rows")
    return out


def write_counts(counts: dict, path: Path = COUNTS):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COUNTS_HEADER)
        for (month, outlet) in sorted(counts):
            c = counts[(month, outlet)]
            w.writerow([month, outlet, c["total"]] + [c[k] for k in CATEGORY_KEYS])


def months_between(start="1995-01", end=None) -> list:
    if end is None:
        end = published_months()[-1][:7]
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def cmd_counts_template():
    """An empty counts.csv, so the shape is obvious before any API call."""
    if COUNTS.exists():
        raise SystemExit(f"{COUNTS.name} already exists; not overwriting")
    with COUNTS.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COUNTS_HEADER)
        for month in months_between():
            for outlet, _ in OUTLETS:
                w.writerow([month, outlet, "", "", "", "", ""])
    print(f"wrote {COUNTS.relative_to(ROOT)}")
    print(f"  {len(months_between())} months x {len(OUTLETS)} outlets"
          f" = {len(months_between()) * len(OUTLETS)} rows to fill")
    print("  blank rows are skipped, so a partial fill still builds")


# ── BigKinds adapter ─────────────────────────────────────────────────────────

class BigKinds:
    """Article counts from the BigKinds Open API.

    DELIBERATELY UNFINISHED. The endpoint and parameter names are not public --
    they come with the key, and the API moved to paid access in 2025. Rather
    than guess a request shape and have it fail in a way that looks like a data
    problem, fill in `_request` from the docs you are issued. Everything the
    request has to express is already assembled for you:

        - query        : query_string(category) / default_query_string()
        - outlet       : one of OUTLETS, by name
        - month        : "YYYY-MM", i.e. the whole calendar month
        - topics       : TOPICS
        - search field : headline and/or body
        - wanted       : the TOTAL HIT COUNT only, never the articles

    That last point is what keeps this cheap: five counts per outlet-month, no
    article payloads, no pagination. If the API can bucket by month or return
    hits per provider in one call, use it -- a full rebuild is otherwise
    len(months) x 18 x 5 requests.
    """

    def __init__(self, access_key: str):
        self.access_key = access_key

    def _request(self, query: str, outlet: str, month: str) -> int:
        raise NotImplementedError(
            "fill in from the BigKinds API docs issued with your key; "
            "return the total hit count for this query/outlet/month"
        )

    def count(self, category, outlet, month) -> int:
        q = default_query_string() if category == "total" else query_string(category)
        return self._request(q, outlet, month)


def cmd_fetch(access_key=None):
    import os
    access_key = access_key or os.environ.get("BIGKINDS_API_KEY")
    if not access_key:
        raise SystemExit("set BIGKINDS_API_KEY, or pass the key as an argument")

    api = BigKinds(access_key)
    counts = read_counts() if COUNTS.exists() else {}
    todo = [(m, o) for m in months_between() for o, _ in OUTLETS
            if (m, o) not in counts]
    print(f"{len(todo)} outlet-months to fetch "
          f"({len(todo) * (len(CATEGORY_KEYS) + 1)} requests)")

    for i, (month, outlet) in enumerate(todo, 1):
        row = {"total": api.count("total", outlet, month)}
        for key in CATEGORY_KEYS:
            row[key] = api.count(key, outlet, month)
        counts[(month, outlet)] = row
        if i % 50 == 0:                      # checkpoint; the fetch is the slow part
            write_counts(counts)
            print(f"  {i}/{len(todo)}")
    write_counts(counts)
    print(f"wrote {COUNTS.relative_to(ROOT)}")


# ── Build / verify / freeze ──────────────────────────────────────────────────

def cmd_build():
    counts = read_counts()
    rows, cols = build_all(counts)
    with REBUILT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date"] + cols)
        w.writerows(rows)
    print(f"wrote {REBUILT.relative_to(ROOT)}  ({len(rows)} months, "
          f"{rows[0][0][:7]} to {rows[-1][0][:7]})")
    print("now run `verify`")


def published_months() -> list:
    with PUBLISHED.open(encoding="utf-8") as f:
        return [r["date"] for r in csv.DictReader(f)]


def _corr(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den else float("nan")


def cmd_verify():
    """Score the rebuild against the published series. This is the whole point."""
    if not REBUILT.exists():
        raise SystemExit("no rebuilt.csv; run `build` first")
    pub = {r["date"]: r for r in csv.DictReader(PUBLISHED.open(encoding="utf-8"))}
    reb = {r["date"]: r for r in csv.DictReader(REBUILT.open(encoding="utf-8"))}
    shared = sorted(set(pub) & set(reb))
    if not shared:
        raise SystemExit("no overlapping months")

    print(f"{len(shared)} overlapping months "
          f"({shared[0][:7]} to {shared[-1][:7]})\n")
    print(f"{'series':<22}{'corr':>8}{'mean|d|':>10}{'max|d|':>9}  worst month")
    print("-" * 70)

    ok = True
    for col in ["gprnk", "gprnk_negative", "gprnk_positive"] + CATEGORY_KEYS:
        if col not in reb[shared[0]]:
            continue
        a = [float(pub[m][col]) for m in shared]
        b = [float(reb[m][col]) for m in shared]
        diffs = [abs(x - y) for x, y in zip(a, b)]
        worst = shared[diffs.index(max(diffs))]
        r = _corr(a, b)
        print(f"{col:<22}{r:>8.4f}{statistics.mean(diffs):>10.3f}"
              f"{max(diffs):>9.3f}  {worst[:7]}")
        if col == "gprnk" and r < 0.99:
            ok = False

    print()
    if ok:
        print("Headline correlation >= 0.99. Compare the worst months by eye,")
        print("then `freeze` and wire up the monthly job.")
    else:
        print("Headline correlation below 0.99 -- do NOT publish this.")
        print("Check, in this order:")
        print("  1. the alpha = 0.1 transform (to_positive) is applied")
        print("  2. base_sigma uses population SD, and the 1995-01..2016-12 window")
        print("  3. the outlet set matches, including months where outlets are absent")
        print("  4. the topic filter (politics/economics/international) is applied")
        print("  5. the search covers headline AND body")
        print("  6. BigKinds has backfilled outlets since the paper was written")


def cmd_freeze():
    """Pin the base-period parameters so future months cannot move past values."""
    counts = read_counts()
    months = sorted({m for m, _ in counts})
    outlets = sorted({o for _, o in counts})
    transformed = {o: {} for o in outlets}
    for (month, outlet), c in counts.items():
        x = net_share(sum(c[k] for k in NEGATIVE),
                      sum(c[k] for k in POSITIVE), c["total"])
        transformed[outlet][month] = to_positive(x)
    sigmas = {}
    for outlet, series in transformed.items():
        sigma = base_sigma(series) if series else None
        if sigma is None and MISSING_BASE_POLICY == "own-window" and series:
            sigma = own_window_sigma(series)
        if sigma:
            sigmas[outlet] = sigma

    y = {}
    for month in months:
        vals = [transformed[o][month] / sigmas[o] for o in outlets
                if month in transformed[o] and sigmas.get(o)]
        if vals:
            y[month] = sum(vals) / len(vals)
    base = [v for m, v in y.items() if BASE_FROM <= m <= BASE_TO]

    PARAMS.write_text(json.dumps({
        "base_period": [BASE_FROM, BASE_TO],
        "alpha": ALPHA,
        "sigma_by_outlet": sigmas,
        "mean_y_base": sum(base) / len(base),
        "note": "Frozen so that adding a month cannot change published history. "
                "Recomputing these each month would silently revise the past.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {PARAMS.relative_to(ROOT)}")


COMMANDS = {
    "counts-template": cmd_counts_template,
    "fetch": cmd_fetch,
    "build": cmd_build,
    "verify": cmd_verify,
    "freeze": cmd_freeze,
}

if __name__ == "__main__":
    # Outlet names are Korean; the Windows console here defaults to cp949.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit(f"usage: {Path(__file__).name} "
                         f"[{' | '.join(COMMANDS)}]")
    COMMANDS[sys.argv[1]](*sys.argv[2:])
