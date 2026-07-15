#!/usr/bin/env python3
"""카드 35장을 skill-creator 기준으로 채점한다.

왜 이 네 축인가 (output/5color_card_score_20260715.md 참조)

skill-creator의 원칙 중 이 카드 형태(붙여넣는 시스템 인스트럭션)에 실제로 걸리는 것만 골랐다.

  A 금지의 일반화 (3점)
     skill-creator "make the skill general and not super-narrow to specific examples".
     SKILL.md도 같은 말을 한다. "직접 인용 금지는 문자열 하나를 막는 규칙이 아니라
     그 뒤의 행동 하나를 막는 규칙이다. (...) 괄호에 그 행동을 한 줄로 붙여 무엇을 막는지 드러낸다."
     인용문만 있으면 모델이 동의어·패러프레이즈로 일반화하지 못한다.

  B 인과 설명 (2점)
     skill-creator "Explain the why. (...) If you find yourself writing ALWAYS or NEVER
     in all caps, or using super rigid structures, that's a yellow flag."
     금지에서 '왜'는 곧 행동 규칙 줄이다. 그래서 규칙형 비율로 잰다.
     인과 접속사를 정규식으로 세는 방식은 버렸다. p32처럼 규칙형 금지를 다 갖췄는데
     접속사를 안 쓰는 카드를 부당하게 깎았다.

  C 예시 (2점)
     skill-creator "Examples pattern". 좋은 예/나쁜 예.
     주의. 35장 중 33장이 만점이라 변별력이 거의 없다. 참고치로만 본다.

  D 규격 준수 (3점)
     리포지토리 자신의 규칙. 분량(SKILL.md 출력 분량 가이드)과
     금지 개수 차등(합격선에 따른 금지 강도 차등화).

뺀 축. 자기완결성(필수 절·페르소나 5인·톤 셋)은 35/35 만점이라 정보가 0이다.
skill-creator의 analyzer가 경고하는 non-discriminating 지표라 넣지 않는다.

이 채점의 한계. 기계 측정이다. 금지 줄의 '질'을 글자수로 근사한다.
라벨이 좋은 라벨인지는 사람이 봐야 한다. 순위가 아니라 어디를 손볼지 가리키는 용도다.

사용법
  python3 scripts/score_cards.py           # 점수표
  python3 scripts/score_cards.py --detail  # 금지 줄 분류까지
"""
import json
import re
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "docs" / "index.html"

# 카드 -> references 정본 합격선. scripts/select_picks.py와 같은 출처다.
CANON = {
    "p1": "9.5", "p2": "9.5", "p3": "9.5", "p4": "9.5", "p5": "9.5", "p6": "9.7",
    "p7": "9.7", "p8": "9.7", "p9": "9.5", "p10": "9.5", "p11": "9.7", "p12": "9.5",
    "p13": "9.7", "p14": "9.7", "p15": "9.5", "p16": "9.5", "p17": "9.5", "p18": "9.5",
    "p19": "9.5", "p20": "9.5", "p21": "9.5", "p22": "9.7", "p23": "9.5", "p24": "9.5",
    "p25": "9.0", "p26": "9.5", "p27": "9.7", "p28": "9.7", "p29": "9.5", "p30": "9.5",
    "p31": "9.5", "p32": "9.5", "p33": "9.7", "p34": "9.0", "p35": "9.0",
}
# SKILL.md "합격선에 따른 금지 강도 차등화"
NEED = {"9.7": (4, 5), "9.5": (2, 3), "9.0": (1, 2)}
BAND = (3000, 5500)  # SKILL.md "출력 분량 가이드"


def strip_html(s):
    return re.sub("<.*?>", "", s)


def load():
    src = INDEX.read_text(encoding="utf-8")
    m = re.search(r"const PROMPTS = (\{.*?\});\n", src, re.S)
    if not m:
        sys.exit("PROMPTS 블록을 찾지 못했다.")
    return json.loads(m.group(1))


def tier(line):
    """금지 한 줄이 일반화 가능한가.

    quote  인용문뿐. 동의어·패러프레이즈로 넓히지 못한다.
    label  인용 + 실패 유형 이름. 짧지만 넓힐 수 있다.
    rule   인용 + 행동 + 무효 범위나 결과. SKILL.md가 요구하는 꼴.

    괄호 안 행동은 세어 준다. SKILL.md가 명시한 형태가 그것이다.
    "괄호에 그 행동을 한 줄로 붙여 무엇을 막는지 드러낸다."
    p11의 `"전략적 시너지가 크다"(정량화 없는 단정)`이 그 꼴이다.
    """
    s = ITEM_MARK.sub("", line.strip()).strip()
    rest = re.sub(r'"[^"]+"', "", s).strip(" .·")
    inner = " ".join(re.findall(r"\(([^)]+)\)", rest))   # 괄호 안 행동
    plain = re.sub(r"\([^)]*\)", "", rest).strip(" .·")  # 괄호 밖 설명
    body = (plain + " " + inner).strip()
    if len(body) < 8:
        return "quote"
    if len(body) < 28:
        return "label"
    return "rule"


