"""
Generate the one-page CV as .docx, for export to the PDF the site links.

    python .claude/tools/build_cv.py            write the .docx
    python .claude/tools/build_cv.py --check    is the published PDF stale?

Writes .claude/cv/CV_Seung-Ho_JUNG(YYYYMMDD).docx. Convert it to PDF with Word
(the accompanying PowerShell one-liner, or File > Save as PDF), drop the PDF in
data/, and point cv.html at it -- see CLAUDE.md work rule 5.

Keeping it current
------------------
--check reads the PDF cv.html actually links, pulls its text, and compares it
against what the CV should say today. It reports two things:

  stale       a selected entry's details are not in the published PDF -- an
              article moved from forthcoming to paginated, a DOI landed, a
              constant below changed. Exits 1.
  candidates  English journal articles in publications.json that are not in
              SELECTED. Informational only: which publications belong on a CV
              is a judgement, not a rule. The current six are not the six most
              recent, so no recency rule would reproduce them -- deciding is
              the author's, and this only makes sure the decision gets asked.

The Stop hook runs --check whenever publications.json or this file changes, so
a new SSCI article cannot quietly leave the CV behind.

What is NOT automatic: the PDF itself. ExportAsFixedFormat needs Word, which
lives on this machine and not in CI, so no GitHub Action can produce it. And a
career change -- a promotion, a move, a new degree -- is not derivable from any
data file; those are the constants below, and they need a human to say so.
--check cannot detect a promotion, only remind you that this block exists.

The previous PDF was hand-made and printed from Word, so it drifted: it still
sent readers to the old Google Sites, carried no ORCID, listed the Asian
Perspective article as forthcoming a year after it appeared, and predated the
Applied Economics Letters paper entirely.

Selected Publications are pulled from data/publications.json by id, so volumes,
pages and DOIs stay correct on their own; SELECTED below is the only editorial
choice. Everything else that is not derivable from the site -- the address,
the teaching list -- sits in the constants here.

Teaching is kept as the earlier PDF had it, not narrowed to the four courses
currently on teaching.html: a CV lists what you have taught, and dropping the
rest would lose information the site never carried.
"""

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.shared import Pt, Inches, RGBColor

ROOT = Path(__file__).resolve().parents[2]
PUBS = ROOT / "data" / "publications.json"
OUTDIR = ROOT / ".claude" / "cv"

NAME = "SEUNG-HO JUNG"
ADDRESS = [
    "Building 14C, office 327",
    "119, Academy-ro, Yeonsu-gu, Incheon, 22012, KOREA",
]
SITE = "https://shjpeace-cloud.github.io/academic/"
ORCID = "0000-0001-7699-3158"
TEL = "(82)-32-835-8726"
EMAILS = "shjung@inu.ac.kr, shjpeace@gmail.com"

EXPERIENCE = [
    ("Assistant / Associate Professor, School of Northeast Asian Studies, "
     "Incheon National University", "2019~Present"),
    ("Economist, Economic Research Institute, Bank of Korea", "2014~2019"),
    ("Researcher, Korea Institute for International Economic Policy", "2005~2007"),
]

EDUCATION = [
    ("Ph.D. in Economics, Seoul National University", "2014",
     "Dissertation: “North Korea’s Trade with China: Aggregate and "
     "Firm-Level Analysis”"),
    ("Master of Public Policy, KDI School of Public Policy and Management", "2003",
     "Concentration in Transition and Development Studies"),
    ("Bachelor of Agriculture, Korea University", "2001", None),
]

# University President's commendations, grouped by award. Source: INU award
# record (포상사항 export, 2026-09-17). Years are the years each award
# recognises, not the years it was given (2022, 2023, 2025 / 2025).
AWARDS = [
    "Research Excellence Award, Incheon National University (2021, 2022, 2024)",
    "Excellent Teaching Award, Incheon National University (Fall 2024)",
]

INTERESTS = ("North Korean economy; North Korean foreign economic relations, "
             "particularly with China and Russia; unification and economic "
             "integration; economic adaptation of North Korean refugees")

# publications.json ids, in the order they should appear.
SELECTED = [56, 48, 37, 38, 24, 21]

# Trailing note for an entry, where the entry needs one.
PUB_NOTES = {
    21: "GPRNK index available at policyuncertainty.com/korea_gpr and at "
        "shjpeace-cloud.github.io/academic/gprnk.html",
}

