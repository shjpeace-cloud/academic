# Seungho Jung — Academic Website 개발 인수인계 프롬프트

## 프로젝트 개요

정승호(Seungho Jung) 교수 — 인천대학교 동북아국제통상물류학부(School of Northeast Asian Studies, IBE) 부교수의 개인 학술 홈페이지.

**GitHub repo (진실의 위치, Source of Truth)**: `shjpeace-cloud/academic`
**Live site**: `https://shjpeace-cloud.github.io/academic/`
**배포 방식**: 정적 사이트 (HTML/CSS/JS + JSON 데이터). GitHub Pages가 main 브랜치 root에서 자동 배포.
**Host-level redirect**: `shjpeace-cloud/shjpeace-cloud.github.io` (별도 user-page repo)가 `/academic/`로 meta-refresh redirect — Naver host 단위 등록 우회용.

---

## ⚠️ Working directory — Primary clone (모든 Claude 세션이 검증할 것)

**올바른 위치**: `C:\Users\shjpe\OneDrive\GitHub\academic\` (OneDrive sync로 multi-PC 동기화)

**잘못된 위치**: `C:\Users\shjpe\GitHub\academic\` — 2026-04-29 초기에 만들었던 stale clone.
2026-05-06에 폐기 + 디렉토리 삭제됨. 만약 미래의 어떤 PC에서 이 경로가 다시 cwd로 잡혀 있으면 **즉시 사용자에게 경고하고 OneDrive 경로로 전환**.

**왜 OneDrive에 두는가**: 사무실 데스크톱 + 노트북 multi-PC 워크플로 + `.timesheet-stats/` cache 공유. OneDrive `.git/`에 충돌 가능성 있으나 **두 PC에서 동시 작업하지 않는 sequential pattern으로 회피**.

세션 시작 시 검증 항목:
1. `cwd`가 `C:\Users\shjpe\OneDrive\GitHub\academic\`인지
2. `.timesheet-stats/`에 최신 backup 파일 존재 (`timesheet_backup_<오늘 또는 어제>.json` 형식)
3. `Get-ScheduledTask -TaskName 'TimesheetBackupFetch'` Trigger=09:00, NumberOfMissedRuns=0

---

## 파일 구조

```
academic/
├── index.html              ← Home (hero, research interests 4-card grid, Recent News)
├── research.html           ← Research (4-card grid + Current Projects 자동 렌더)
├── publications.html       ← Publications (JSON 기반 자동 렌더 + 8개 type 필터)
├── teaching.html           ← Teaching (강의 소개)
├── cv.html                 ← CV (학력, 경력, Selected Publications)
├── style.css               ← 공통 스타일 (fluid responsive, 3단 브레이크포인트)
├── sitemap.xml             ← 5 URL, priorities
├── robots.txt              ← 전체 허용 + sitemap 안내
├── google1f7b21bb5170b5de.html  ← Google Search Console verification
├── photo.jpg               ← 프로필 사진 (직접 추가 — onerror로 missing OK)
├── README.md               ← 사용자용 운영 매뉴얼
├── current project.txt     ← 5개 current project 영문 설명 원문 (사용자 작성)
│
├── data/
│   ├── publications.json   ← 논문 데이터 (모든 발표 SOT — 여기만 수정하면 자동 업데이트)
│   ├── current-projects.json  ← 진행 중 프로젝트 (research.html이 fetch)
│   └── CV_Seung-Ho_JUNG(20251010).pdf
│
├── js/
│   └── research-interests.js  ← 4-card 자동 갱신 + Current Projects 렌더 + 3-tier 우선순위
│
└── .claude/
    ├── settings.json        ← Stop hook (auto-push) — repo에 commit
    ├── settings.local.json  ← 개인 권한 (gitignored)
    ├── auto-push.sh         ← auto-commit/push 스크립트
    ├── worklog/             ← 작업 일지 (gitignored, OneDrive 동기화로만 보존)
    └── career/              ← 경력 컨설팅 자료 (gitignored, 비공개)

