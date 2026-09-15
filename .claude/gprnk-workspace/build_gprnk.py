"""
Build the public GPRNK data release from the co-authors' master workbook.

    python .claude/gprnk-workspace/build_gprnk.py

Reads  : .claude/GPRNK(YYYYMM).xlsx   (master, 186 columns — NOT published)
Writes : data/gprnk/GPRNK_monthly.csv   9 public columns
         data/gprnk/GPRNK_monthly.xlsx  same, + a Notes sheet
         data/gprnk/gprnk-index.png     Figure 1-style chart for the site

Only the nine GPRNK columns are published. The master also carries third-party
series (Caldara-Iacoviello country GPR, EPU/GEPU, KOSPI/KOSDAQ/Dow returns,
VKOSPI, FX) and regression scratch columns; redistributing those is not ours to
do, so they stop here.

Monthly update: drop the new master in .claude/, re-run this script, then bump
the changelog row in gprnk.html.
"""

import csv
import datetime as dt
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import openpyxl
from openpyxl.styles import Font

ROOT = Path(__file__).resolve().parents[2]          # …/academic
OUT = ROOT / "data" / "gprnk"

# master column  ->  published column
COLUMNS = [
    ("GPRNK", "gprnk"),
    ("GPRNK_NEG", "gprnk_negative"),
    ("GPRNK_POS", "gprnk_positive"),
    ("adjthr_index", "threat"),
    ("sanc_index", "sanction"),
    ("adjtalk_index", "talks"),
    ("adjecoop_index", "economic_cooperation"),
    ("GPRNK_broad", "gprnk_raw"),
]

DEFINITIONS = [
    ("date", "Month (first day of month, YYYY-MM-DD)."),
    ("gprnk", "GPRNK index. Net negative news share, standardised within outlet "
              "over 1995-2016, averaged across outlets, normalised to mean 100 "
              "over 1995-2016."),
    ("gprnk_negative", "Negative component (military tensions + sanctions)."),
    ("gprnk_positive", "Positive component (talks/agreements + economic cooperation)."),
    ("threat", "Subtopic index: military tensions."),
    ("sanction", "Subtopic index: sanctions."),
    ("talks", "Subtopic index: talks and agreements."),
    ("economic_cooperation", "Subtopic index: inter-Korean economic cooperation."),
    ("gprnk_raw", "GPRNK-raw: same searches without excluding negation terms "
                  "(correlation with GPRNK: 0.98)."),
]

CITATION = ('Lee, Jongmin, Seohyun Lee, and Seungho Jung (2026), "Corporate '
            'Investment Under North Korea Threats", Applied Economics Letters, '
            "1-8. https://doi.org/10.1080/13504851.2026.2731151")
LICENSE = "CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)"

# Events annotated on the figure. Each is placed at the month it occurred;
# `side` puts the label above a spike or below a trough, and `dx` nudges a
# label sideways where two annotations would otherwise crowd each other.
EVENTS = [
    ("2000-06", "1st inter-Korean\nsummit", "below", 0),
    ("2006-10", "1st nuclear test", "above", 0),
    ("2007-10", "2nd inter-Korean\nsummit", "below", 0),
    ("2010-11", "Yeonpyeong\nshelling", "above", 0),
    ("2013-03", "3rd nuclear test", "above", 0),
    ("2016-09", "5th nuclear test", "above", -14),
    ("2017-08", '"Fire and fury";\nICBM tests', "above", 0),
    ("2018-04", "Panmunjom &\nSingapore summits", "below", 0),
    ("2022-10", "Record missile\nbarrage", "above", -30),
    ("2023-12", '"Two hostile\nstates"', "above", 34),
]

INK = "#1c1c1c"
MUTED = "#898781"
GRID = "#e1e0d9"
LINE = "#1a3a5c"
BASE = "#c3c2b7"


def latest_master() -> Path:
    cands = sorted(
        p for p in (ROOT / ".claude").glob("GPRNK(*).xlsx")
        if re.fullmatch(r"GPRNK\(\d{6}\)\.xlsx", p.name)
    )
    if not cands:
        raise SystemExit("no .claude/GPRNK(YYYYMM).xlsx master found")
    return cands[-1]


