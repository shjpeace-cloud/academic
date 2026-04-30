# Schedule Setup Prompt

Claude.ai remote 연결이 회복되면 `/schedule` 명령 후 아래 prompt를 그대로 복사해서 사용.
매월 1일 KST 09:00 실행되는 career consultation agent 생성.

---

```
매월 1일 KST 09:00 (00:00 UTC) 에 실행되는 monthly career consultation agent를 만들어줘.

저장소: github.com/shjpeace-cloud/academic (main branch)

agent 작업:
1. repo의 최신 main 상태를 pull
2. .claude/career/ 폴더에서 가장 최근 baseline 또는 update 파일을 식별 (날짜순)
3. 다음 파일들의 현재 상태를 읽기:
   - data/publications.json
   - data/current-projects.json
   - cv.html
   - research.html
   - .claude/career/ 내 모든 파일
4. baseline 대비 변화 점검:
   - publications.json에 신규 항목 — 어떤 type/venue? top journal 진입 여부?
   - current-projects.json 신규/진행 update
   - cv.html 신규 awards / grants / committee / talks
   - 사용자가 누적 보고한 job market 변화 (.claude/career/ 다른 파일들에서)
5. .claude/career/YYYY-MM-DD-update.md 새 파일로 진단 작성:
   - 지난 baseline/update 대비 무엇이 변했나
   - top-journal lever 진행도 (특히 김규철 공저 working paper)
   - Marketization Index 후속 진행도
   - candidate set 재평가 (국제대학원 GSIS, 북한대학원대학교, 통일평화대학원 신설 가능성, 정부출연 본부장급, INU 정착 default)
   - 새로 spotted 된 NK economy 시장의 채용 신호 / institution 변화
   - 다음 1개월 권고 행동
6. commit + push to origin/main

진단 관점:
- 사용자: 정승호 (Seungho Jung), 51세 (1975년 1월생), INU Associate Prof, NK economy specialist
- 정년 14년 남음 → realistic upgrade try 1–2회. Risk-adjusted EV 기준 추천
- 제외 targets: KDI School, 동국대 (불교 filter), 이화 재시도, SNU 본진, 여대 일반
- 사용자가 frank substantive analysis 선호. flattery 금지

진단 형식:
- 한국어로 작성 (구조 헤더는 영문 OK)
- 변화가 없으면 "이번 달 의미 있는 변화 없음" 명시 + 그래도 권고 행동 1–2개 제시
- 변화가 큰 달엔 candidate set probability table 갱신

기타: 사용자에게 push notification 또는 email 으로 update 완료 알림 (가능하면).
```

---

## 대안: schedule이 끝까지 안 될 경우

**Calendar reminder 폴백**:
- Google Calendar / iOS / Outlook 에서 매월 1일 9시 알림 등록
- 알림 제목: "academic site career check 받기"
- 알림 받으면 새 Claude Code 세션 열고 다음 입력:
  ```
  /career-check 이번 달 진단해줘. .claude/career/ baseline 참고해서.
  ```
- 사용자가 직접 trigger하지만 1분 작업으로 끝남

**GitHub Actions 폴백** (Claude 없이 변화 detection만):
- `.github/workflows/career-check.yml` 작성 매월 1일 cron
- publications.json diff 감지하면 issue 생성
- 단 진단(analysis)은 사람 또는 별도 Claude 세션 필요