.timesheet-stats/            ← timesheet 자동 백업 cache (gitignored, 통합 진단용)
```

**Out-of-repo (관련 위치)**:
- `C:\Users\shjpe\.claude\projects\C--Users-shjpe-OneDrive-GitHub\memory\` — 메모리 (multi-project 부모 폴더용). academic 단독 launch 시엔 `C--Users-shjpe-OneDrive-GitHub-academic\memory\`도 사용
- `C:\Users\shjpe\OneDrive\GitHub\.claude\fetch-timesheet-backup.ps1` — Apps Script endpoint 호출, `.timesheet-stats/`에 저장
- Windows Task `TimesheetBackupFetch` — 매일 09:00 KST, `-WakeToRun`/`-StartWhenAvailable`/`-AllowStartIfOnBatteries`

---

## 페이지별 구조

### `index.html` (Home)
- `<head>`: 한/영 통합 title, meta description, keywords, canonical, Open Graph, Twitter Card
- JSON-LD `Person` schema (`alternateName`, `worksFor`, `address`, `sameAs`=Google Scholar, `knowsAbout`)
- Hero: photo + 이름(영/한) + 직위 + 한국어 소속 라인 (`인천대학교 동북아국제통상물류학부 부교수`, Korean SEO 매칭) + Office/주소/Tel/이메일 2개(`shjung@inu.ac.kr`, `shjpeace@gmail.com`) + 3 hero links (Google Scholar / CV / Email)
- **Research Interests** 섹션: `<div id="research-grid">` — `js/research-interests.js`가 4-card 자동 갱신
- **Recent News**: 최근 ~9개 항목 수동 관리. 새 publication/commentary 추가 시 최상단에 `<div class="news-item">` 추가, 가장 오래된 것 제거 (사용자 판단)

### `research.html`
- `<head>`: 동일 SEO 패키지 (page별 canonical, title)
- Research Interests 4-card grid (`#research-grid`) + Current Projects 자동 렌더 (`#current-projects`)
- 정적 fallback이 HTML에 박혀 있어 JS 실패해도 페이지는 안 깨짐

### `publications.html`
- `<head>`: SEO
- Filter buttons: `all` / `journal-en` / `journal-kr` / `commentary-en commentary-kr` (둘 다) / `report-en report-kr` (둘 다) / `working-paper` / `book`
- `data/publications.json` fetch → `SECTION_LABELS` + `SECTION_ORDER` 기준 섹션 렌더
- `formatPub(p)`: type별 분기 (book은 별도 분기). authors, year(.month), title(linked), journal(italic), volume(issue), pages, year_label, publisher, DOI 순
- `buildLinks(p)`: `kr_url` (EAI 한글 버전 — 현재는 분리된 Korean entry 쓰므로 거의 비어있음), `extra_url`

### `teaching.html` / `cv.html`
- `cv.html`: 학력(B.Agr. Korea Univ. 2001 / MPP KDI School 2003 / Ph.D. SNU 2014), 경력(BoK Economist 2014–2019, KIEP Researcher 2005–2007 등), Selected Publications(5건 + DOI 링크), `data/CV_Seung-Ho_JUNG(20251010).pdf` 다운로드 (URL-encoded `%28%29`)

---

## 데이터 모델

### `data/publications.json`

배열. 항목 구조 (id 내림차순으로 유지):

```json
{
  "id": 49,
  "type": "commentary-kr",
  "year": 2026,
  "month": 5,
  "authors": "정승호, 이현태",
  "title": "...",
  "journal": "관행중국",
  "publisher": "인천대학교 중국학술원",
  "note": "[웹진]",
  "url": "...",
  "volume": "10", "issue": "2", "pages": "1–30",
  "doi": "10.xxxx/xxxxx",
  "kr_url": "...", "extra_url": "...", "extra_label": "..."
}
```

#### Type 목록

| type | 설명 |
|---|---|
| `journal-en` | 영문 피어리뷰 저널 |
| `journal-kr` | 한국어 피어리뷰 저널 |
| `commentary-en` | 영문 Commentary / Policy Brief (Global NK 등) |
| `commentary-kr` | 한국어 Commentary (EAI 동아시아연구원, 인천대 중국학술원 관행중국 등) |
| `report-en` | 영문 Special Report |
| `report-kr` | 한국어 정책보고서 (KDI 북한경제리뷰, EAI Special Report 등) |
| `working-paper` | Working Paper (BOK 경제연구, IMF WP 등) |
| `book` | 단행본 / 챕터 |

### `data/current-projects.json`

배열. `research.html`의 Current Projects 섹션 자동 렌더용.

```json
{ "title": "...", "url": "...", "meta": "with ... (소속) · ...", "description": "...",
  "tags": ["GPRNK", "stock returns", "지정학"] }
```

순서는 **impact 기반** (`677ae88` 이후): GPRNK paper 1번 → famine → regional reconfiguration → health assimilation → anti-unification.

`(INU)` 표기는 본인 소속이라 `meta` 공저자 목록에서 **제외** — durable feedback (memory `user_affiliation.md`).

---

## `js/research-interests.js` — 자동 카드 + 우선순위 룰 ⭐