# 불릿(-, *)과 번호(1. 2.) 목록을 모두 항목으로 본다.
# p11은 번호 목록만 써서, 불릿만 찾던 첫 파서가 "금지 0개"로 잘못 읽었다.
ITEM_LINE = re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+)")
ITEM_MARK = re.compile(r"^\s*(?:[-*]\s+|\d+\.\s+)")


def specific_prohibitions(full_prompt):
    m = re.search(r"## 하지 말아야 할 것[^\n]*\n(.*?)(\n## |$)", full_prompt, re.S)
    body = m.group(1) if m else ""
    sm = re.search(r"[^\n]*특화[^\n]*\n(.*?)(\n\n[^-\d\n]|$)", body, re.S)
    src = sm.group(1) if sm else body
    return [l for l in src.split("\n") if ITEM_LINE.match(l)]


def score(cid, card):
    fp = card["fullPrompt"]
    want = CANON[cid]
    lines = specific_prohibitions(fp)
    t = {"quote": 0, "label": 0, "rule": 0}
    for l in lines:
        t[tier(l)] += 1
    n = len(lines)

    a = 0.0 if n == 0 else round((t["rule"] * 1.0 + t["label"] * 0.6 + t["quote"] * 0.1) / n * 3, 1)
    b = 0.0 if n == 0 else round(min(1.0, t["rule"] / max(1, min(n, 4))) * 2, 1)
    g, bd = len(re.findall(r"좋은 예", fp)), len(re.findall(r"나쁜 예", fp))
    c = 2.0 if g >= 3 and bd >= 3 else 1.5 if g >= 2 and bd >= 2 else 1.0 if g and bd else 0.5
    lo, hi = NEED[want]
    d = (1.5 if BAND[0] <= len(fp) <= BAND[1] else 0.0) \
        + (1.5 if lo <= n <= hi else 0.5 if n and abs(n - hi) <= 2 else 0.0)
    return dict(id=cid, title=strip_html(card["title"]), tier=want, a=a, b=b, c=c, d=d,
                total=round(a + b + c + d, 1), n=n, mix=t, chars=len(fp))


def main():
    d = load()
    missing = set(d) - set(CANON)
    if missing:
        sys.exit(f"합격선 정본이 없는 카드가 있다: {sorted(missing)}")
    rows = sorted((score(k, v) for k, v in d.items()), key=lambda r: -r["total"])

    print("skill-creator 기준 4축 10점. A 금지의 일반화 3 · B 인과 설명 2 · C 예시 2 · D 규격 준수 3\n")
    print(f"{'id':4s} {'카드':22s} {'군':4s} {'A/3':4s} {'B/2':4s} {'C/2':4s} {'D/3':4s} {'총점':5s} 금지(인용/라벨/규칙)")
    print("-" * 86)
    for r in rows:
        m = r["mix"]
        print(f"{r['id']:4s} {r['title'][:21]:22s} {r['tier']:4s} "
              f"{r['a']:.1f}  {r['b']:.1f}  {r['c']:.1f}  {r['d']:.1f}  {r['total']:4.1f}   "
              f"{r['n']}개 ({m['quote']}/{m['label']}/{m['rule']})")

    vals = [r["total"] for r in rows]
    print(f"\n평균 {st.mean(vals):.2f} · 중앙값 {st.median(vals):.2f} · 최고 {max(vals)} · 최저 {min(vals)}")
    for name, key, mx in [("A 금지의 일반화", "a", 3), ("B 인과 설명", "b", 2),
                          ("C 예시", "c", 2), ("D 규격 준수", "d", 3)]:
        v = [r[key] for r in rows]
        print(f"  {name}: 평균 {st.mean(v):.2f}/{mx} ({st.mean(v)/mx*100:.0f}%)")

    tot = {"quote": 0, "label": 0, "rule": 0}
    for r in rows:
        for k2 in tot:
            tot[k2] += r["mix"][k2]
    s = sum(tot.values())
    print(f"\n금지 줄 {s}개 = 인용만 {tot['quote']} ({tot['quote']/s*100:.0f}%) / "
          f"라벨형 {tot['label']} ({tot['label']/s*100:.0f}%) / 규칙형 {tot['rule']} ({tot['rule']/s*100:.0f}%)")
    print(f"규칙형이 0개인 카드: {sum(1 for r in rows if r['mix']['rule'] == 0)}/35")

    if "--detail" in sys.argv:
        print("\n=== 금지 줄 분류 ===")
        for r in rows:
            if r["mix"]["rule"] == r["n"] and r["n"]:
                continue
            print(f"\n[{r['id']}] {r['title']} ({r['total']}점)")
            for l in specific_prohibitions(d[r["id"]]["fullPrompt"]):
                print(f"  {tier(l):6s} {l.strip()[:88]}")


if __name__ == "__main__":
    main()
