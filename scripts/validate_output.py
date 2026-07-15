#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""5-Color Harness 출력 자체 점검 중 기계 판정 가능한 항목을 검사한다.

왜 스크립트인가. 아래 열은 결정적인 문자열·수 검사라 매 회차 모델이 눈으로 다시 볼 이유가 없다.
특히 em dash의 수 범위 예외(6~10 같은 자리는 위반이 아니다)는 사람이 매번 판정하면 실수가 잦다.
판단이 필요한 항목(페르소나 정체성, 합격선 장면의 구체성, 종결 체가 작업 영역에 맞는지)은
여기서 다루지 않는다. 그건 SKILL.md의 자체 점검 표가 맡는다.

사용법.
    python3 scripts/validate_output.py output.md
    cat output.md | python3 scripts/validate_output.py -
종료 코드. 위반 0건이면 0, 있으면 1.
"""
import re, sys

TONE_POOL = ['건조','단정','신랄','차분','깐깐','냉정','회의적','무뚝뚝','속내 드러냄','실무자 직설']
TAIL_NOTE = "위 마크다운을 새 클로드 프로젝트의 지침 박스에 붙여 넣어 사용하세요"


def prose_em_dash(text):
    """산문 em dash만 잡는다. 수 사이 범위(6–10)와 규칙 인용은 위반이 아니다."""
    t = re.sub(r'em dash\([^)]*\)', '', text)     # 규칙이 문자를 인용한 자리
    t = re.sub(r'`[—–]`', '', t)
    t = re.sub(r'(?<=\d)\s*[—–]\s*(?=\d)', '', t)  # 수 범위
    return [m.start() for m in re.finditer(r'[—–]', t)]


def fenced_block(text):
    m = re.search(r'````+\s*markdown\s*\n(.*?)\n````+', text, re.S)
    return m.group(1) if m else None


SHAPE_SECTIONS = r'출력 포맷|출력 템플릿|출력 양식|보고 양식|인용 규칙|인용 형식'


def lines_outside_output_format(block):
    """산출물의 생김새를 규정하는 절을 뺀 줄만 돌려준다.

    그 절의 대괄호는 BLACK이 런타임에 채우는 슬롯이라 '미치환'이 아니다.
    예. 출력 포맷의 `[도입 단락]`, 인용 규칙의 `[지표] [수치] ([출처], [시점])`.
    이 검사가 잡으려는 것은 SKILL.md 출력 템플릿의 `[작업 영역명]`처럼
    스킬이 채웠어야 할 자리가 빈 채로 나간 경우다. 둘을 갈라야 검사가 옳은 것을 잡는다.
    """
    out, skip = [], False
    for ln in block.split('\n'):
        if ln.startswith('#'):
            skip = bool(re.search(SHAPE_SECTIONS, ln))
        if not skip:
            out.append(ln)
    return out


def check(text):
    v = []
    block = fenced_block(text)

    # 1. 코드펜스
    if block is None:
        v.append('코드펜스 누락. 산출물 전체를 ````markdown 한 묶음으로 감싸야 사용자가 통째로 복사한다.')
        block = text

    # 2. 산문 em dash 0개 (자동 fail)
    hits = prose_em_dash(block)
    if hits:
        v.append(f'산문 em dash {len(hits)}개. 자동 fail. 마침표·쉼표·괄호·콜론 중 하나로 교체한다.')

    # 3. 브래킷 잔존
    #    잡으려는 것은 SKILL.md 출력 템플릿의 [브래킷]이 안 채워진 채 나간 자리다.
    #    카드가 자기 목적으로 쓰는 대괄호는 위반이 아니다. 셋을 면책한다.
    #    (1) 출력 포맷 절의 슬롯. BLACK이 런타임에 채울 자리다. [도입 단락], [제목: ...] 같은 꼴.
    #    (2) 색 라벨. [BLACK], [BLUE] 같은 발화자 표기.
    #    (3) 금지 조항이 인용한 대괄호. "대괄호 [ ] 표기 금지"가 자기 자신에게 걸리면 안 된다.
    #    em dash 검사가 규칙 인용을 면책하는 것과 같은 원리다.
    left = []
    for ln in lines_outside_output_format(block):
        if re.search(r'금지|쓰지 않는다|않는다|안 쓴다', ln):
            continue
        for x in re.findall(r'\[[^\]\n]{1,40}\]', ln):
            if re.match(r'\[(미확인|출처|\d+)\]', x):
                continue
            if re.match(r'\[(BLACK|RED|SILVER|BLUE|GOLD)\]', x):
                continue
            left.append(x)
    if left:
        v.append(f'[브래킷] 미치환 {len(left)}개: {", ".join(left[:5])}')

    # 4. 분량 (3000~5500자). 근거는 SKILL.md "출력 분량 가이드".
    #    2026-07-15에 1500~3500에서 옮겼다. 옛 기준은 실측이 아니라 추정이었고
    #    카드 35장 중 28장이 위반했다. 실측 분포는 3043~5221 연속에 6956 하나가 이상치다.
    n = len(block)
    if not (3000 <= n <= 5500):
        why = '5인 페르소나·워크플로우·점수 기준·문체·금지가 다 들어가지 못해 평가 레이어가 작동하지 않는다' if n < 3000 \
              else '이 선을 넘으면 같은 말을 두 자리에서 반복하고 있을 가능성이 높다. 중복부터 찾는다'
        v.append(f'분량 {n}자. 3000~5500자를 벗어났다. {why}.')

    # 5. 끝줄 안내 (코드펜스 바깥)
    outside = text.replace(block, '') if block in text else text
    if TAIL_NOTE not in outside:
        v.append('끝줄 안내 문구 누락. 코드펜스 바깥에 붙여야 사용자가 어디 붙일지 한 번 더 묻지 않는다.')

    # 6. 비평가 발화 톤 셋 중복
    tones = {}
    for color in ('RED','SILVER','BLUE'):
        m = re.search(r'^\s*[-*]\s*'+color+r'\b[^\n]*?\(([^)]{1,14})\)\s*[:：]', block, re.M)
        if m and any(p in m.group(1) for p in TONE_POOL):
            tones[color] = m.group(1).strip()
    if len(tones) < 3:
        v.append(f'비평가 발화 톤 미표기 {3-len(tones)}개. RED·SILVER·BLUE 각자에게 한 단어를 붙인다.')
    elif len(set(tones.values())) < 3:
        v.append(f'비평가 발화 톤 중복: {tones}. 셋은 서로 다른 단어여야 사고 모드가 갈린다.')

    # 7. 자평·메타 코멘트
    #    금지 조항이 인용한 자리는 위반이 아니다. 카드가 '"어떠신가요" 같은 마무리는 붙이지 않는다'라고
    #    적은 것을 잡으면, 검사를 통과하려고 금지 조항을 지우게 된다. 규칙과 위반을 뒤집는 검사가 된다.
    for bad in ('어떠신가요','어떠세요','도움이 되셨','참고하시기 바랍니다'):
        for ln in block.split('\n'):
            if bad in ln and not re.search(r'금지|않는다|말라|안 붙|삭제', ln):
                v.append(f'자평·메타 코멘트 "{bad}". 블록 안에서 삭제한다.')
                break

    # 8. 본 스킬 내부 어휘·구조 유출
    #    산출물은 사용자가 클로드 프로젝트 지침 박스에 붙여 넣는 자기완결 문서다.
    #    그 문서 안에는 본 스킬도, 카드 카탈로그도, 형제 카드도 없다. 오직 이 한 장뿐이다.
    #    그래서 다음 셋은 실행하는 모델이 따를 수 없는 지시가 된다.
    #      (1) 분류 어휘. "9.0군", "9.7 영역", "보정군". 붙여 넣는 사람은 들어본 적이 없다.
    #          필요한 건 분류명이 아니라 "(합격선 9.0)"이라는 값과 왜 그 선인지의 근거다.
    #      (2) 캐스팅 근거. "직접 인용 8개", "정량 강제가 작가 톤을 깎기 때문이다".
    #          본 스킬이 캐스팅을 정한 이유이지 그 지침을 실행하는 모델에게 주는 지시가 아니다.
    #      (3) 카탈로그 색인. "p28 사과문으로 넘긴다", "형제 카드로 넘긴다".
    #          붙여 넣은 프로젝트에 p28은 없다. 사용자는 "p28이 뭔데?"라고 묻게 된다.
    #          라우팅 의도는 살리되 번호는 걷는다. "사과문으로 넘긴다"면 이름만으로 통한다.
    #    korean 스킬이 내부 코드 키 L3·L2를 화면에 노출하지 말라고 못 박은 것과 같은 자리다.
    for pat, why in (
        # \b를 붙이면 안 된다. 한글은 \w라서 "9.5군이라"의 군과 이 사이에 단어 경계가 없다.
        # 넓히려다 원래 잡던 것을 놓친다. "(합격선 9.7)"에는 군·영역이 없으므로 오탐도 없다.
        (r'9\.\d\s*(?:군|영역)', '본 스킬의 분류 어휘다. 합격선 값과 그 근거만 남긴다'),
        (r'보정군', '본 스킬의 분류 어휘다'),
        (r'\d+개 절제|둘로 절제한다|정량 강제가', '캐스팅 근거를 산출물에 적었다. 실행 지시만 남긴다'),
        (r'직접 인용 \d+개|특화 금지 \d+개', '금지 개수는 본 스킬의 체크리스트다. 산출물에는 금지 자체만 적는다'),
        (r'\bp\d+\s+[가-힣]', '카드 카탈로그 색인이다. 붙여 넣은 프로젝트에 그 번호는 없다'),
        (r'형제 카드', '카탈로그 구조다. 자기완결 문서에 형제는 없다'),
    ):
        hit = re.search(pat, block)
        if hit:
            v.append(f'내부 어휘 유출 "{hit.group(0).strip()}". {why}.')

    # 9. 다른 카드로 넘기는 지시 ("적용하지 않는 경우" 절 한정)
    #    산출물은 개별 프롬프트로 혼자 돈다. 넘길 대상이 없으므로 "X로 넘긴다"는 실행하는
    #    모델이 수행할 수 없는 동작이다. 사용자는 "그래서 어디로?"라고 묻게 된다.
    #    범위 밖이면 넘기는 게 아니라 시작하지 않는다. 출력 템플릿의 "적용하지 않는 경우"가
    #    그렇게 쓰여 있다. "다음 신호가 들어오면 작업을 시작하지 않는다."
    #
    #    이 절로 좁히는 이유. 산출물 전체에서 "넘긴다"를 찾으면 오탐이 쏟아진다. GOLD의
    #    마무리 패턴 "다음 문단으로 넘긴다"는 독자가 글을 읽는 행동이지 라우팅이 아니다.
    #    라우팅 버그는 이 절에만 산다.
    #    단, 전문의·1393·HR/법무처럼 현실의 사람에게 넘기는 것은 실제로 수행 가능하다.
    REAL_HANDOFF = r'전문의|1393|HR·법무|법무 절차|전문 기관|외부 PR 자문|사람 검수|전문가'
    scope = block.split('## 적용하지 않는 경우')
    if len(scope) > 1:
        for ln in scope[-1].split('\n'):
            if re.search(r'(?:으로|로)\s*(?:넘긴다|보낸다|넘깁니다)', ln) and not re.search(REAL_HANDOFF, ln):
                v.append(f'다른 카드로 넘기는 지시. "{ln.strip()[:38]}". 개별 프롬프트라 넘길 대상이 없다. '
                         f'범위 밖이면 넘기는 게 아니라 시작하지 않는다.')
                break

    # 10. 재작업 트리거 산술
    #     트리거는 합격선에서 0.3 아래다. 이 뺄셈을 사람이 매번 눈으로 하면 틀린다.
    #     실제로 9.0군 카드가 "(합격선 - 0.3) 미만, 즉 9.2 미만"으로 나갔다. 9.0-0.3은 8.7이다.
    #     한 카드를 고치다 두 자리 중 한 자리만 고쳐 카드 안에서 숫자가 갈리는 일도 있었다.
    #     공식을 적어 놓고 숫자를 틀리면 읽는 모델은 숫자를 따른다. 그래서 숫자를 검사한다.
    #     합격선 표기는 카드마다 꼴이 다르다. "(합격선 9.7)", "합격선 9.7에 닿을",
    #     "합격선은 9.7이다", "합격선을 9.7로 둔다". 괄호형만 찾으면 나머지를 놓쳐
    #     기본값 9.5로 잘못 계산한다. 여러 꼴을 모아 가장 많이 나온 값을 합격선으로 본다.
    cand = [float(x) for x in re.findall(r'합격선[^\n]{0,8}?(\d\.\d)', block)]
    if cand:
        pass_line = max(set(cand), key=cand.count)
    else:
        pass_line = 9.5                              # 표기가 없으면 9.5가 기본값이다
    want = round(pass_line - 0.3, 1)
    found = set()
    for ln in block.split('\n'):
        if not re.search(r'트리거|v2를 만들|v2 질의|v2를 한 번', ln):
            continue
        for x in re.findall(r'(\d\.\d)\s*(?:점\s*)?미만', ln):
            # 5 미만은 점수가 아니라 차이값이다. "합격선 9.5에서 0.3 미만으로 떨어진 경우"의
            # 0.3을 트리거 점수로 읽으면 안 된다. 트리거는 언제나 8~10 사이에 있다.
            if float(x) >= 5:
                found.add(float(x))
    # 합격선 자체를 트리거로 쓰는 카드가 있다(보도자료. "미달이면 전부 v2, 사각지대를 두지
    # 않는다"고 명시). 그건 의도된 설계라 위반이 아니다.
    off = sorted(x for x in found if abs(x - want) > 0.01 and abs(x - pass_line) > 0.01)
    if off:
        v.append(f'재작업 트리거 {off}. 합격선 {pass_line}이면 {want} 미만이어야 한다. '
                 f'한 카드 안에서 숫자가 갈리면 읽는 모델이 어느 쪽을 따를지 모른다.')
    return v


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else '-'
    text = sys.stdin.read() if src == '-' else open(src, encoding='utf-8').read()
    v = check(text)
    if not v:
        print('통과. 기계 검사 10종 위반 0건.')
        return 0
    print(f'위반 {len(v)}건. SKILL.md 복구 우선순위 표대로 위에서부터 손본다.\n')
    for i, x in enumerate(v, 1):
        print(f'{i}. {x}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