**4개 카테고리 고정**: nk-economy / foreign-relations / unification / refugees. 각 카드에 "Latest" 또는 "Current project" 라벨로 1건 surface.

### Scoring
- 항목 텍스트 = `title + book + journal + note + tags.join(' ')` lowercase
- 카테고리별 keyword 매칭. **6자 이상 keyword = 2점, 짧은 건 1점**

### 3-Tier 우선순위 (사용자 2026-05-06 명시)

> "publication을 우선하고, 현재일 기준으로 관련분야의 3개월 publication이 없을때만 on going project표시"

```
Tier 1 — 최근 3개월 내 publication           (recent pub)
Tier 2 — ongoing project                     (Tier 1 비어있을 때만)
Tier 3 — 3개월 이전 publication              (최후 fallback)
```

각 tier 내: year/month 내림차순. `month` 없는 entry는 year-end(12월)로 처리해서 "Forthcoming" 같은 entry가 부당하게 older tier로 추락하지 않도록 함.

`recentCutoffMonths()` = `now.year*12 + now.month - 3`.

### EAI 한·영 페어 중복 방지

EAI(동아시아연구원)는 같은 글을 `commentary-en` (Global NK) + `commentary-kr` (동아시아연구원) 두 entry로 발행. **research-interests scoring에서 한글 페어를 제외** (`isEAIKoreanTranslation`: `commentary-kr` AND `journal === "동아시아연구원"`).

**Exemption**: 한글 단독 commentary-kr (영문 페어 없음 — 예: id 49 관행중국)은 filter 통과. journal 값으로 식별하므로 자동.

→ Memory `project_eai_dual_publication.md` 룰 적용.

### Surface 결과 (오늘 기준 시뮬레이션 = 2026-05-06)

| 카테고리 | Tier | Winner |
|---|---|---|
| nk-economy | RECENT-PUB | id 47 (2026.4) Assessment of NK 9th Party Congress |
| foreign-relations | **RECENT-PUB** | **id 49 (2026.5) 관행중국 웹진** |
| unification | ONGOING | Corporate Investment under NK Threats (3개월 내 unification pub 없음) |
| refugees | RECENT-PUB | id 48 (2026 Forthcoming) Health Status & Economic Assimilation |

---

## SEO / 검색 등록 현황

| 도구 | 상태 | 비고 |
|---|---|---|
| Google Search Console | ✅ Verify + sitemap 제출 + 5 URL Request indexing | `google1f7b21bb5170b5de.html` |
| Naver Search Advisor | ✅ Verify (host repo) + sitemap + 5 URL 수집 요청 | `shjpeace-cloud.github.io` host에 `naver*.html` |
| Google Scholar | URL 변경 권장 (TODO) | Homepage URL → 새 사이트 |
| sitemap.xml | ✅ 5 URLs, priorities | |
| robots.txt | ✅ Allow all + sitemap | |
| JSON-LD Person schema | ✅ index.html에 박힘 | knowsAbout 배열에 영/한 키워드 |
| Open Graph + Twitter Card | ✅ 모든 페이지 head | |

