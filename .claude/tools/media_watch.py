"""
Find news articles that mention Seungho Jung, for data/media.json.

    python .claude/tools/media_watch.py            search, write new candidates
    python .claude/tools/media_watch.py --all      also re-list candidates seen before

Sources
-------
- Google News RSS, Korean and English queries (no key needed).
- Naver News Search API, Korean only, when NAVER_CLIENT_ID and
  NAVER_CLIENT_SECRET are set (Windows user environment variables; read from
  the registry too, so a session started before they were set still sees them).
  Naver carries many regional and online outlets that Google News misses.

Filtering
---------
The name is common ("Seung-ho Jung" is mostly actors and footballers), so a hit
only counts when the article body itself contains the name AND the
affiliation: 정승호 + 인천대, or Jung + Incheon (Naver: checked in the
article body; Google: the query requires both, since its links cannot be
resolved to the publisher). Articles already in
data/media.json and ones seen on an earlier run are skipped.

Output
------
.claude/media_watch/candidates.md  (gitignored). Nothing is added to the site
automatically: the user picks what goes into media.json.
"""

import argparse
import datetime as dt
import email.utils
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "data" / "media.json"
OUT_DIR = ROOT / ".claude" / "media_watch"
SEEN = OUT_DIR / "seen.json"
CANDS = OUT_DIR / "candidates.md"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) media-watch"

# Every Google query carries both the name and the affiliation: Google News RSS
# links are opaque redirects that cannot be resolved to the publisher without a
# private endpoint, so for Google hits the query itself is the filter.
GOOGLE_QUERIES = [
    ('"정승호" 인천대', "ko"),
    ('"정승호" 인천대학교', "ko"),
    ('"정승호" 통일통합연구원', "ko"),
    ('"Seungho Jung" Incheon', "en"),
    ('"Jung Seung-ho" Incheon', "en"),
    ('"Seung-ho Jung" Incheon', "en"),
]
NAVER_QUERIES = ['"정승호" 인천대', '"정승호 교수" 북한', '정승호 통일통합연구원']

# body must contain one name form AND one affiliation form
NAME = re.compile(r"정승호|Seung-?ho Jung|Jung,? Seung-?ho|Seungho Jung", re.I)
AFFIL = re.compile(r"인천대|Incheon National|Incheon Nat", re.I)

# Title-level noise seen in practice: namesakes at other universities, and
# English sports pages (footballers/baseball players from Incheon clubs).
NAMESAKE = re.compile(r"정승호\s*\(?(?!인천)[가-힣]{1,6}대|(?<!인천)(?<![가-힣])[가-힣]{1,4}대\s+정승호")
EN_TOPIC = re.compile(r"Korea|Pyongyang|Kim Jong|unification|sanction|defector|econom", re.I)


