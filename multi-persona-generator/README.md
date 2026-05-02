# Multi-Persona Generator

화이트칼라 작업 영역(이메일, 보고서, PPT, 계약서, 이력서, 투자 메모, 사내 공지 등)을 한 단어라도 언급하면, 그 영역 전용 Claude 프로젝트 system instruction을 멀티 페르소나 방법론으로 즉시 생성해 주는 Claude Code Skill입니다.

생성된 마크다운을 Claude나 ChatGPT의 프로젝트 지침 박스에 그대로 붙여 넣으시면, 그 프로젝트에서 만들어지는 모든 산출물이 자동으로 5색 평가 레이어를 통과합니다.

---

## 목차

- [60초 시작](#60초-시작)
- [멘탈 모델: 5색 메타포](#멘탈-모델-5색-메타포)
- [설치](#설치)
- [사용법](#사용법)
- [생성된 지침을 프로젝트에 적용하기](#생성된-지침을-프로젝트에-적용하기)
- [카테고리 라우팅](#카테고리-라우팅)
- [합격선 차등](#합격선-차등)
- [폴더 구조](#폴더-구조)
- [평가와 트러블슈팅](#평가와-트러블슈팅)
- [라이선스](#라이선스)

---

## 60초 시작

1. 스킬 폴더에 클론합니다.
   ```bash
   git clone https://github.com/airoasting/multi-persona-generator.git \
     ~/.claude/skills/multi-persona-generator
   ```
2. Claude Code 세션을 새로 열고 한 단어만 칩니다. 예. "이메일".
3. 마크다운 한 묶음(1500-3500자)으로 system instruction이 출력됩니다.
4. Claude Projects(claude.ai) 또는 ChatGPT Projects(chatgpt.com)에서 새 프로젝트를 만드시고, Project instructions 박스에 출력된 마크다운을 통째로 붙여 넣고 저장합니다.
5. 그 프로젝트의 채팅창에 평소 요청을 던지시면 BLACK이 1차 산출물을 만들고 RED, SILVER, BLUE, GOLD 4인이 10점 만점으로 자동 평가합니다.

---

## 멘탈 모델: 5색 메타포

LLM에 "이메일 써줘"라고 던지면 평균치의 글이 나옵니다. 톤은 무난하고 구조는 표준이며, 어디 한 군데도 틀리지 않았지만 그래서 아무도 다시 읽지 않습니다. 이 스킬은 그 평균치를 깹니다. 만드는 사람 1명, 비판하는 사람 3명, 읽는 사람 1명이 등장하는 system instruction을 생성합니다.

| 색 | 역할 | 인원 | 정체 |
|----|------|------|------|
| BLACK | 실행자 | 1명 | 그 작업 영역 베테랑 15년차+ |
| RED | 비평가 (WHAT 축) | 1명 | 내용·결론·메시지 검증자 |
| SILVER | 비평가 (HOW 축) | 1명 | 구조·논리·흐름 검증자 |
| BLUE | 비평가 (FORM 축) | 1명 | 톤·분량·시각·호흡 검증자 |
| GOLD | 독자 | 1명 | 시간·장소·행위·심리로 정의된 단일 독자 |

세 가지 핵심 원칙입니다.

- 비평가 셋의 축은 WHAT, HOW, FORM 세 카테고리에서 한 개씩 뽑습니다. 같은 카테고리에서 두 축을 뽑으면 시야가 겹쳐 평균치로 흐릅니다.
- GOLD는 인구통계가 아니라 상황으로 정의합니다. "30대 직장인"이 아니라 "월요일 9시 30분, 이사회 직전에 5장짜리 보고서를 처음 펼친 CEO"처럼 시간, 장소, 행위, 심리가 들어갑니다.
- BLACK은 항상 15년차 이상으로 캐스팅하고 톤, 제약, 분량을 한 줄로 못 박습니다.

자세한 캐스팅 9원칙과 출력 템플릿은 [SKILL.md](SKILL.md)를 보십니다.

---

## 설치

방법 1. Claude Code skill 폴더에 클론합니다(권장).

```bash
git clone https://github.com/airoasting/multi-persona-generator.git \
  ~/.claude/skills/multi-persona-generator
```

`~/.claude/skills/` 아래에 폴더가 있으면 Claude Code가 자동 인식합니다. 별도 등록이 없습니다. 다음 메시지부터 트리거됩니다.

방법 2. 프로젝트별 설치는 그 프로젝트 루트의 `.claude/skills/` 아래에 클론합니다. 팀 저장소에 커밋해 두시면 동료 머신에서도 자동 동작합니다.

방법 3. claude.ai 웹의 Project 환경에서는 skill 자동 로딩이 없습니다. [SKILL.md](SKILL.md) 본문(frontmatter 제외)을 통째로 Project instructions 박스에 붙이시면 같은 동작을 합니다.

---

## 사용법

작업 영역을 한 마디라도 언급하시면 트리거됩니다. 명확화 질문 없이 즉시 가장 일반적인 해석으로 캐스팅합니다.

한국어 트리거 예시.

```
이메일
보고서 검토
계약서 검토 지침
위기 대응 메시지
이력서 작업
PPT 지침
투자 메모
사내 공지
```

영문 트리거 예시.

```
make a system prompt for resume work
create a project instruction for sales emails
project guide for OKR reports
instruction for board memo
```

영문 트리거가 들어오면 자동으로 [`references/english-augment.md`](references/english-augment.md)도 함께 읽어 영문 보강을 적용합니다. BLACK과 GOLD가 영어 환경 인물로 캐스팅되고, 분량 단위가 단어 수로 바뀌며(700-1700 words), 평가 발화도 영문으로 나옵니다.

복합 산출물(예. "영업 덱이랑 발표 스크립트 같이")은 본체 작업 영역 하나를 결정하고 부속을 BLACK 제약 줄에 흡수합니다. 시리즈물("주간 뉴스레터 시리즈")은 캐스팅에 고정 자산 한 줄이 추가됩니다.

다음은 트리거되지 않습니다. 이미 만든 산출물을 평가, 요약, 계수하는 작업과 단순 사실 검색, 계산, 기계적 변환입니다("이 이메일 톤만 평가해줘", "이 보고서 한 줄 요약", "fix typos in this report"). 이 스킬은 system instruction을 만드는 도구지 산출물 자체를 평가하는 도구가 아닙니다.

---

## 생성된 지침을 프로젝트에 적용하기

이 스킬의 출력은 새 프로젝트의 지침 박스에 붙여 넣을 system instruction 마크다운 한 묶음입니다. 코드를 작성하시거나 API를 호출하실 필요가 없습니다.

전체 흐름은 세 단계입니다.

1. Claude Code에서 스킬을 트리거합니다.
2. 출력된 마크다운을 통째로 복사합니다. 첫 줄 `# [작업 영역명] 프로젝트`부터 마지막까지 모두 포함합니다. 끝에 붙는 안내 한 줄("위 마크다운을 새 클로드 프로젝트의 지침 박스에 붙여 넣어 사용하세요")은 사용자 안내용이므로 빼고 복사합니다.
3. 새 프로젝트의 지침 박스에 붙여 넣고 저장합니다.

### Claude Projects (claude.ai)

1. [claude.ai](https://claude.ai)에서 좌측 사이드바의 Projects → New project를 누릅니다.
2. 프로젝트 이름을 입력합니다. "외부 비즈니스 이메일", "이사회 1페이지 보고서"처럼 작업 영역 단위로 적으십니다.
3. Project instructions 박스를 열고 복사한 마크다운을 통째로 붙여 넣습니다.
4. Save instructions를 누릅니다.
5. 그 프로젝트의 채팅창에 평소 요청을 던지시면 5색 평가가 자동으로 돌아갑니다.

### ChatGPT Projects (chatgpt.com)

1. [chatgpt.com](https://chatgpt.com)에서 Projects → New project를 누릅니다.
2. 프로젝트 이름과 한 줄 설명을 입력합니다.
3. Instructions 박스에 복사한 마크다운을 통째로 붙여 넣고 Save를 누릅니다.
4. 채팅창에서 작업 요청을 던지시면 동일하게 5색 평가가 돌아갑니다.

GPT-5와 GPT-4o 어느 모델을 쓰시든 페르소나 5색 구조와 합격선 평가 절차는 동일하게 인식됩니다.

### 자주 막히는 지점

- 5색 평가가 자동으로 안 돕니다. 마크다운의 `## 워크플로우` 섹션이 빠짐없이 들어갔는지 확인하십니다.
- 분량 한도를 초과합니다. "좀 더 짧게 다시 만들어줘" 한 줄로 1500-2000자 범위로 다시 생성합니다.
- 한 프로젝트에 두 영역을 합치지 않습니다. 작업 영역마다 별도 프로젝트를 만드십니다.

---

## 카테고리 라우팅

사용자가 단어 하나만 말씀하셔도 8개 카테고리 중 하나로 캐스팅합니다.

| # | 카테고리 | 참조 파일 | 대표 키워드 |
|---|---------|----------|------------|
| 1 | 외부 커뮤니케이션 | [external-comm.md](references/external-comm.md) | 이메일, 위기 대응, 보도자료, 뉴스레터, SNS, 블로그, CS |
| 2 | 내부 커뮤니케이션 | [internal-comm.md](references/internal-comm.md) | 사내 공지, 1on1, 채용 공고, 타운홀, HR 정책 |
| 3 | 의사결정 문서 | [decision-docs.md](references/decision-docs.md) | 보고서, 이사회, IR, OKR, 투자 메모, DD, 6-pager |
| 4 | 발표 자료 | [presentation.md](references/presentation.md) | PPT, 슬라이드, 영업 덱, 피치덱, 컨설팅 덱 |
| 5 | 분석·법무 | [analysis-legal.md](references/analysis-legal.md) | 계약서, 법률 의견서, 소장, 감사·세무, 실사 |
| 6 | 마케팅 | [marketing.md](references/marketing.md) | 카피, 슬로건, 네이밍, 브랜드 가이드 |
| 7 | AI 프롬프트 | [ai-prompt.md](references/ai-prompt.md) | 이미지·영상 생성, LLM 시스템 프롬프트 |
| 8 | 개인용 | [personal.md](references/personal.md) | 이력서, 자기소개서, 커버레터, 인터뷰 |

표에 없는 과제는 가장 가까운 카테고리로 잡습니다. 카테고리도 모호하면 외부 커뮤니케이션이 최종 fallback입니다.

---

## 합격선 차등

작업 영역마다 평가 합격선이 다릅니다.

| 합격선 | 작업 영역 성격 | 예 | 분량 |
|--------|---------------|-----|------|
| 9.0 | 정답 없음, 개인 톤이 자산 | 시, 단편 소설, 블로그 | 1500-2000자 |
| 9.5 | 표준 (기본값) | 보고서, 이메일, PPT, 마케팅 카피 | 2000-2800자 |
| 9.7 | 결함이 곧 손실 | 계약서, 이사회 보고서, 주주 서한, 위기 대응, IR | 2800-3500자 |

9.7군은 그 영역의 흔한 실패 문구를 직접 인용 금지로 박아 넣습니다. 예. 계약서의 "합리적 노력", IR의 "견조한", 위기 대응의 "일부 부주의로". 일반 어휘로 "형용사를 줄여라"라고 적어도 LLM이 진짜 실패 문구를 피하지 못하기 때문에, 구체 문장 단위로 금지를 박아야 실수가 줄어듭니다.

GOLD 합격선 기준 장면도 영역별로 다릅니다. "수신자가 미리보기 두 줄로 답장 여부를 정한다"(이메일), "법무 검토가 첫 시도에 통과한다"(계약서 9.7), "독자가 북마크하거나 링크를 누군가에게 공유한다"(블로그 9.0)처럼 시간, 장소, 동작이 들어간 한 줄 장면입니다.

영문 산출물 분량은 700-1700 words, 한국어 분량의 절반 수준입니다.

---

## 폴더 구조

```
multi-persona-generator/
├── SKILL.md                  스킬 본문 (frontmatter, 라우팅, 출력 템플릿, 자체 점검)
├── README.md                 이 파일
├── LICENSE                   Apache License 2.0
├── references/               카테고리별 매핑·문체·금지 뱅크
│   ├── ai-prompt.md
│   ├── analysis-legal.md
│   ├── decision-docs.md
│   ├── english-augment.md    영문 트리거 시 자동 추가
│   ├── examples.md           풀 출력 예시 5종
│   ├── external-comm.md
│   ├── internal-comm.md
│   ├── marketing.md
│   ├── personal.md
│   └── presentation.md
└── evals/
    ├── EVALS_GUIDE.md
    └── trigger_eval.json
```

`references/<카테고리>.md`에는 매핑 표(작업 영역별 RED, SILVER, BLUE 축, 합격선, 기준 장면), 문체와 금지 뱅크, fallback 합성 알고리즘이 들어 있습니다. 작업 영역을 추가하시려면 이 파일들만 손보시면 됩니다.

[`references/examples.md`](references/examples.md)에는 풀 출력 예시 5종(이메일, 9.7군 외부 메시지, 이력서, 블로그, 영업 덱+발표 스크립트 복합)이 들어 있어 처음 쓰실 때 톤과 구조를 익히기 좋습니다.

---

## 평가와 트러블슈팅

[`evals/`](evals/) 디렉터리에 트리거 정확도 평가 셋이 있습니다. should-trigger 10개와 should-not-trigger 10개로 구성되어 있고, should-not-trigger 10개 중 8개는 near-miss입니다(키워드는 포함하지만 평가, 요약, 계수 작업이라 트리거되면 안 되는 경우). 자세한 실행 방법은 [`evals/EVALS_GUIDE.md`](evals/EVALS_GUIDE.md)를 보십니다.

빠른 60초 sanity check.

1. 새 클로드 프로젝트를 만드시고 SKILL.md 본문을 지침 박스에 붙입니다.
2. 채팅에 "이메일"이라고만 칩니다. 마크다운 한 묶음이 나오는지 확인합니다.
3. "위기 대응 메시지"를 한 번 더 쳐서 9.7군 처리(직접 인용 금지 2줄 이상)가 들어가는지 확인합니다.

자주 막히는 지점.

- 스킬이 트리거되지 않습니다. 폴더 경로와 이름(`~/.claude/skills/multi-persona-generator/`)을 확인하시고 Claude Code 세션을 새로 여십니다.
- 트리거되긴 하는데 평이한 답변입니다. references 디렉터리의 카테고리 파일이 모두 있는지 확인합니다.
- 9.7군인데 직접 인용 금지가 1개뿐입니다. 다음 메시지에 "9.7군이면 직접 인용 금지 두 개 이상이어야 함"을 명시하시면 재생성됩니다.
- 영문 트리거인데 한국어가 나옵니다. "in English"를 명시하시거나 [`references/english-augment.md`](references/english-augment.md)가 폴더에 있는지 확인합니다.

---

## 라이선스

Apache License 2.0입니다. 자세한 내용은 [LICENSE](LICENSE)를 보십니다.
