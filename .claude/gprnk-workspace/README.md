# GPRNK data-release workspace (HOLD → bundled overhaul)

**Status**: on hold pending discussion with co-authors (Seohyun Lee, Jongmin Lee).
Do NOT publish anything from this folder to the live site until green-lit.

**Trigger for next action**: co-author approval of hosting + license + citation.

**Once triggered, execute as a single bundled overhaul** (user decision 2026-09-12):

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
