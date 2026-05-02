# Evals 셋업 가이드

이 문서는 multi-persona-generator 스킬을 evals로 검증해서 9.45 → 10/10에 도달하는 방법을 담는다. 두 종류의 evals를 권장한다.

1. **트리거링 evals** — description이 정확한 케이스에서만 트리거되는지 (run_loop.py)
2. **출력 품질 evals** — 같은 입력 3회 호출 시 출력 구조가 일관되는지 (수동 비교 또는 run_eval.py)

---

## 1. 트리거링 evals (run_loop.py)

### 개요

skill-creator의 `run_loop.py`는 description을 자동으로 5번 반복 개선하면서 트리거 정확도를 측정한다. 60% 학습 + 40% 테스트 분할로 오버피팅을 방지한다.

### 사전 준비

#### 1.1 eval 셋 작성

`/Users/jaydenkang/Desktop/New Projects/20260501_멀티 페르소나 스킬/multi-persona-generator/evals/trigger_eval.json` 에 20개 쿼리 작성. should-trigger 10개 + should-not-trigger 10개.

```json
[
  {"query": "이메일 프로젝트 만들어줘", "should_trigger": true},
  {"query": "내일 거래처에 보낼 이메일 톤 가이드 좀 잡아줘 — 우리 회사 시그니처 톤이 있어야 할 것 같아", "should_trigger": true},
  {"query": "사과문 system instruction 필요해. 9.7 보정 적용된 걸로", "should_trigger": true},
  {"query": "make a project guide for OKR quarterly reports", "should_trigger": true},
  {"query": "create a system prompt for cover letter writing", "should_trigger": true},
  {"query": "PPT 작업할 때 쓸 클로드 프로젝트 셋업해줘", "should_trigger": true},
  {"query": "투자 메모 IC 미팅에서 쓸 거 — 가정 명시랑 베이스/업/다운 케이스 강제하는 지침", "should_trigger": true},
  {"query": "이력서 이직용. 경력 10년차 IT 매니저", "should_trigger": true},
  {"query": "multi-persona evaluation framework for press releases", "should_trigger": true},
  {"query": "사내 공지 가이드 — 슬랙 메시지 형식으로 짧게", "should_trigger": true},

  {"query": "이 이메일 톤만 평가해줘 — 너무 딱딱한 것 같은데", "should_trigger": false},
  {"query": "이 보고서 한 줄로 요약해줘", "should_trigger": false},
  {"query": "PPT 슬라이드가 몇 장이야?", "should_trigger": false},
  {"query": "이 계약서에 NDA 조항 있어?", "should_trigger": false},
  {"query": "이 자소서 점수 매겨줘 7/10 정도?", "should_trigger": false},
  {"query": "summarize this memo in one line", "should_trigger": false},
  {"query": "translate this email to English", "should_trigger": false},
  {"query": "fix typos in this report", "should_trigger": false},
  {"query": "오늘 점심 뭐 먹지?", "should_trigger": false},
  {"query": "파이썬 함수 작성해줘 — 두 숫자 더하는", "should_trigger": false}
]
```

핵심 — should-not-trigger 10개 중 8개는 **near-miss**다. "이메일·보고서·PPT·이력서·자소서·계약서" 같은 키워드를 포함하지만 "사용자가 만든 산출물을 평가·요약·계수"하는 작업이라서 트리거 X. 마지막 2개만 완전 무관(점심·코딩).

#### 1.2 모델 ID 확인

run_loop.py는 `claude -p` 서브프로세스를 호출하므로 현재 세션 모델 ID를 그대로 넘긴다. 이 세션은 `claude-opus-4-7`.

### 실행

터미널에서:

```bash
cd "/Users/jaydenkang/Desktop/New Projects/20260501_멀티 페르소나 스킬/multi-persona-generator"

python -m scripts.run_loop \
  --eval-set evals/trigger_eval.json \
  --skill-path . \
  --model claude-opus-4-7 \
  --max-iterations 5 \
  --verbose
```

(`scripts.run_loop`은 skill-creator 패키지의 모듈이므로 `PYTHONPATH`에 skill-creator 경로 추가 필요.)

```bash
export PYTHONPATH="/var/folders/2_/9tvc_jzd4vs_x2p7vd_3ffxh0000gn/T/claude-hostloop-plugins/2d7a646e17e17c3e/skills/skill-creator:$PYTHONPATH"
```

### 결과 해석

- 출력 JSON의 `best_description`이 새 description 후보.
- 학습 점수와 테스트 점수가 함께 나옴. **테스트 점수가 0.85 이상이면 9.5 → 10 도달**.
- 만약 best_description이 현 description보다 좋으면 SKILL.md frontmatter 교체. 더 나쁘면 유지.

---

## 2. 출력 품질 evals (수동)