**SEO 권위 이전 미완료**: 옛 Google Sites (`sites.google.com/site/shjpeace`) 가 여전히 검색 1위. 5개 페이지에 redirect HTML 박스 적용해야 함 (worklog 2026-04-29 후속 #1).

---

## 작업 규칙

### 1. 편집 → 즉시 push (사용자 2026-05-05 feedback)

이전: 부모 폴더 Stop 훅이 턴 끝날 때 묶어서 commit/push.
**현재**: academic 편집을 마치면 즉시 descriptive 메시지로 commit + push. Stop 훅은 backup 안전망.

이유: "did you push?" 라운드트립 회피. memory `feedback_push_immediately.md`.

### 2. Stop hook 동작 (`.claude/auto-push.sh`)

매 턴 종료 시:
1. `cd "$(dirname "$0")/.."` (상대경로 — 4/29 stale clone 절대경로 버그 수정 후 안전)
2. `git status --porcelain` — 변경 없으면 silent exit
3. `git add -A` → `git commit -m "auto: changes from Claude Code session"`
4. `git push origin main`
5. systemMessage로 결과 표시

부모 폴더 (`OneDrive\GitHub\.claude\auto-push-router.sh`)는 academic + timesheet 두 폴더를 순회하며 각자 auto-push.sh 위임.

### 3. 새 publication 추가 시

1. `data/publications.json` 최상단(또는 id 큰 쪽)에 추가 — 신규 id = max+1
2. `index.html` Recent News 최상단에 `<div class="news-item">` 추가, 가장 오래된 1-2건 제거
3. EAI 한·영 페어면 두 entry로 분리 (`commentary-en` + `commentary-kr`/journal=`동아시아연구원`)
4. type이 신규(예: `commentary-kr` 신설)면 `publications.html` SECTION_LABELS / SECTION_ORDER / filter button 등록
5. 즉시 commit + push

### 4. 새 current project 추가 시

`data/current-projects.json`만 수정. `research.html` 직접 편집 불필요 (JS가 fetch). 정적 fallback HTML도 같이 업데이트하면 JS-disabled 환경 안전.

공저자 메타에 `(INU)` 본인 소속 빼기.

### 5. CV 업데이트 시

새 PDF를 `data/CV_Seung-Ho_JUNG(YYYYMMDD).pdf`로 배치 (옛 PDF 그대로 둬도 됨 — 링크만 갈아끼움). `cv.html`의 두 곳 갱신:
- `<a class="cv-download" href="data/CV_Seung-Ho_JUNG%28YYYYMMDD%29.pdf">` (URL-encoded 괄호)
- `Last updated: ...` 라인

### 6. `formatPub` 알려진 동작

- `note` 필드는 `[Commentary]` / `[웹진]` / `[논평]` 같은 라벨용. 2026-05-06에 두 번 출력되던 pre-existing bug 수정 완료(`a490611`).
- `book` 분기는 line 89-100에 따로 있음. 일반 분기는 line 103+.
- `kr_url`은 한·영 분리 후 거의 사용 안 함. 분리되지 않은 옛 entry에만 잔존 가능.

### 7. 반응형 / Style 룰

- `style.css` fluid typography: `clamp(min, ideal+vw, max)`로 PC↔모바일 부드러운 스케일링
- 브레이크포인트:
  - `≤768px` (태블릿): nav 높이 축소
  - `≤640px` (모바일): hero 1열, research-grid 1열, **`.nav-brand` 숨김** (페이지에 이미 이름 있음 — 사용자 결정)
  - `≤380px` (소형 폰): 추가 축소, news-item 세로 스택
- `.research-card-latest`: 카드 하단 점선 + gold 라벨로 최신 항목 강조

---

## 보안·프라이버시

- `.gitignore`: `.claude/career/`, `.claude/worklog/`, `.timesheet-stats/`, `.claude/settings.local.json`, `.claude/smoke.log` 등은 모두 push 안 됨
- `.claude/career/evaluation.md` (22KB, 단일 파일로 통합 — 4/30 evaluation.txt + 5/5 evaluation.md merge): 김규철 비교, Ewha 결정 분석, Lever 1번 실행 로그, 통합 진단 spec 포함. **절대 push 금지**
- timesheet `BACKUP_SECRET`은 OneDrive/GitHub 외부 — Windows User scope 환경변수 (`TIMESHEET_CLOUD_URL`, `TIMESHEET_BACKUP_SECRET`)에만 존재

---

## 통합 진단 (`.claude/career/integrated-diagnosis-framework.md` 기반)

**Trigger**: "통합 진단해줘" / "integrated diagnosis" / "academic + timesheet 종합" / 시간통계 새 백업 언급.

**Inputs (이 순서로 read)**:
1. `.timesheet-stats/<latest>.json` (`ls -t .timesheet-stats/*.json` 가장 최근)
2. `data/publications.json`
3. `data/current-projects.json`
4. `cv.html`
5. `.claude/career/baseline-*.md` (직전 baseline)
6. `.claude/career/evaluation.md`
7. memory files

**핵심 metric**: **R1 (실제 연구) 일평균 추세** — 본인 top journal lever의 시간 함수.

| R1 일평균 | 의미 |
|---|---|
| ≥ 1.5 h/d | 충분 — top journal 1편 1년 페이스 가능 |
| 1.3–1.5 h/d | 안정 baseline — JIE급 1.5–2년 페이스 |
| 1.1–1.3 h/d | 위험 신호 — publication 정체 |
| < 1.1 h/d | output 둔화 거의 확실 |

**최신 baseline (2026-04-30)**: 2025년 R1=1.12 h/d 5년 최저, 2026 1-4월 1.39 h/d 회복 중. 4월 M3(시간통계 자기언급) 53h spike — instrumentation overhead. 김규철 paper 여전히 pending.

**Anomaly 점검**: R1 ±20% break / M3 spike / R 그룹 내부 unbalance / D 변동 / A 0인 날 다수.

**Output**: 한국어, candid analytical, flattery 금지. 변화 없으면 짧게 명시.

---

## Known issues / 후속 작업

| 우선 | 항목 | 비고 |
|---|---|---|
| 높 | **Web analytics 셋업** | Cloudflare Web Analytics 권장 (무료, 쿠키 X, GDPR/PIPA 적합). 5개 HTML에 snippet 1줄. 현재 visit 통계 0건 |
| 높 | **Google Sites redirect** | 옛 사이트 5페이지에 redirect HTML 박스. SEO 권위 이전 — 새 사이트 검색 가시성에 결정적 |
| 높 | **Google Scholar Homepage URL 변경** | 1분 작업, 인덱싱 가속 |
| 중 | **INU 학과 페이지 URL 변경 행정 요청** | `inu.ac.kr` 도메인 backlink — SEO 점프 효과 큼 |
| 중 | **OneDrive `.git/` 충돌 모니터링** | 두 PC 동시 작업 X 룰 유지. `.git/index.lock` / HEAD conflict copy 발견 시 룰 강화 |
| 중 | **3-tier rule cadence 재검토 (~2026-12)** | publication 빈도 변화 시 cutoff 3개월이 적절한지. 모든 카드가 항상 Tier 1이면 ongoing 표시 기회 사라짐 |
| 낮 | **Scheduler missed runs 재발 시** | Operational log enabled 상태. `Get-WinEvent -LogName 'Microsoft-Windows-TaskScheduler/Operational'`로 raw evidence 확보 |
| 낮 | **ORCID / KCI URL 등록** | 5분 |
| 낮 | **`photo.jpg` 추가** | onerror로 사이트는 안 깨짐, 시각만 보강 |

---

## 작업 로그 (worklog)

- 위치: `.claude/worklog/YYYY-MM-DD.md` (gitignored, OneDrive 동기화로만 보존)
- **Claude 책임**: 매 작업 마무리 전 대화 요약 append (사용자 요청 요지 + 한 일 + 변경 파일)
- **훅 책임**: commit 성공 시 자동 append
- 멀티프로젝트 인프라 작업(예: 부모 폴더 셋업)은 양쪽 worklog에 모두 기록
- 용도: "어제/지난주 뭐 했지?" 답변 + 다음 세션 컨텍스트

### worklog 누적 내역 (2026-04-29 ~ 2026-05-06)

| 날짜 | 핵심 |
|---|---|
| 04-29 | Google Sites → GitHub Pages 이전, CV PDF/HTML 업데이트, Research 4분야 재구성, SEO 풀패키지(meta/JSON-LD/sitemap/robots), Search Console + Naver 등록, user-page redirect repo 생성, book rendering bugfix |
| 04-30 | 반응형 CSS (clamp, 3단 BP, 모바일 nav-brand 숨김), `js/research-interests.js` 신설 (4-card 자동 갱신), `data/current-projects.json` 분리, BOK 경제연구 → working-paper 재분류, **auto-push Stop 훅 셋업** |
| 04-30 (오전) | 첫 통합 진단 baseline 작성 (`.claude/career/baseline-2026-04-30.md`) |
| 05-01 | 부모 폴더 멀티프로젝트 셋업 (academic + timesheet 단일 터미널), auto-push.sh 절대경로 버그 픽스, timesheet 자동 백업 → `.timesheet-stats/` Apps Script endpoint + Task Scheduler 04:00 (이후 09:00로 이동) |
| 05-05 | Current Projects impact-based 재정렬 + GPRNK SSRN DOI 링크, **편집 직후 즉시 push 정책 변경**, evaluation.txt+evaluation.md 단일 .md 통합, auto-backup 5/2 이후 누락 진단 |
| 05-06 | **Stale clone 발견 + 폐기** (working dir 정정), Backup scheduler 정상화 (04:00→09:00, junction 셋업, Operational log 활성화), 관행중국 commentary id 49 추가, EAI 한·영 페어 분리 (id 50/51/52/53/54) + research-interests 한글 페어 제외 filter, **3-tier 우선순위 룰** (recent pub > ongoing > older pub), formatPub note 중복 출력 bug 수정 |

---

## 저자 / 소속 (publications.json `authors` 표기 룰)

- 영문: `Jung, Seungho` 본인 첫 자리. 공저자: `Jung, Seungho, Coauthor Name`
- 한글: `정승호` 본인 첫 자리. 공저자: `정승호, 공동저자`
- `(INU)` 본인 소속 표기 **제외**
- `meta` (current-projects.json)에는 공저자 소속 명시: `with Jongmin Lee (Korea National Defense University)` 형식
