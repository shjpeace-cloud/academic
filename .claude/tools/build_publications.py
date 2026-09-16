"""
Bake data/publications.json into publications.html as static markup.

    python .claude/tools/build_publications.py            rewrite the block
    python .claude/tools/build_publications.py --check    exit 1 if it is stale

Why this exists
---------------
publications.html used to ship 21 words of HTML: a heading, a Scholar link and
the filter buttons. All 56 entries arrived later, from JS fetching the JSON.
People saw a normal page, but the first thing a crawler reads was an empty one,
and Google's JS rendering happens in a separate, slower queue -- a common reason
a page sits at "Crawled - currently not indexed".

research.html never had that problem because its cards are written into the HTML
and JS only decorates them. This does the same for publications, except there
are 56 entries, so they are generated rather than hand-written.

Nothing about how the page behaves changes. The JSON stays the single source of
truth; the script only mirrors the "All" view into the markup that ships. On
load, render('all') overwrites #pub-list with its own output, so the static
block is what search engines and JS-less readers get, and the live page is
byte-identical to before. If the fetch fails, the static block simply stays --
which is what a fallback is for.

The formatting here mirrors formatPub/buildLinks/renderSection in
publications.html. Change one and you must change the other; --check catches a
stale block but not a divergent formatter.

Run this after editing publications.json, before committing.
"""

import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "data" / "publications.json"
HTML_PATH = ROOT / "publications.html"

BEGIN = ("    <!-- BEGIN generated from data/publications.json by "
         ".claude/tools/build_publications.py — do not edit by hand -->")
END = "    <!-- END generated -->"

SECTION_LABELS = {
    "journal-en": "Peer-reviewed Articles (English)",
    "journal-kr": "Peer-reviewed Articles (Korean)",
    "commentary-en": "Commentaries &amp; Policy Briefs (English)",
    "commentary-kr": "Commentaries &amp; Policy Briefs (Korean)",
    "report-en": "Policy Reports (English)",
    "report-kr": "Policy Reports (Korean)",
    "working-paper": "Working Papers",
    "book": "Books &amp; Book Chapters",
    "book-review": "Book Reviews",
}

SECTION_ORDER = [
    "journal-en", "journal-kr", "commentary-en", "commentary-kr",
    "report-en", "report-kr", "working-paper", "book", "book-review",
]

# Own-name forms across the corpus, longest/most specific first.
SELF_NAMES = ["Jung, Seungho", "Jung, Seung-Ho", "Seungho Jung",
              "Seung-Ho Jung", "정승호"]

_BARE_AMP = re.compile(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)")


def attr(url: str) -> str:
    """A URL safe to drop in an href.

    The JS interpolates URLs raw, which browsers forgive; static markup that
    search engines parse should not rely on that. Bare ampersands only -- the
    JSON has no quotes or angle brackets in any field, and re-escaping an
    already-escaped entity would corrupt the link.
    """
    return _BARE_AMP.sub("&amp;", url).replace('"', "&quot;")


def text(s) -> str:
    return html.escape(str(s), quote=False) if s is not None else ""


def mark_corr(p: dict) -> str:
    """Asterisk on the author's own name; the note goes at the end of the entry."""
    authors = p["authors"]
    if not p.get("corresponding"):
        return text(authors)
    for name in SELF_NAMES:
        i = authors.find(name)
        if i != -1:
            cut = i + len(name)
            return text(authors[:cut]) + "*" + text(authors[cut:])
    return text(authors)


def year_str(p: dict) -> str:
    return f"{p['year']}.{p['month']}." if p.get("month") else f"{p['year']}."


def linked_title(p: dict) -> str:
    title = text(p["title"])
    if p.get("url"):
        return f'<a href="{attr(p["url"])}" target="_blank">{title}</a>'
    return title