def get(url: str, headers: dict | None = None, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        enc = r.headers.get_content_charset() or "utf-8"
    for e in (enc, "utf-8", "euc-kr", "cp949"):
        try:
            return raw.decode(e)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("utf-8", "replace")


def env(name: str) -> str | None:
    v = os.environ.get(name)
    if not v and sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                v = winreg.QueryValueEx(k, name)[0]
        except OSError:
            pass
    return v


def google(query: str, lang: str) -> list[dict]:
    hl = "ko&gl=KR&ceid=KR:ko" if lang == "ko" else "en-US&gl=US&ceid=US:en"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl={hl}"
    s = get(url)
    out = []
    for it in re.findall(r"<item>(.*?)</item>", s, re.S):
        title = html.unescape(re.search(r"<title>(.*?)</title>", it, re.S).group(1))
        link = re.search(r"<link>(.*?)</link>", it, re.S).group(1).strip()
        pub = re.search(r"<pubDate>(.*?)</pubDate>", it)
        src = re.search(r"<source[^>]*>(.*?)</source>", it, re.S)
        date = email.utils.parsedate_to_datetime(pub.group(1)).date().isoformat() if pub else ""
        out.append({"title": title, "url": link, "date": date,
                    "outlet": html.unescape(src.group(1)) if src else "", "via": "google"})
    return out


def naver(query: str, cid: str, secret: str) -> list[dict]:
    url = ("https://openapi.naver.com/v1/search/news.json?display=50&sort=date&query="
           + urllib.parse.quote(query))
    s = get(url, {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": secret})
    out = []
    for it in json.loads(s).get("items", []):
        title = html.unescape(re.sub(r"<[^>]+>", "", it["title"]))
        date = email.utils.parsedate_to_datetime(it["pubDate"]).date().isoformat()
        out.append({"title": title, "url": it.get("originallink") or it["link"],
                    "date": date, "outlet": "", "via": "naver"})
    return out


def resolve_google(url: str) -> str:
    """Google News RSS links are redirects; follow to the publisher when possible."""
    if "news.google.com" not in url:
        return url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            final = r.geturl()
            if "news.google.com" not in final:
                return final
            body = r.read().decode("utf-8", "replace")
        m = re.search(r'data-n-au="([^"]+)"', body) or re.search(
            r'<a[^>]+href="(https?://(?!news\.google)[^"]+)"', body)
        return html.unescape(m.group(1)) if m else url
    except Exception:
        return url


def body_text(url: str) -> str:
    s = get(url)
    s = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", " ", s)
    # News1 and others ship the body as JSON inside a script; keep raw text too
    return html.unescape(re.sub(r"<[^>]+>", " ", s)) + " " + s


def snippet(text: str) -> str:
    t = re.sub(r"\s+", " ", text)
    m = NAME.search(t)
    return t[max(0, m.start() - 80): m.start() + 180].strip() if m else ""


def norm_title(t: str) -> str:
    t = re.sub(r"\s+-\s+[^-]+$", "", t)      # Google appends " - Outlet"
    return re.sub(r"\W", "", t)[:30]


def norm(url: str) -> str:
    u = urllib.parse.urlsplit(url)
    q = "&".join(p for p in u.query.split("&") if p and not p.startswith(("input=", "utm_", "si=")))
    return f"{u.netloc.lower().removeprefix('www.')}{u.path.rstrip('/')}?{q}"


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--all", action="store_true", help="re-check items seen before")
    a = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    media = json.loads(MEDIA.read_text(encoding="utf-8"))
    known = {norm(m["url"]) for m in media}
    known_titles = {norm_title(m["title"]) for m in media}
    seen = json.loads(SEEN.read_text(encoding="utf-8")) if SEEN.exists() else {}

    hits = []
    for q, lang in GOOGLE_QUERIES:
        try:
            hits += google(q, lang)
        except Exception as e:
            print(f"google {q!r}: {e}", file=sys.stderr)
    cid, secret = env("NAVER_CLIENT_ID"), env("NAVER_CLIENT_SECRET")
    if cid and secret:
        for q in NAVER_QUERIES:
            try:
                hits += naver(q, cid, secret)
            except Exception as e:
                print(f"naver {q!r}: {e}", file=sys.stderr)
    else:
        print("naver: NAVER_CLIENT_ID/SECRET not set — Google News only", file=sys.stderr)

    new, checked = [], 0
    by_title = {}
    for h in hits:                                   # same story from several queries
        by_title.setdefault(re.sub(r"\W", "", h["title"])[:40], h)
    for h in by_title.values():
        key = re.sub(r"\W", "", h["title"])[:40]
        if key in seen and not a.all:
            continue
        bare = re.sub(r"\s+-\s+[^-]+$", "", h["title"])   # drop " - Outlet"
        lang_en = not re.search(r"[가-힣]", bare)
        if NAMESAKE.search(h["title"]) or (lang_en and not EN_TOPIC.search(h["title"])):
            seen[key] = {"status": "noise", "title": h["title"]}
            continue
        url = resolve_google(h["url"])
        if norm(url) in known or any(norm_title(h["title"]) == t for t in known_titles):
            seen[key] = {"status": "in-media", "url": url}
            continue
        checked += 1
        if "news.google.com" in url:          # unresolvable: trust the query
            seen[key] = {"status": "google-query", "url": url, "title": h["title"], "date": h["date"]}
            new.append({**h, "url": url, "snippet": "", "ok": True, "unverified": True})
            continue
        try:
            txt = body_text(url)
            ok = bool(NAME.search(txt) and AFFIL.search(txt))
            snip = snippet(txt) if ok else ""
        except Exception as e:
            ok, snip = None, f"(본문 열기 실패: {e})"
        seen[key] = {"status": "match" if ok else ("error" if ok is None else "no-match"),
                     "url": url, "title": h["title"], "date": h["date"]}
        if ok or ok is None:
            new.append({**h, "url": url, "snippet": snip, "ok": ok})

    SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=1), encoding="utf-8")
    new.sort(key=lambda x: x["date"], reverse=True)
    stamp = dt.date.today().isoformat()
    lines = [f"\n## {stamp} — 새 후보 {sum(1 for n in new if n['ok'])}건"
             f" (확인 {checked}건, 본문 못 연 것 {sum(1 for n in new if n['ok'] is None)}건)\n"]
    for n in new:
        mark = (" (Google 검색 일치, 본문 미확인)" if n.get("unverified")
                else "" if n["ok"] else " ⚠️본문 확인 못 함")
        lines.append(f"- {n['date']} {n['outlet']} [{n['title']}]({n['url']}) ({n['via']}){mark}")
        if n["snippet"]:
            lines.append(f"  > {n['snippet']}")
    with CANDS.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"-> {CANDS}")


if __name__ == "__main__":
    main()