skill-creator의 `run_eval.py`는 자동 grader 기반인데, 우리 스킬은 출력이 **창의적 system instruction**이라 자동 grading이 어렵다. 수동 평가가 더 정확.

### 셋업

`/Users/jaydenkang/Desktop/New Projects/20260501_멀티 페르소나 스킬/multi-persona-generator/evals/output_quality_eval.md` 에 다음 5개 케이스를 만들어 각각 3회 호출.

| ID | 입력 | 검증 항목 |
|----|------|-----------|
| Q1 | "이메일" | 9.5군. 카테고리 라우팅 정확. 분량 1500~2800자. |
| Q2 | "사과문" | 9.7군. 직접 인용 금지 2개 이상. BLACK 제약 2개. |
| Q3 | "블로그" | 9.0군. 특화 금지 1~2개로 절제. |
| Q4 | "영업 덱이랑 발표 스크립트 같이" | 복합 산출물. 본체+부속 흡수. GOLD 단일 독자. |
| Q5 | "make a system prompt for board memo" | 영문 트리거. english-augment 적용. GOLD 영문 환경. |

### 점검 체크리스트 (각 출력별)

- [ ] 출력이 **마크다운 한 묶음**이고 끝줄에 "위 마크다운을 새 클로드 프로젝트의 지침 박스에 붙여 넣어 사용하세요"가 있다.
- [ ] BLACK 캐스팅에 연차(15년차+), 톤, 제약, 분량 가이드 모두 있다.
- [ ] RED·SILVER·BLUE 축이 WHAT/HOW/FORM 한 개씩 (같은 카테고리 두 축 위반 없음).
- [ ] 비평가 발화 톤 셋이 서로 다르다.
- [ ] GOLD가 시간·장소·행위·심리가 들어간 한 줄 장면이다 (인구통계 아님).
- [ ] 9.7군이면 특화 금지 4~5개 + BLACK 제약 2개 + 직접 인용 금지 2줄 이상.
- [ ] 9.0군이면 특화 금지 1~2개로 절제.
- [ ] 분량이 1500~3500자.
- [ ] 자평·"어떠신가요" 마무리 없음.

3회 호출 결과의 **일관성**도 본다. 같은 입력에 대해 BLACK 톤 단어, GOLD 시간·장소가 매번 비슷한 범위 안에서 변주되는가, 아니면 매번 완전히 다른 사람이 쓴 듯 흔들리는가.

---

## 3. 합격 기준

| 항목 | 합격선 | 비고 |
|------|--------|------|
| 트리거링 정확도 (테스트) | **0.85 이상** | run_loop.py 결과의 best_description 테스트 점수 |
| 출력 체크리스트 통과율 | **9개 항목 모두 통과 × 5개 케이스 × 3회 = 135/135** | 한 항목이라도 한 번이라도 빠지면 fail |
| 일관성 | **3회 호출의 BLACK 톤·GOLD 시간이 같은 범위 안** | 매번 다른 직군으로 바뀌면 fail |

3개 모두 통과하면 **진짜 10/10**.

---

## 4. 빠른 검증 (60초 sanity check)

evals 다 돌릴 시간이 없을 때 60초 간이 검증:

1. 새 클로드 프로젝트를 만들고 SKILL.md 본문을 지침 박스에 붙인다.
2. 채팅에 "이메일"이라고만 친다.
3. 응답이 마크다운 한 묶음으로 오고 위 9개 체크리스트가 모두 통과하는지 확인한다.
4. "사과문" 한 번 더 쳐서 9.7군 처리(직접 인용 금지 2줄 이상)가 들어가는지 확인한다.

이 둘이 통과하면 일상 사용 OK 수준 (9.5/10). 진짜 10점은 위 1·2·3을 다 돌려야 함.

---

## 부록 A. eval-viewer 띄우기

run_loop.py가 끝나면 자동으로 HTML 리포트가 열리지만, Cowork 환경에서는 `--static` 플래그로 정적 HTML 출력만 생성된다.

```bash
python /var/folders/2_/9tvc_jzd4vs_x2p7vd_3ffxh0000gn/T/claude-hostloop-plugins/2d7a646e17e17c3e/skills/skill-creator/eval-viewer/generate_review.py \
  multi-persona-generator-workspace/iteration-1 \
  --skill-name "multi-persona-generator" \
  --benchmark multi-persona-generator-workspace/iteration-1/benchmark.json \
  --static evals/report.html
```

생성된 `evals/report.html`을 브라우저로 직접 연다.

---

## 부록 B. 회차 간 비교

iteration-2 이상으로 갈 때는 `--previous-workspace` 플래그로 직전 회차를 지정해서 변화량을 본다.

```bash
python -m scripts.run_loop \
  --eval-set evals/trigger_eval.json \
  --skill-path . \
  --model claude-opus-4-7 \
  --max-iterations 5 \
  --previous-workspace multi-persona-generator-workspace/iteration-1 \
  --verbose
```