def format_pub(p: dict) -> str:
    ys = year_str(p)

    if p["type"] == "book":
        line = f'{mark_corr(p)}. {ys} {linked_title(p)}.'
        if p.get("editor"):
            line += f' {text(p["editor"])},'
        if p.get("book"):
            line += f' <em>{text(p["book"])}</em>.'
        if p.get("publisher"):
            line += f' {text(p["publisher"])}.'
        if p.get("note"):
            line += f' ({text(p["note"])})'
        if p.get("corresponding"):
            line += ' <span class="pub-corr">*Corresponding author</span>'
        return line

    line = f'{mark_corr(p)}. {ys} "{linked_title(p)}"'
    if p.get("note"):
        line += f' {text(p["note"])}'
    line += "."

    if p.get("journal"):
        line += f' <em>{text(p["journal"])}</em>'

    if p.get("volume") and p.get("issue"):
        line += f', {text(p["volume"])}({text(p["issue"])})'
    elif p.get("volume"):
        line += f', {text(p["volume"])}'

    if p.get("pages"):
        line += f', {text(p["pages"])}'
    if p.get("year_label"):
        line += f' {text(p["year_label"])}'
    if p.get("publisher"):
        line += f', {text(p["publisher"])}'

    if p.get("doi"):
        doi = text(p["doi"])
        line += (f'. DOI: <a href="https://doi.org/{attr(p["doi"])}"'
                 f' target="_blank">{doi}</a>')

    line += "."
    if p.get("corresponding"):
        line += ' <span class="pub-corr">*Corresponding author</span>'
    return line


def build_links(p: dict) -> str:
    links = []
    if p.get("kr_url"):
        links.append(f'<a class="pub-link" href="{attr(p["kr_url"])}"'
                     f' target="_blank">Korean version (EAI)</a>')
    if p.get("extra_url"):
        label = text(p.get("extra_label") or "Link")
        links.append(f'<a class="pub-link" href="{attr(p["extra_url"])}"'
                     f' target="_blank">{label}</a>')
    return f'<div class="pub-links">{"".join(links)}</div>' if links else ""


def render(pubs: list) -> str:
    """The "All" view, matching the filter that is active on load."""
    out = [BEGIN]
    for kind in SECTION_ORDER:
        items = [p for p in pubs if p.get("type") == kind]
        if not items:
            continue
        out.append(f'    <div class="pub-section" data-type="{kind}">')
        out.append(f'      <div class="pub-section-title">'
                   f'{SECTION_LABELS[kind]}</div>')
        for p in items:
            out.append('      <div class="pub-item">')
            out.append(f"        {format_pub(p)}")
            links = build_links(p)
            if links:
                out.append(f"        {links}")
            out.append("      </div>")
        out.append("    </div>")
    out.append(END)
    return "\n".join(out)


def splice(page: str, block: str) -> str:
    """Put the block inside #pub-list, replacing any previous one."""
    if BEGIN in page:
        start = page.index(BEGIN)
        end = page.index(END) + len(END)
        return page[:start] + block + page[end:]

    # First run: the container is still the empty <div id="pub-list"></div>.
    anchor = '<div id="pub-list">'
    i = page.index(anchor)          # raises if the container is gone: loud, not silent
    rest = page[i + len(anchor):]
    if rest.lstrip()[:6] != "</div>":
        raise SystemExit(
            "#pub-list already has content but no generated markers; "
            "clear it by hand before running this")
    close = page.index("</div>", i + len(anchor))
    return page[:i] + anchor + "\n" + block + "\n  " + page[close:]


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if publications.html is out of date")
    args = ap.parse_args()

    pubs = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    page = HTML_PATH.read_text(encoding="utf-8")
    block = render(pubs)
    updated = splice(page, block)

    counted = sum(1 for p in pubs if p.get("type") in SECTION_ORDER)
    if counted != len(pubs):
        unknown = sorted({p.get("type") for p in pubs} - set(SECTION_ORDER))
        print(f"warning: {len(pubs) - counted} entries have a type not in "
              f"SECTION_ORDER and will not appear: {unknown}", file=sys.stderr)

    if args.check:
        if updated != page:
            print("publications.html is stale — run "
                  "`python .claude/tools/build_publications.py`", file=sys.stderr)
            return 1
        print(f"publications.html is up to date ({counted} entries)")
        return 0

    if updated == page:
        print(f"no change ({counted} entries)")
        return 0

    HTML_PATH.write_text(updated, encoding="utf-8")
    print(f"wrote {HTML_PATH.name}: {counted} entries in "
          f"{sum(1 for k in SECTION_ORDER if any(p.get('type') == k for p in pubs))}"
          f" sections")
    return 0


if __name__ == "__main__":
    sys.exit(main())
