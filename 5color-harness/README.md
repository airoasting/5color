# 5-Color Harness

화이트칼라 작업 영역(이메일·보고서·PPT·계약서·이력서 등)을 한 단어라도 언급하면, 그 영역 전용 Claude·ChatGPT 프로젝트 system instruction을 5-Color Harness 방법론으로 즉시 생성하는 Claude Code Skill입니다.

생성된 마크다운을 프로젝트 지침 박스에 그대로 붙이시면, 이후 그 프로젝트의 모든 산출물이 5색 평가 레이어를 자동으로 통과합니다.

---

## 5색 메타포

| 색 | 역할 | 정체 |
|----|------|------|
| BLACK | 수행자 | 그 작업 영역 베테랑 15년차+ |
| RED | 이성 비평가 | 논리·근거·결론 타당성 |
| SILVER | 분야 전문가 비평가 | 베테랑이 첫눈에 짚는 디테일 |
| BLUE | 공감 비평가 | 수신자 감정·톤·진정성 |
| GOLD | 독자 | 시간·장소·행위·심리로 정의된 단일 독자 |

세 비평가는 서로 다른 사고 모드입니다. 한 색이 다른 색의 자리에 침범하면 그 발언은 무효입니다. GOLD는 인구통계가 아니라 상황(예. "월요일 9시 30분, 이사회 직전에 5장짜리 보고서를 처음 펼친 CEO")으로 정의합니다.

자세한 캐스팅 9원칙과 출력 템플릿은 [SKILL.md](SKILL.md)를 보십니다.

---

## 60초 시작

```bash
git clone https://github.com/airoasting/multi-persona-generator.git \
  ~/.claude/skills/5color-harness
```

1. Claude Code 세션을 새로 열고 한 단어를 칩니다. 예. "이메일".
2. 마크다운 한 묶음(1500-3500자)이 나옵니다.
3. Claude Projects 또는 ChatGPT Projects의 지침 박스에 통째로 붙이고 저장합니다.
4. 이후 그 프로젝트에서 BLACK이 1차 산출물을 만들고 RED·SILVER·BLUE·GOLD 4인이 자동 평가합니다.

claude.ai 웹에서 skill 자동 로딩 없이 쓰시려면 [SKILL.md](SKILL.md) 본문(frontmatter 제외)을 그대로 Project instructions에 붙이시면 같은 동작을 합니다.

---

## 트리거

작업 영역을 한 마디라도 언급하시면 즉시 캐스팅합니다. 명확화 질문 없습니다.

- 한국어 단어 단독: "이메일", "보고서", "PPT", "계약서", "이력서"
- 영문 단어 단독: "email", "deck", "memo", "resume"
- 문장형: "외부 비즈니스 이메일 지침", "make a system prompt for cover letter"

영문 트리거는 [`references/english-augment.md`](references/english-augment.md)가 자동 추가되어 BLACK·GOLD가 영어 환경 인물로 캐스팅되고 평가도 영문으로 나옵니다.

복합 산출물(예. "영업 덱+발표 스크립트")은 본체 한 영역을 결정하고 부속을 BLACK 제약에 흡수합니다. 시리즈물은 캐스팅에 고정 자산 한 줄이 추가됩니다.

다음은 트리거되지 않습니다. 이미 만든 산출물 평가·요약·번역·계수, 단순 사실 검색, 기계적 변환. 이 스킬은 system instruction을 만드는 도구지 산출물 자체를 평가하는 도구가 아닙니다.

---

## 카테고리·합격선·종결 체

상세한 표는 [SKILL.md](SKILL.md)에 들어 있습니다. 요약입니다.

- **카테고리 8개.** 의사결정·전략, 분석·보고서, 외부 커뮤니케이션, 마케팅, 내부 커뮤니케이션, 법무 검토·규제 대응, 커리어·상담, 소셜미디어·글쓰기. 표에 없는 과제는 외부 커뮤니케이션이 최종 fallback.
- **합격선 3군.** 9.0(시·소설·블로그처럼 작가 톤이 자산), 9.5(표준), 9.7(계약서·이사회·IR·위기 대응처럼 결함이 곧 손실).
- **종결 체.** 작업 영역마다 다릅니다. 한 산출물 안에 두 체가 섞이면 위반.
- **em dash 0개.** 본문에 `—`, `–` 한 개라도 있으면 자동 fail.

---

## 폴더 구조

```
5color-harness/
├── SKILL.md                  스킬 본문
├── README.md                 이 파일
├── LICENSE                   Apache License 2.0
├── references/               카테고리별 매핑·문체·금지 뱅크
│   ├── decision-strategy.md  의사결정·전략
│   ├── analysis-report.md    분석·보고서
│   ├── external-comm.md      외부 커뮤니케이션
│   ├── marketing.md          마케팅
│   ├── internal-comm.md      내부 커뮤니케이션
│   ├── legal-regulatory.md   법무 검토·규제 대응
│   ├── career-counseling.md  커리어·상담
│   ├── social-writing.md     소셜미디어·글쓰기
│   ├── english-augment.md    영문 트리거 시 자동 추가
│   └── examples.md           풀 출력 예시 5종
└── evals/                    트리거 정확도 평가 셋
```

작업 영역을 추가하시려면 해당 카테고리의 `references/` 파일만 손보시면 됩니다. 처음 쓰실 때는 [`references/examples.md`](references/examples.md)의 풀 예시 5종으로 톤과 구조를 익히실 수 있습니다.

---

## 트러블슈팅

- **5색 평가가 자동으로 안 돕니다.** 마크다운의 `## 워크플로우` 섹션이 빠짐없이 들어갔는지 확인.
- **9.7군인데 직접 인용 금지가 부족합니다.** "9.7군이면 직접 인용 금지 두 개 이상이어야 함"을 한 줄 던지시면 재생성.
- **영문 트리거인데 한국어가 나옵니다.** "in English" 명시 또는 [`references/english-augment.md`](references/english-augment.md) 존재 확인.
- **페르소나 정체성 침범.** "RED는 이성, BLUE는 공감만"을 한 줄 던지시면 재캐스팅.
- **em dash가 보입니다.** "본문 em dash 0개로 다시" 한 줄.

평가 셋과 60초 sanity check는 [`evals/EVALS_GUIDE.md`](evals/EVALS_GUIDE.md)를 보십니다.

---

## 라이선스

Apache License 2.0. [LICENSE](LICENSE).
