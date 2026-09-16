# GPRNK workspace

Two paths, for two different jobs.

| | `build_gprnk.py` | `rebuild_gprnk.py` |
|---|---|---|
| Input | co-authors' master `.claude/GPRNK(YYYYMM).xlsx` | BigKinds article counts |
| Does | reformats a finished index for publication | recomputes the index from scratch |
| Status | **in use** — produced the live release | stage 1: arithmetic done, unvalidated |
| Needs | a new master workbook | a BigKinds API key (paid since 2025) |

`build_gprnk.py` is the current update route: drop a new master in `.claude/`,
run it, bump the changelog row in `gprnk.html`. `rebuild_gprnk.py` exists so the
series can eventually be extended without waiting for a master.

## Published release

`data/gprnk/` — `GPRNK_monthly.csv`, `GPRNK_monthly.xlsx` (+ Notes sheet),
`gprnk-index.png`. Nine columns, 370 months, 1995-01 to 2025-10. CC BY 4.0,
cite Lee, Lee and Jung (2026) AEL. Page: `gprnk.html`.

Only the nine GPRNK columns are published. The master carries 186, including
third-party series (Caldara-Iacoviello country GPR, EPU/GEPU, KOSPI/KOSDAQ/Dow,
VKOSPI, FX) that are not ours to redistribute. `.gitignore` keeps masters out of
the repo; one was tracked from 6e2ec54 until it was removed from history on
2026-09-16.

---

## The recipe

From IMF WP 2021/251 §2.2 (`.claude/papers/IMF_WP_2021-251_GPRNK.pdf`), which is
far more explicit than the AEL letter. Recorded here so nobody has to re-read 36
pages.

### Sample — 18 outlets (fn. 9)

- **Dailies (10)**: 조선일보, 동아일보, 중앙일보, 경향신문, 국민일보, 문화일보, 서울신문, 세계일보, 한겨레, 한국일보
- **Business (5)**: 매일경제, 머니투데이, 서울경제, 한국경제, 헤럴드경제
- **Broadcast (3)**: KBS, MBC, SBS

68.9% of national newspaper circulation, 63.6% of national broadcast viewership
(fn. 18). Topics restricted to 정치·경제·국제. Search covers headline and/or body.

### Search terms (Table 1 Panel B)

Default keyword 북한 — also 北, 北韓, which papers use interchangeably (fn. 10).

| Category | Topic | Action/Status | Excluded |
|---|---|---|---|
| Military tensions | 핵, 미사일, 군사, 전쟁 | 위협, 긴장, 도발 | 평화 |
| Sanctions | 제재, 압박 | 반발, 불복, 비난 | — |
| Talks/agreements | 대화, 회담 | 재개, 합의, 협의 | 결렬, 무산, 거부 |
| Economic cooperation | 경제협력, 경협 | 추진, 기대 | 우려 |

Terms within a column are OR'd; columns are AND'd; excluded terms are NOT'd.
Negative = military tensions + sanctions. Positive = talks + economic cooperation.

### Arithmetic

```
X_it   = (N_neg,it − N_pos,it) / N_it            net negative share, outlet i, month t
X~_it  = ½ ( X_it + √(X_it² + 0.1) )             α = 0.1  (fn. 14)
Y_it   = X~_it / σ_i                             σ_i = SD of X~_i over 1995-01..2016-12
Y_t    = mean of Y_it across outlets present
GPRNK  = 100 · Y_t / Ȳ                           Ȳ = mean of Y_t over 1995–2016
```

The α transform is the step no summary mentions and without which nothing
reproduces. It is monotone and convex, asymptotic to y = x as x → +∞ and to zero
as x → −∞, so negative net shares compress toward zero instead of going negative.

### Checks the release passes

Verified against `data/gprnk/GPRNK_monthly.csv` on 2026-09-16:

| Paper says | Published data |
|---|---|
| corr(negative, military tensions) = 0.99 | 0.995 |
| corr(positive, talks) = 0.98 | 0.978 |
| corr(talks, 경협) = 0.43 | 0.435 |
| corr(GPRNK, GPRNK-raw) = 0.98 | 0.983 |
| all series mean 100 over 1995–2016 | exactly 100.00, all eight |

---

## Open problems for the reconstruction

**1. The underlying database moves.** Identical search terms, very different
counts between the two papers:

| | IMF (→2020) | AEL (→2024) | ratio |
|---|---|---|---|
| default 북한 | 1,039,297 | 1,441,420 | ×1.39 |
| military tensions | 124,328 | 229,361 | ×1.84 |
| sanctions | 24,637 | 45,642 | ×1.85 |
| talks | 124,824 | 250,639 | ×2.01 |
| economic cooperation | 16,774 | 40,601 | ×2.42 |

The period grew 16%; the categories grew 84–142%. Most likely BigKinds
backfilled outlets — it starts Chosun and Dong-a in 2018 and Joongang in 2008
(fn. 19). So today's query need not return what either paper saw. This is why
`verify` exists and why nothing gets published before it passes.

**2. Late-starting outlets have no σ.** Chosun and Dong-a begin in 2018, after
the base period has closed, so a 1995–2016 SD is undefined for them. The WP
reports *excluding* the three late papers as a robustness check (corr 0.98)
against a benchmark that includes them, which only works if they were
standardisable somehow. Unresolved. `MISSING_BASE_POLICY` makes the choice
explicit: `drop` (default), `own-window`, or `error`.

**3. The six secondary series are not documented.** The WP derives the headline
index only. The release also carries negative/positive components and four
subtopics; those are plain shares, already positive, so the α transform may or
may not apply. `SUBTOPIC_USES_TRANSFORM` is the switch; `verify` decides it.

**4. The API is paid** as of 2025, and its request shape is not public.
`BigKinds._request` is deliberately left unimplemented rather than guessed, so a
wrong request cannot masquerade as a data problem.

---

## Working through it

```
python rebuild_gprnk.py counts-template   # 6,660 empty rows, to see the shape
python rebuild_gprnk.py fetch             # BigKinds -> counts.csv   [needs a key]
python rebuild_gprnk.py build             # counts.csv -> rebuilt.csv
python rebuild_gprnk.py verify            # rebuilt vs published — the gate
python rebuild_gprnk.py freeze            # pin σ_i and Ȳ once verified
```

`fetch` checkpoints every 50 outlet-months and skips what `counts.csv` already
has, so it can be interrupted. Five counts per outlet-month, no article payloads
— a full rebuild is 370 × 18 × 5 ≈ 33,300 requests, monthly updates 90. If the
API can bucket by month or return hits per provider in one call, that drops a
lot.

Partial fills build fine; unfilled rows are skipped with a count.

**Freeze σ_i after validation.** Recomputing the base period every month would
silently revise published history — the thing a public index must never do.

Only after `verify` passes does automation make sense: a monthly Actions job that
fetches the new month, applies the frozen parameters, regenerates
`data/gprnk/`, and opens a **pull request**. Never an auto-merge; a wrong value
published quietly is the worst outcome here.

## Monthly update today (master workbook route)

1. Co-author drops a new `.claude/GPRNK(YYYYMM).xlsx`
2. `python .claude/gprnk-workspace/build_gprnk.py`
3. Add a changelog row to `gprnk.html`
4. Commit and push
