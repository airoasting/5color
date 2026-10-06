#!/usr/bin/env python3
"""에디터 픽 선정. 점수표에서 픽을 유도한다.

방법 (output/5color_pick_eval_20260715.md, output/5color_worker_eval_20261006.md 참조)

2026-10-06에 채점 관점을 바꿨다. 전에는 C레벨 한 사람의 눈으로 쟀고, 그래서 쓰는 사람이
회사에 한두 명뿐인 이사회 보고서가 1위가 됐다. 지금은 그 문서를 실제로 쓰는 사람
(사원부터 CEO까지) 기준으로 잰다. 다섯 축의 뜻은 같고 주어만 바뀐다.
  F 빈도   작성자가 그 문서를 얼마나 자주 직접 쓰는가
  O 본인성 작성자가 남에게 못 맡기고 직접 붙잡는가
  1. 게이트. O(본인성) >= 1.5 그리고 S(스테이크) >= 1.5.
     진짜 일은 본인성과 스테이크가 동시에 높은 곳에서만 발생한다.
  2. 게이트를 통과한 카드만 총점으로 줄을 세워 상위 N장을 뽑는다.
  3. EDITORIAL_PICKS를 더한다. 게이트를 못 넘었지만 편집자 판단으로 올린 카드다.

점수는 '어느 카드를 픽할지'만 정한다. '어떤 순서로 보일지'는 카드 번호가 정한다.
전에는 진열창을 총점 순으로 깔았는데, 그 순위는 화면에 안 보이고 카드 번호만
06 -> 12 -> 01처럼 헝클어져 보였다. 읽는 사람이 못 읽는 정보를 심어봐야
번호의 예측 가능성만 잃는다. 번호는 카드 고유값이라(docs/index.html의 order + 1)
필터를 바꿔도 따라 움직이지 않는다. 오름차순이 가장 읽기 쉽다.

손으로 index.html의 pick 필드를 고치지 않는다. 이 파일을 고치고 다시 돌린다.
점수를 원하는 결과가 나오게 조정하지 않는다. 점수는 관찰이고, 예외는 예외로 적는다.

사용법
  python3 scripts/select_picks.py           # 선정 결과만 출력
  python3 scripts/select_picks.py --apply   # docs/index.html에 반영
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "index.html"

N_PICKS = 5
GATE_O = 1.5
GATE_S = 1.5

# 게이트를 못 넘었지만 편집자 판단으로 픽에 올린 카드. 사유를 반드시 적는다.
#
# 둘 다 S(스테이크)에서 걸린다. 건당 스테이크는 낮지만 직장인이 Claude에 가장 자주
# 직접 시키는 일이라는 공통점이 있다. 게이트는 "틀리면 손해가 큰 자리"를 찾도록 설계돼서
# 방으로 가는 입구를 못 잡는다. 이 예외는 게이트의 알려진 한계를 덮는 자리이지,
# 점수가 틀렸다는 뜻이 아니다. 점수는 그대로 둔다.
#
# 예외가 셋 이상으로 늘면 게이트가 게이트가 아니다. 그때는 예외를 늘리지 말고
# S 축 정의나 게이트 기준선을 다시 본다 (output/5color_pick_eval_20260715.md 참조).
EDITORIAL_PICKS = {
    "p1":  "리서치·자료조사. F 2.0·D 2.0으로 두 축 만점인 유일한 카드. 모든 방 앞에 오는 준비 작업이라 방 자체는 아니지만 입구다. 이게 빠지면 진열창이 결재와 협상 같은 무거운 장면으로만 차서 방문자의 실제 화요일과 어긋난다.",
    "p33": "AI 글 자연스럽게 다듬기. F 1.9·D 1.9·W 1.9. 진입 장벽이 가장 낮고 결과가 즉시 검증된다. AI를 쓰는 직장인이 상시로 겪는 문제라, 스테이크가 낮다고 진열창에서 빼면 가장 많이 쓰일 카드를 숨기는 셈이다.",
}

# 카드 id -> (F 빈도, S 스테이크, O 본인성, D AI델타, W 시연력)
# 각 축 0~2점. 2026-10-06 작성자 기준으로 진열대 카드를 다시 채점했다.
# 전문 직군 서랍 카드는 픽 후보가 아니라 7월 점수를 그대로 둔다.
SCORES = {
    # 보고·기획
    "p1":  (2.0, 1.3, 1.7, 2.0, 1.8),  # 리서치·자료조사
    "p4":  (1.9, 1.4, 1.7, 1.7, 1.8),  # 1페이지 보고서
    "p36": (2.0, 1.0, 1.8, 1.4, 1.6),  # 주간 업무보고
    "p6":  (1.8, 1.8, 1.7, 1.7, 1.8),  # 의사결정 요청 보고서
    "p3":  (1.4, 1.7, 1.5, 1.8, 1.5),  # 문제 해결 보고서
    "p9":  (1.8, 1.4, 1.5, 1.5, 1.4),  # 월간·분기 실적 보고
    "p17": (1.8, 1.7, 1.8, 1.6, 1.6),  # 사업 기획안
    "p5":  (0.8, 2.0, 1.8, 1.7, 1.5),  # 연간 사업계획
    # 메일·사내 소통
    "p18": (2.0, 1.0, 1.9, 1.2, 1.4),  # 메일 쓰기
    "p37": (1.8, 1.1, 1.4, 1.6, 1.6),  # 회의록
    "p38": (1.2, 1.3, 1.5, 1.5, 1.4),  # 사내 공지
    "p22": (1.7, 1.6, 2.0, 1.7, 1.7),  # 어려운 메시지 (거절·탈락·종료)
    "p28": (1.2, 1.5, 1.8, 1.6, 1.5),  # 경위서
    # 팀 운영
    "p23": (1.9, 1.2, 1.9, 1.3, 1.3),  # 정기 1 on 1
    "p24": (1.6, 1.6, 1.9, 1.6, 1.6),  # 성과 평가·피드백 (자기평가 포함)
    "p21": (1.3, 1.6, 1.9, 1.7, 1.6),  # 전사·팀 메시지
    "p25": (1.5, 1.3, 2.0, 1.7, 1.9),  # 리더 심리 상담
    # 제안·협상
    "p16": (1.4, 1.6, 1.7, 1.5, 1.4),  # 영업·제휴 제안서
    "p12": (1.6, 1.7, 1.8, 1.9, 1.8),  # 협상 전략 브리프
    "p14": (1.4, 1.8, 1.5, 1.8, 1.6),  # 계약서 검토 (1차 검토)
    # 마케팅·홍보
    "p19": (1.0, 1.0, 1.0, 1.3, 1.3),  # 카피라이팅·출시 메시지
    "p29": (1.2, 1.1, 0.9, 1.4, 1.2),  # 보도자료
    # 글쓰기·브랜딩
    "p33": (1.9, 0.9, 1.6, 1.9, 1.9),  # AI 글 자연스럽게 다듬기
    "p30": (1.4, 0.9, 1.7, 1.2, 1.2),  # SNS·링크드인 포스팅
    "p32": (0.9, 1.0, 1.3, 1.3, 1.2),  # 뉴스레터
    "p34": (0.2, 0.4, 1.5, 1.4, 1.0),  # 소설 쓰기
    "p35": (0.2, 0.3, 1.5, 1.4, 0.9),  # 시 쓰기
    # 전문 직군 (서랍, 픽 후보 아님)
    "p7":  (1.3, 1.9, 1.6, 1.6, 1.3),  # IR·실적 발표
    "p8":  (0.9, 1.7, 1.9, 1.6, 1.5),  # 주주 서한
    "p10": (1.2, 1.8, 1.0, 1.7, 1.5),  # 재무 모델링
    "p11": (0.5, 2.0, 1.6, 1.8, 1.6),  # M&A 딜 메모
    "p13": (0.9, 1.9, 1.5, 1.6, 1.3),  # 투자 검토
    "p26": (0.5, 1.5, 1.7, 1.5, 1.4),  # 비전·미션 선언문
    "p27": (0.6, 2.0, 1.9, 1.9, 1.8),  # 위기 대응 메시지
    "p31": (0.6, 1.2, 1.8, 1.5, 1.3),  # 신문 칼럼
}


def load_prompts(src):
    m = re.search(r"const PROMPTS = (\{.*?\});\n", src, re.S)
    if not m:
        sys.exit("PROMPTS 블록을 찾지 못했다.")
    return json.loads(m.group(1)), m


def strip_html(s):
    return re.sub("<.*?>", "", s)


# 카드 id -> order. main()이 docs/index.html에서 채운다.
ORDER = {}

# 진열대 밖 서랍. 쓰는 사람이 직군 몇 명뿐인 카드라 픽 후보에서 뺀다.
DRAWER_CAT = "전문 직군"


def card_number(cid):
    """카드에 찍히는 번호. docs/index.html이 order + 1을 두 자리로 찍는다.

    2026-10-06에 카드를 합치고 서랍으로 옮기면서 id 숫자와 화면 번호가 갈렸다.
    그래서 id가 아니라 order에서 읽는다.
    """
    return ORDER[cid] + 1


def gate(cid, scores):
    F, S, O, D, W = scores[cid]
    return O >= GATE_O and S >= GATE_S


def rank(cid, scores):
    F, S, O, D, W = scores[cid]
    return (F + S + O + D + W, O + S)


def select(scores, n=N_PICKS):
    """뽑기는 점수로, 줄 세우기는 카드 번호로.

    반환하는 picks는 카드 번호(order) 오름차순이다. 진열창에 그대로 깔린다.
    """
    passed = sorted((rank(c, scores) + (c,) for c in scores if gate(c, scores)), reverse=True)
    by_gate = passed[:n]
    editorial = [rank(c, scores) + (c,) for c in EDITORIAL_PICKS if c in scores]
    picks = sorted(by_gate + editorial, key=lambda r: card_number(r[2]))
    return picks, passed, by_gate


def main():
    src = INDEX.read_text(encoding="utf-8")
    prompts, m = load_prompts(src)

    missing = set(prompts) - set(SCORES)
    if missing:
        sys.exit(f"점수가 없는 카드가 있다. 채점 후 다시 돌려라: {sorted(missing)}")
    stale = set(SCORES) - set(prompts)
    if stale:
        sys.exit(f"카드에 없는 점수가 있다. SCORES에서 지워라: {sorted(stale)}")

    ORDER.update({k: v["order"] for k, v in prompts.items()})
    shelf = {k: v for k, v in SCORES.items() if prompts[k]["cat"] != DRAWER_CAT}
    picks, passed, by_gate = select(shelf)
    title = lambda cid: strip_html(prompts[cid]["title"])
    gate_ids = {c for _, _, c in by_gate}

    print(f"게이트 O>={GATE_O} AND S>={GATE_S} 통과: {len(passed)}장 / 전체 {len(SCORES)}장")
    print(f"선정 {len(picks)}장 = 게이트 {len(by_gate)}장 + 편집자 예외 {len(EDITORIAL_PICKS)}장\n")
    print(f"=== 선정 {len(picks)}장 (진열창 노출 순 = 카드 번호 오름차순) ===")
    for tot, os_, cid in picks:
        tag = "게이트" if cid in gate_ids else "예외  "
        num = f"{card_number(cid):02d}"
        print(f"  {num}  [{prompts[cid]['folio']:6s}] {title(cid):22s} 총점 {tot:.1f}  O+S {os_:.1f}  {tag}  ({prompts[cid]['cat']})")

    if EDITORIAL_PICKS:
        print(f"\n=== 편집자 예외 사유 ===")
        for cid, why in EDITORIAL_PICKS.items():
            F, S, O, D, W = SCORES[cid]
            miss = ", ".join(f"{k} {v} 미달" for k, v in (("O", O), ("S", S)) if v < (GATE_O if k == "O" else GATE_S))
            print(f"  [{prompts[cid]['folio']}] {title(cid)} ({miss})")
            print(f"     {why}")

    print(f"\n=== 게이트는 통과했으나 총점에서 밀림 ===")
    for tot, os_, cid in passed[len(by_gate):]:
        print(f"     [{prompts[cid]['folio']:6s}] {title(cid):22s} 총점 {tot:.1f}  O+S {os_:.1f}")

    print(f"\n=== 게이트 탈락 중 총점 8.0 이상 (예외로 올리지 않은 것) ===")
    for cid, (F, S, O, D, W) in SCORES.items():
        tot = F + S + O + D + W
        if not gate(cid, SCORES) and tot >= 8.0 and cid not in EDITORIAL_PICKS:
            why = [f"{k} {v} 미달" for k, v in (("O", O), ("S", S)) if v < (GATE_O if k == "O" else GATE_S)]
            print(f"     [{prompts[cid]['folio']:6s}] {title(cid):22s} 총점 {tot:.1f}  <- {', '.join(why)}")

    covered = {prompts[cid]["cat"] for _, _, cid in picks}
    all_cats = {v["cat"] for v in prompts.values() if v["cat"] != DRAWER_CAT}
    print(f"\n카테고리 커버: {len(covered)}/{len(all_cats)}")
    for c in sorted(all_cats - covered):
        print(f"     픽 없음: {c}")

    if "--apply" not in sys.argv:
        print("\n(반영하려면 --apply)")
        return

    before = {k for k, v in prompts.items() if v.get("pick")}
    for v in prompts.values():
        v.pop("pick", None)
        v.pop("pickOrder", None)
    for i, (_, _, cid) in enumerate(picks, 1):
        prompts[cid]["pick"] = True
        prompts[cid]["pickOrder"] = i

    after = {cid for _, _, cid in picks}
    new = json.dumps(prompts, ensure_ascii=False, separators=(",", ":"))
    INDEX.write_text(src[: m.start(1)] + new + src[m.end(1) :], encoding="utf-8")

    print(f"\n반영 완료. {INDEX.relative_to(ROOT)}")
    if before - after:
        print("  내림:", ", ".join(title(c) for c in sorted(before - after)))
    if after - before:
        print("  올림:", ", ".join(title(c) for c in sorted(after - before)))
    if before & after:
        print("  유지:", ", ".join(title(c) for c in sorted(before & after)))


if __name__ == "__main__":
    main()
