#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""5-Color Harness 출력 자체 점검 중 기계 판정 가능한 항목을 검사한다.

왜 스크립트인가. 아래 여섯은 결정적인 문자열·수 검사라 매 회차 모델이 눈으로 다시 볼 이유가 없다.
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
    left = re.findall(r'\[[^\]\n]{1,40}\]', block)
    left = [x for x in left if not re.match(r'\[(미확인|출처|\d+)\]', x)]
    if left:
        v.append(f'[브래킷] 미치환 {len(left)}개: {", ".join(left[:5])}')

    # 4. 분량 밴드 (1500~3500자)
    n = len(block)
    if not (1500 <= n <= 3500):
        why = '페르소나·문체·금지 디테일이 부족해 평가 레이어가 작동하지 않는다' if n < 1500 \
              else '사용자가 지침 박스에 붙일 때 압도된다'
        v.append(f'분량 {n}자. 1500~3500자 밴드를 벗어났다. {why}.')

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
    for bad in ('어떠신가요','어떠세요','도움이 되셨','참고하시기 바랍니다'):
        if bad in block:
            v.append(f'자평·메타 코멘트 "{bad}". 블록 안에서 삭제한다.')
    return v


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else '-'
    text = sys.stdin.read() if src == '-' else open(src, encoding='utf-8').read()
    v = check(text)
    if not v:
        print('통과. 기계 검사 7종 위반 0건.')
        return 0
    print(f'위반 {len(v)}건. SKILL.md 복구 우선순위 표대로 위에서부터 손본다.\n')
    for i, x in enumerate(v, 1):
        print(f'{i}. {x}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