# Public datasets, one bullet each. The check below looks for each page name,
# so a dataset added here flags the published PDF as stale until it is rebuilt.
DATA_RELEASES = [
    ("GPRNK — Geopolitical Risk Index for North Korea. Monthly, 1995–present. "
     "Free download at shjpeace-cloud.github.io/academic/gprnk.html"),
    ("North Korean Marketization Index — price liberalization, privatization and "
     "financial development, five periods to 2020, rebuilt from public survey data. "
     "Free download at shjpeace-cloud.github.io/academic/marketization.html"),
]

TEACHING = [
    "Understanding North Korea’s Economic System and Transition",
    "Development Economics, Economic Growth of South Korea",
    "Principles of Economics, Statistics for Economics, Econometrics, Time Series Analysis",
]

RIGHT_TAB = Inches(6.5)


def en(s):
    """Normalise hyphens in page ranges to en dashes."""
    return s.replace("-", "–") if s else s


def cite(p: dict) -> str:
    """One Selected-Publications line. Mirrors how cv.html renders these."""
    authors = p["authors"]
    if p.get("corresponding"):
        for n in ("Jung, Seungho", "Seungho Jung"):
            i = authors.find(n)
            if i != -1:
                authors = authors[:i + len(n)] + "*" + authors[i + len(n):]
                break

    line = f'{authors}. {p["year"]}. “{p["title"]}.” {p["journal"]}'
    if p.get("volume") and p.get("issue"):
        line += f', {p["volume"]}({p["issue"]})'
    elif p.get("volume"):
        line += f', {p["volume"]}'
    elif p.get("note"):
        line += f', {p["note"]}'
    if p.get("pages"):
        line += f', {en(p["pages"])}'
    line += "."
    if p.get("corresponding"):
        line += " *Corresponding author."
    if PUB_NOTES.get(p["id"]):
        line += f' ({PUB_NOTES[p["id"]]})'
    return line


def setup(doc):
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Inches(0.6)
        section.left_margin = section.right_margin = Inches(0.9)
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)
    pf = style.paragraph_format
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0


