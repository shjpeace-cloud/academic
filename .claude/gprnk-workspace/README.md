# GPRNK data-release workspace (RELEASED 2026-09-16)

**Status**: released. Co-authors (Seohyun Lee, Jongmin Lee) approved, and the bundled
overhaul below shipped in commit `bb3099f` — except item 1 (photo.jpg), which is still
missing from the repo.

**Live**: https://shjpeace-cloud.github.io/academic/gprnk.html

**Build**: `python .claude/gprnk-workspace/build_gprnk.py` regenerates
`data/gprnk/{GPRNK_monthly.csv, GPRNK_monthly.xlsx, gprnk-index.png}` from the newest
`.claude/GPRNK(YYYYMM).xlsx`. Those three files are build output — never hand-edit them.
`gprnk-monthly.csv` in this folder is the original 9-column draft, superseded by the
generated CSV.

**Open**: whether to `git rm --cached .claude/GPRNK(202510).xlsx` — the 186-column master
is still tracked in the public repo from an earlier session (the note below saying it is
gitignored was wrong). New masters are now blocked by `.gitignore: .claude/*.xlsx`.

**What shipped** (plan of 2026-09-12):

1. **Add photo.jpg** — currently missing (onerror hides), long-standing known issue
2. **Home page refactor**
   - Remove Research Interests 4-card grid (duplicate of Research page)
   - Add short bio paragraph (SEO-friendly, all 4 research pillars mentioned)
   - Add featured Figure 1-style GPRNK chart with caption → link to `data/gprnk.html`
   - Recent News stays
3. **Research page** — retains sole ownership of the 4-card grid (its raison d'être)
4. **GPRNK data page** — `data/gprnk.html` + `data/gprnk-monthly.csv` (this workspace's CSV, licensed CC BY 4.0, cite Lee-Lee-Jung 2026 AEL); navbar gets "Data" entry
5. **Chart generation** — Python/matplotlib PNG from `gprnk-monthly.csv`, styled after paper Figure 1 (event annotations for nuclear tests, ICBMs, summits, hostile-two-state)
6. **Recent News** — add "GPRNK index dataset now available (1995–2025)" item at top
7. **sitemap.xml + navbar** — new URL entry
8. All in a single coordinated commit series so the design lands as one visible change

## Files here

- `gprnk-monthly.csv` — cleaned 9-column public draft
  - Extracted from `.claude/GPRNK(202510).xlsx` (proprietary master, gitignored)
  - Columns: `date, gprnk, gprnk_negative, gprnk_positive, threat, sanction, talks, economic_cooperation, gprnk_raw`
  - Coverage: 1995-01 → 2025-10 (370 monthly obs)
  - `gprnk` = main index (Table 5 baseline, mean 100 over 1995–2016)
  - `gprnk_raw` = same index without negation-term exclusion (paper reports corr 0.98)

## Open decisions before release

1. Co-author consent (hosting, license, canonical citation)
2. Column scope (Minimal 1-col vs Full 8-col)
3. Page location (dedicated `data/gprnk.html` vs Research page section)

## Update workflow (once approved)

1. Co-author drops new `.claude/GPRNK(YYYYMM).xlsx` monthly
2. Re-run the extraction snippet in this folder
3. Overwrite `data/gprnk-monthly.csv` on the live site
4. Regenerate chart PNG (Figure 1 style, matplotlib)
5. Bump changelog entry on `data/gprnk.html`
6. auto-push
