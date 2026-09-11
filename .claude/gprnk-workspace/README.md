# GPRNK data-release workspace (HOLD)

**Status**: on hold pending discussion with co-authors (Seohyun Lee, Jongmin Lee).
Do NOT publish anything from this folder to the live site until green-lit.

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
