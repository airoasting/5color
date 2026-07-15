#!/usr/bin/env python3
"""에디터 픽 선정. 점수표에서 픽을 유도한다.

방법 (output/5color_pick_eval_20260715.md 참조)
  1. 게이트. O(본인성) >= 1.5 그리고 S(스테이크) >= 1.5.
     진짜 일은 본인성과 스테이크가 동시에 높은 곳에서만 발생한다.
  2. 게이트를 통과한 카드만 총점으로 줄을 세워 상위 N장을 뽑는다.
  3. EDITORIAL_PICKS를 더한다. 게이트를 못 넘었지만 편집자 판단으로 올린 카드다.
  4. 전체를 총점으로 줄 세운다. 동점이면 O+S가 높은 쪽이 앞선다.

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
# 둘 다 S(스테이크)에서 걸린다. 건당 스테이크는 낮지만 리더가 Claude에 가장 자주
# 직접 시키는 일이라는 공통점이 있다. 게이트는 "리더가 서는 방"을 찾도록 설계돼서
# 방으로 가는 입구를 못 잡는다. 이 예외는 게이트의 알려진 한계를 덮는 자리이지,
# 점수가 틀렸다는 뜻이 아니다. 점수는 그대로 둔다.
#
# 예외가 셋 이상으로 늘면 게이트가 게이트가 아니다. 그때는 예외를 늘리지 말고
# S 축 정의나 게이트 기준선을 다시 본다 (output/5color_pick_eval_20260715.md 참조).
EDITORIAL_PICKS = {
    "p1":  "리서치·자료조사. F 2.0·D 2.0으로 두 축 만점인 유일한 카드. 모든 방 앞에 오는 준비 작업이라 방 자체는 아니지만 입구다. 이게 빠지면 진열창이 드물고 극적인 장면(이사회·딜·위기)으로만 차서 방문자의 실제 화요일과 어긋난다.",
    "p33": "AI 글 자연스럽게 다듬기. F 1.9·D 1.9·W 1.9. 진입 장벽이 가장 낮고 결과가 즉시 검증된다. AI를 쓰는 리더가 상시로 겪는 문제라, 스테이크가 낮다고 진열창에서 빼면 가장 많이 쓰일 카드를 숨기는 셈이다.",
}

# 카드 id -> (F 빈도, S 스테이크, O 본인성, D AI델타, W 시연력)
# 각 축 0~2점. 채점 근거는 output/5color_pick_eval_20260715.md에 있다.
SCORES = {
    "p1":  (2.0, 1.3, 1.7, 2.0, 1.8),  # I·1 리서치·자료조사
    "p2":  (1.3, 1.7, 1.0, 1.6, 1.5),  # I·2 산업·시장 분석
    "p3":  (1.2, 1.8, 1.4, 1.8, 1.6),  # I·3 경영 이슈 진단
    "p4":  (0.9, 1.7, 1.8, 1.8, 1.3),  # I·4 내러티브 메모 (6-pager)
    "p5":  (0.6, 2.0, 1.7, 1.7, 1.5),  # I·5 연간 사업계획
    "p6":  (1.5, 2.0, 1.8, 1.7, 1.9),  # II·1 이사회 보고서
    "p7":  (1.3, 1.9, 1.6, 1.6, 1.3),  # II·2 IR·실적 발표
    "p8":  (0.9, 1.7, 1.9, 1.6, 1.5),  # II·3 주주 서한
    "p9":  (1.3, 1.6, 1.3, 1.4, 1.2),  # II·4 분기 실적 리뷰
    "p10": (1.2, 1.8, 1.0, 1.7, 1.5),  # II·5 재무 모델링
    "p11": (0.5, 2.0, 1.6, 1.8, 1.6),  # III·1 M&A 딜 메모
    "p12": (1.6, 1.7, 1.8, 1.9, 1.8),  # III·2 협상 전략 브리프
    "p13": (0.9, 1.9, 1.5, 1.6, 1.3),  # III·3 투자 검토
    "p14": (1.7, 1.8, 1.6, 1.8, 1.7),  # III·4 계약서 검토
    "p15": (1.3, 1.4, 1.4, 1.6, 1.4),  # III·5 파트너십·제휴 제안
    "p16": (1.6, 1.6, 1.1, 1.5, 1.4),  # IV·1 영업 제안서
    "p17": (1.5, 1.3, 1.0, 1.4, 1.2),  # IV·2 사업 기획안
    "p18": (2.0, 0.9, 1.9, 1.0, 1.0),  # IV·3 이메일 (외부 비즈니스)
    "p19": (1.0, 1.0, 1.0, 1.3, 1.3),  # IV·4 카피라이팅
    "p20": (0.9, 1.1, 0.9, 1.3, 1.1),  # IV·5 출시 메시지 작성
    "p21": (1.4, 1.6, 1.9, 1.7, 1.6),  # V·1 타운홀·전사 메시지
    "p22": (1.7, 1.4, 2.0, 1.7, 1.7),  # V·2 어려운 메시지 (거절 등)
    "p23": (1.9, 1.2, 1.9, 1.3, 1.3),  # V·3 정기 1 on 1
    "p24": (1.5, 1.5, 1.9, 1.6, 1.5),  # V·4 성과 평가·피드백
    "p25": (1.5, 1.3, 2.0, 1.7, 1.9),  # V·5 리더 심리 상담
    "p26": (0.5, 1.5, 1.7, 1.5, 1.4),  # V·6 비전·미션 선언문
    "p27": (0.6, 2.0, 1.9, 1.9, 1.8),  # VI·1 위기 대응 메시지
    "p28": (0.5, 1.9, 1.8, 1.7, 1.6),  # VI·2 사과문
    "p29": (1.2, 1.1, 0.9, 1.4, 1.2),  # VI·3 보도자료
    "p30": (1.4, 0.9, 1.7, 1.2, 1.2),  # VII·1 SNS 포스팅
    "p31": (0.6, 1.2, 1.8, 1.5, 1.3),  # VII·2 신문 칼럼
    "p32": (0.9, 1.0, 1.3, 1.3, 1.2),  # VII·3 뉴스레터
    "p33": (1.9, 0.9, 1.6, 1.9, 1.9),  # VII·4 AI 글 자연스럽게 다듬기
    "p34": (0.2, 0.4, 1.5, 1.4, 1.0),  # VII·5 소설 쓰기
    "p35": (0.2, 0.3, 1.5, 1.4, 0.9),  # VII·6 시 쓰기
}


def load_prompts(src):
    m = re.search(r"const PROMPTS = (\{.*?\});\n", src, re.S)
    if not m:
        sys.exit("PROMPTS 블록을 찾지 못했다.")
    return json.loads(m.group(1)), m


def strip_html(s):
    return re.sub("<.*?>", "", s)


def gate(cid, scores):
    F, S, O, D, W = scores[cid]
    return O >= GATE_O and S >= GATE_S


def rank(cid, scores):
    F, S, O, D, W = scores[cid]
    return (F + S + O + D + W, O + S)


def select(scores, n=N_PICKS):
    """게이트 통과 상위 n장 + 편집자 예외. 전체를 총점(동점이면 O+S)으로 줄 세운다."""
    passed = sorted((rank(c, scores) + (c,) for c in scores if gate(c, scores)), reverse=True)
    by_gate = passed[:n]
    editorial = [rank(c, scores) + (c,) for c in EDITORIAL_PICKS if c in scores]
    picks = sorted(by_gate + editorial, reverse=True)
    return picks, passed, by_gate


def main():
    src = INDEX.read_text(encoding="utf-8")
    prompts, m = load_prompts(src)

    missing = set(prompts) - set(SCORES)
    if missing:
        sys.exit(f"점수가 없는 카드가 있다. 채점 후 다시 돌려라: {sorted(missing)}")

    picks, passed, by_gate = select(SCORES)
    title = lambda cid: strip_html(prompts[cid]["title"])
    gate_ids = {c for _, _, c in by_gate}

    print(f"게이트 O>={GATE_O} AND S>={GATE_S} 통과: {len(passed)}장 / 전체 {len(SCORES)}장")
    print(f"선정 {len(picks)}장 = 게이트 {len(by_gate)}장 + 편집자 예외 {len(EDITORIAL_PICKS)}장\n")
    print(f"=== 선정 {len(picks)}장 (진열창 노출 순) ===")
    for i, (tot, os_, cid) in enumerate(picks, 1):
        tag = "게이트" if cid in gate_ids else "예외  "
        print(f"  {i}. [{prompts[cid]['folio']:6s}] {title(cid):22s} 총점 {tot:.1f}  O+S {os_:.1f}  {tag}  ({prompts[cid]['cat']})")

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
    all_cats = {v["cat"] for v in prompts.values()}
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