def read_master(path: Path):
    ws = openpyxl.load_workbook(path, data_only=True).active
    head = [c.value for c in ws[1]]
    pos = {src: head.index(src) for src, _ in COLUMNS}
    ym = head.index("month")
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[pos["GPRNK"]] is None:          # trailing months not yet computed
            continue
        stamp = str(int(r[ym]))
        rows.append(
            [f"{stamp[:4]}-{stamp[4:]}-01"]
            + [round(float(r[pos[src]]), 4) for src, _ in COLUMNS]
        )
    rows.sort(key=lambda x: x[0])
    return rows


def write_csv(rows, path: Path):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date"] + [pub for _, pub in COLUMNS])
        w.writerows(rows)


def write_xlsx(rows, path: Path, coverage: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "GPRNK"
    header = ["date"] + [pub for _, pub in COLUMNS]
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for row in rows:
        ws.append(row)
    ws.freeze_panes = "B2"
    ws.column_dimensions["A"].width = 12
    for col in "BCDEFGHI":
        ws.column_dimensions[col].width = 20

    notes = wb.create_sheet("Notes")
    for line in [
        ["GPRNK - Geopolitical Risk Index for North Korea"],
        [f"Coverage: {coverage} (monthly)"],
        [f"Generated: {dt.date.today().isoformat()}"],
        [],
        ["Source", "Monthly news article counts from 18 South Korean newspapers "
                   "and broadcasters via BigKinds (Korea Press Foundation)."],
        ["Citation", CITATION],
        ["License", LICENSE],
        ["Page", "https://shjpeace-cloud.github.io/academic/gprnk.html"],
        [],
        ["Column", "Definition"],
        *[list(d) for d in DEFINITIONS],
    ]:
        notes.append(line)
    notes["A1"].font = Font(bold=True)
    notes["A10"].font = Font(bold=True)
    notes["B10"].font = Font(bold=True)
    notes.column_dimensions["A"].width = 22
    notes.column_dimensions["B"].width = 100
    for r in notes.iter_rows(min_col=2, max_col=2):
        for c in r:
            c.alignment = c.alignment.copy(wrap_text=True)
    wb.save(path)


def draw(rows, path: Path):
    xs = [dt.date.fromisoformat(r[0]) for r in rows]
    ys = [r[1] for r in rows]
    by_month = {r[0][:7]: r[1] for r in rows}

    fig, ax = plt.subplots(figsize=(9.2, 4.1), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    # Reference line at the base-period mean; the y-axis label names it, so it
    # carries no callout of its own.
    ax.axhline(100, color=BASE, lw=0.9, zorder=1)

    ax.plot(xs, ys, color=LINE, lw=1.3, zorder=3, solid_capstyle="round")

    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(BASE)
    ax.spines["bottom"].set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=8, length=0)
    ax.xaxis.set_major_locator(matplotlib.dates.YearLocator(5))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.set_ylim(0, max(ys) * 1.28)
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylabel("Index (1995–2016 mean = 100)", color=MUTED, fontsize=8)

    for month, label, side, dx in EVENTS:
        if month not in by_month:
            continue
        x = dt.date.fromisoformat(month + "-01")
        y = by_month[month]
        ax.plot([x], [y], "o", ms=3.4, color=LINE, mec="#ffffff", mew=1.2, zorder=4)
        dy, va = (14, "bottom") if side == "above" else (-14, "top")
        ax.annotate(
            label, xy=(x, y), xytext=(dx, dy), textcoords="offset points",
            ha="center", va=va, fontsize=7.2, color="#52514e", linespacing=1.25,
            arrowprops=dict(arrowstyle="-", color=BASE, lw=0.7,
                            shrinkA=1, shrinkB=3),
        )

    fig.tight_layout(pad=0.6)
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    master = latest_master()
    rows = read_master(master)
    coverage = f"{rows[0][0][:7]} to {rows[-1][0][:7]}"
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(rows, OUT / "GPRNK_monthly.csv")
    write_xlsx(rows, OUT / "GPRNK_monthly.xlsx", coverage)
    draw(rows, OUT / "gprnk-index.png")
    print(f"master   : {master.name}")
    print(f"rows     : {len(rows)}  ({coverage})")
    print(f"latest   : {rows[-1][0]}  gprnk={rows[-1][1]}")
    print(f"written  : {OUT.relative_to(ROOT)}/"
          "{GPRNK_monthly.csv, GPRNK_monthly.xlsx, gprnk-index.png}")


if __name__ == "__main__":
    main()
