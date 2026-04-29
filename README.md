# Seungho Jung — Academic Website

Personal academic website for Seungho Jung (정승호), Associate Professor at Incheon National University.

**Live site:** `https://shjpeace-cloud.github.io/academic/`
*(Update this URL after deployment)*

---

## 파일 구조

```
academic-site/
├── index.html          ← Home (연구 소개, 최근 소식)
├── research.html       ← Research (연구 분야, 진행 중 프로젝트)
├── publications.html   ← Publications (JSON에서 자동 렌더링)
├── teaching.html       ← Teaching (강의 소개)
├── cv.html             ← CV (학력, 경력, 연락처)
├── style.css           ← 공통 스타일시트
├── photo.jpg           ← 프로필 사진 (직접 추가 필요)
├── CV_Seung-Ho_JUNG.pdf ← CV PDF 파일 (직접 추가 필요)
└── data/
    └── publications.json  ← 논문 데이터 (여기만 수정하면 Publications 자동 업데이트)
```

---

## GitHub Pages 배포 방법

### 1. 저장소 생성

```bash
# shjpeace-cloud 계정에 새 저장소 생성
# 저장소 이름: academic (또는 원하는 이름)
# Settings → Pages → Source: main branch / root
```

### 2. 로컬에서 작업 (VS Code + Claude Code)

```bash
git clone https://github.com/shjpeace-cloud/academic.git
cd academic
# 파일들을 이 폴더로 복사
git add .
git commit -m "Initial site"
git push origin main
```

### 3. 배포 확인

`https://shjpeace-cloud.github.io/academic/` 접속 확인

### 4. 기존 Google Sites에서 리디렉션 (선택)

기존 `sites.google.com/site/shjpeace` 홈페이지에 다음 텍스트와 링크 추가:

> This site has moved to [새 URL]. You will be redirected automatically.

---

## Publications 업데이트 방법 (가장 중요)

새 논문이 출판되면 `data/publications.json` 파일 맨 앞에 항목 추가.

### JSON 항목 형식

#### 영문 저널 논문 (journal-en)
```json
{
  "id": 47,
  "type": "journal-en",
  "year": 2026,
  "authors": "Jung, Seungho, Coauthor Name",
  "title": "논문 제목",
  "journal": "Journal Name",
  "volume": "10",
  "issue": "2",
  "pages": "100–120",
  "doi": "10.xxxx/xxxxx",
  "url": "https://doi.org/10.xxxx/xxxxx"
}
```

#### 한국어 저널 논문 (journal-kr)
```json
{
  "id": 47,
  "type": "journal-kr",
  "year": 2026,
  "authors": "정승호, 공동저자",
  "title": "논문 제목",
  "journal": "저널명",
  "volume": "10",
  "issue": "2",
  "pages": "1–30",
  "url": "https://www.kci.go.kr/..."
}
```

#### 영문 Commentary (commentary-en)
```json
{
  "id": 47,
  "type": "commentary-en",
  "year": 2026,
  "month": 4,
  "authors": "Jung, Seungho",
  "title": "Commentary Title",
  "note": "[Commentary]",
  "journal": "Global NK",
  "url": "https://www.globalnk.org/...",
  "kr_url": "https://www.eai.or.kr/..."
}
```

#### 한국어 보고서 (report-kr)
```json
{
  "id": 47,
  "type": "report-kr",
  "year": 2026,
  "month": 4,
  "authors": "정승호",
  "title": "보고서 제목",
  "journal": "KDI 북한경제리뷰",
  "year_label": "2026년 4월",
  "publisher": "한국개발연구원",
  "url": "https://www.kdi.re.kr/..."
}
```

#### 단행본/챕터 (book)
```json
{
  "id": 47,
  "type": "book",
  "year": 2026,
  "authors": "정승호",
  "title": "챕터 제목",
  "book": "단행본 제목",
  "editor": "편집자 외 엮음",
  "publisher": "출판사",
  "url": "https://..."
}
```

#### Working Paper (working-paper)
```json
{
  "id": 47,
  "type": "working-paper",
  "year": 2026,
  "authors": "Jung, Seungho",
  "title": "Paper Title",
  "journal": "NBER Working Paper",
  "note": "No. 12345",
  "url": "https://..."
}
```

### 타입 목록

| type | 설명 |
|------|------|
| `journal-en` | 영문 피어리뷰 저널 |
| `journal-kr` | 한국어 피어리뷰 저널 |
| `commentary-en` | 영문 Commentary / Policy Brief |
| `report-en` | 영문 정책보고서 |
| `report-kr` | 한국어 정책보고서 |
| `working-paper` | Working Paper |
| `book` | 단행본 / 챕터 |

---

## Home 페이지 업데이트

새 논문/소식이 있을 때 `index.html`의 "Recent News" 섹션 맨 위에 추가:

```html
<div class="news-item">
  <div class="news-date">2026.04</div>
  <div>New article: <a href="링크" target="_blank">"제목"</a> — <em>저널명</em>, Volume(Issue).</div>
</div>
```

---

## 파일 추가 필요 항목

배포 전 다음 파일을 루트 폴더에 추가하세요:

- [ ] `photo.jpg` — 프로필 사진 (권장: 300×300px 이상, 정사각형)
- [ ] `CV_Seung-Ho_JUNG.pdf` — 최신 CV PDF

---

## CV 업데이트

`cv.html` 파일에서 다음 두 곳을 수정:

```html
<!-- CV 파일명 -->
<a class="cv-download" href="CV_Seung-Ho_JUNG.pdf" ...>

<!-- 업데이트 날짜 -->
<p ...>Last updated: October 2025</p>
```

그리고 새 PDF 파일을 루트에 교체.

---

## 로컬 테스트

로컬에서 테스트할 때는 `publications.html`이 `fetch('data/publications.json')`을 호출하므로
단순히 HTML 파일을 더블클릭하면 CORS 오류가 납니다. 간단한 로컬 서버 실행:

```bash
# Python
python -m http.server 8000
# 브라우저에서 http://localhost:8000 접속
```

또는 VS Code의 **Live Server** 확장 사용.

---

## 기존 사이트 주소

명함/이메일에 기재된 기존 주소:
`https://sites.google.com/site/shjpeace/home`

이 주소는 그대로 유지하고, 해당 페이지에 새 사이트 링크를 안내문과 함께 추가하는 것을 권장합니다.