def para(doc, text="", *, size=10, bold=False, italic=False, space_before=0,
         space_after=0, indent=0.0, hanging=None, align=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    if indent:
        pf.left_indent = Inches(indent)
    if hanging:
        pf.first_line_indent = Inches(-hanging)
    if align is not None:
        p.alignment = align
    if text:
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        r.font.size = Pt(size)
    return p


def heading(doc, text):
    p = para(doc, text, size=11, bold=True, space_before=9, space_after=2)
    pbdr = p.paragraph_format
    pbdr.keep_with_next = True
    # A rule under the heading, the way the previous CV separated sections.
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    pPr = p._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:color"), "808080")
    bottom.set(qn("w:space"), "1")
    borders.append(bottom)
    pPr.append(borders)
    return p


def dated(doc, left, right, *, indent=0.18):
    """A line with the entry on the left and its years flush right."""
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(0)
    pf.left_indent = Inches(indent)
    pf.tab_stops.add_tab_stop(RIGHT_TAB, WD_TAB_ALIGNMENT.RIGHT)
    p.add_run(left)
    p.add_run("\t" + right)
    return p


def bullet(doc, text, *, indent=0.36):
    para(doc, "•  " + text, indent=indent, hanging=0.18, space_before=2)


def build(doc, pubs):
    setup(doc)

    para(doc, NAME, size=17, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER,
         space_after=2)
    contact = " · ".join(ADDRESS)
    para(doc, contact, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, f"Tel: {TEL} · {EMAILS}", size=9,
         align=WD_ALIGN_PARAGRAPH.CENTER)
    para(doc, f"{SITE} · ORCID: {ORCID}", size=9,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)

    heading(doc, "Professional Experience")
    for what, when in EXPERIENCE:
        dated(doc, what, when)

    heading(doc, "Education")
    for what, when, sub in EDUCATION:
        dated(doc, what, when)
        if sub:
            para(doc, sub, size=9, indent=0.36)

    heading(doc, "Research Interests")
    bullet(doc, INTERESTS)

    heading(doc, "Selected Publications")
    by_id = {p["id"]: p for p in pubs}
    missing = [i for i in SELECTED if i not in by_id]
    if missing:
        raise SystemExit(f"ids not in publications.json: {missing}")
    for i in SELECTED:
        bullet(doc, cite(by_id[i]))

    heading(doc, "Data")
    for release in DATA_RELEASES:
        bullet(doc, release)

    heading(doc, "Teaching")
    for course in TEACHING:
        para(doc, course, indent=0.36, space_before=2)

    heading(doc, "Honors and Awards")
    for award in AWARDS:
        para(doc, award, indent=0.36, space_before=2)


# Dash and quote variants that mean the same thing to a reader but not to
# a string comparison. The previous CV wrote a page range with a fullwidth
# dash, which is a formatting difference, not a stale entry.
_FOLD = str.maketrans({
    "–": "-", "—": "-", "‒": "-", "‑": "-",
    "−": "-", "－": "-", "〜": "~", "～": "~",
    "“": '"', "”": '"', "‘": "'", "’": "'",
})


def squash(s: str) -> str:
    """Whitespace-free, dash-folded lowercase, for matching PDF text.

    Extraction sprays spaces through words ("COVID -19", "shjpeace-\\ncloud"),
    so any comparison that respects spacing produces false alarms.
    """
    return "".join(s.translate(_FOLD).split()).lower()


def published_pdf() -> Path:
    """The PDF cv.html links, so the check follows the site rather than a guess."""
    page = (ROOT / "cv.html").read_text(encoding="utf-8")
    m = re.search(r'href="(data/CV_[^"]+\.pdf)"', page)
    if not m:
        raise SystemExit("no CV link found in cv.html")
    return ROOT / unquote(m.group(1))


def check(pubs) -> int:
    try:
        from pypdf import PdfReader
    except ImportError:
        print("check needs pypdf (pip install pypdf)", file=sys.stderr)
        return 0                               # never block on a missing dep

    pdf = published_pdf()
    if not pdf.exists():
        print(f"cv.html links {pdf.name}, which is missing", file=sys.stderr)
        return 1

    text = squash("".join(pg.extract_text() or ""
                          for pg in PdfReader(str(pdf)).pages))
    by_id = {p["id"]: p for p in pubs}

    stale = []
    for i in SELECTED:
        p = by_id.get(i)
        if p is None:
            stale.append(f"id {i} is in SELECTED but not in publications.json")
            continue
        # Distinctive, and exactly the things that change after acceptance.
        probes = [("title", p["title"][:44])]
        if p.get("volume"):
            probes.append(("volume", str(p["volume"])))
        for what, probe in probes:
            if squash(probe) not in text:
                stale.append(f'id {i} {what} "{probe}" is not in the PDF'
                             f' — {p["title"][:52]}')

        # Page ranges get written with every separator there is (en dash,
        # tilde, fullwidth dash), so match the numbers and ignore what joins
        # them -- the point is whether the article is still unpaginated.
        if p.get("pages"):
            nums = re.findall(r"\d+", p["pages"])
            if nums and not re.search(r"[^0-9]{0,3}".join(nums), text):
                stale.append(f'id {i} pages "{p["pages"]}" are not in the PDF'
                             f' — {p["title"][:52]}')

    # Career facts live in the constants, not in any data file; the most a
    # check can do is notice the PDF no longer says what they say.
    facts = [("site", SITE.rstrip("/")), ("ORCID", ORCID),
             ("position", EXPERIENCE[0][0][:40])]
    facts += [("data", re.search(r"academic/(\S+\.html)", d).group(1))
              for d in DATA_RELEASES]
    for label, value in facts:
        if squash(value) not in text:
            stale.append(f"{label} in the PDF differs from the constants here")

    english = [p for p in pubs if p["type"] == "journal-en"
               and p["id"] not in SELECTED]
    english.sort(key=lambda p: (-p["year"], -p["id"]))

    print(f"CV check against {pdf.name}")
    if stale:
        print(f"  STALE ({len(stale)}):")
        for line in stale:
            print(f"    {line}")
        print("    -> rebuild: python .claude/tools/build_cv.py, export with "
              "Word, update cv.html")
    else:
        print(f"  up to date ({len(SELECTED)} selected entries verified)")

    if english:
        print(f"  not in Selected Publications ({len(english)} English "
              f"journal articles) — include any?")
        for p in english[:6]:
            print(f"    id {p['id']:>3}  {p['year']}  {p['journal'][:32]:<32} "
                  f"{p['title'][:44]}")
        if len(english) > 6:
            print(f"    ... and {len(english) - 6} older")

    return 1 if stale else 0


def main():
    # This prints dashes and quotation marks, and the Windows console defaults
    # to cp949 here, which cannot encode them.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="report whether the published PDF is out of date")
    args = ap.parse_args()

    pubs = json.loads(PUBS.read_text(encoding="utf-8"))
    if args.check:
        return check(pubs)

    doc = Document()
    build(doc, pubs)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().strftime("%Y%m%d")
    out = OUTDIR / f"CV_Seung-Ho_JUNG({stamp}).docx"
    doc.save(out)
    print(f"wrote {out.relative_to(ROOT)}")
    print("convert with Word, then put the PDF in data/ and update cv.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
