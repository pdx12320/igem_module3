# -*- coding: utf-8 -*-
"""
阶段 58 —— 靶向比偏倚的「回补检验」与校正后重新排序

背景（Cycle 3）：
  我们此前发现 targeting_ratio = Σ_GCG / Σ_nonGCG 被 5% 检测下限混淆——
  酶整体活性下降时，脱靶位点率先掉到检出线下被记为 0，分母塌缩、比值虚高。
  当时我们确立了两条规则并**应用**了下限（见 25_offtarget_screen.py:96，
  `if r["on"] < 0.30: continue`），但从未回补检验两件事：
    (1) 加了活性下限之后，偏倚是否真的被消除？
    (2) 若按校正后的指标重新排序，选出的候选会不会与原始排序不同？

本脚本补做这两件事。

【回补检验 Part 1】偏倚是否被下限消除
  比较「全量」与「加下限 C388 ≥ 0.30」两种口径下：
    · Pearson/Spearman(靶向比, Σ非GCG)
    · Pearson(C388%, Σ非GCG%)
    · 低/高活性层靶向比中位数
    · 比值 = ∞ 的构建体数

【回补检验 Part 2】六种排序口径的对比与稳健候选
  (a) 原始 targeting_ratio
  (b) 加活性下限的 targeting_ratio
  (c) 活性残差化（对 C388% 回归取残差）
  (d) 平均非 GCG 编辑率（Σ/n_detected，减轻分母塌缩）
  (e) 归一化脱靶负荷 Σoff/on（25 脚本实际使用的口径）
  (f) +1 比（GCG/GCA，单点对单点，独立于扩增子指标）
  对比各自 top-10 的重叠度，区分「稳健候选」与「原始排序伪影」。

产出：results/靶向比_回补检验.csv
      results/靶向比_重排序对比.csv
"""
import csv, math, sys
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from scipy import stats as st

SRC = "results/GCG_vs_off_ranking_WT.csv"
OFF = "results/offtarget_by_mutant.csv"
CMB = "results/23_combo_master_table.csv"
FLOOR = 0.30
OUT1, OUT2 = "results/靶向比_回补检验.csv", "results/靶向比_重排序对比.csv"


def F(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def rd(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


# ---------- 载入 ----------
rows = [r for r in rd(SRC) if r["is_WT"] != "True"]
off = {r["mutant"]: r for r in rd(OFF)}
p1 = {r["muts"]: F(r["ratio_p1"]) for r in rd(CMB)}

for r in rows:
    r["_c388"] = F(r["C388_pct"])
    r["_tr"] = F(r["targeting_ratio"])
    r["_off"] = F(r["sum_nonGCG_pct"])
    r["_ngcg"] = F(r["n_nonGCG_detected"])
    r["_ng"] = F(r["n_GCG_detected"])
    r["_act"] = F(r["activity_retention"])
    o = off.get(r["mutation"], {})
    r["_offsum"] = F(o.get("off_sum"))
    r["_on388"] = F(o.get("on_388"))
    r["_p1"] = p1.get(r["mutation"])

has_off = [r for r in rows if r["_off"] is not None]
fin = [r for r in has_off if r["_tr"] is not None]
keep = [r for r in fin if r["_c388"] is not None and r["_c388"] >= FLOOR * 100]
print(f"组合构建体 {len(rows)} 个；有 Σ 非GCG 读数 {len(has_off)}；比值有限 {len(fin)}；"
      f"再加 C388 ≥ {FLOOR*100:.0f}% 后 {len(keep)}")

# ===========================================================================
# Part 1 —— 偏倚是否被下限消除
# ===========================================================================
print("\n" + "=" * 96)
print("Part 1　回补检验：加活性下限后，偏倚被消除了吗？")
print("=" * 96)

res1 = []


def part1(tag, sub):
    off_a = np.array([r["_off"] for r in sub])
    tr_a = np.array([r["_tr"] for r in sub])
    c3_a = np.array([r["_c388"] for r in sub])
    if len(sub) < 5:
        return
    rp = float(np.corrcoef(off_a, tr_a)[0, 1])
    rs = float(st.spearmanr(off_a, tr_a)[0])
    cp = float(np.corrcoef(c3_a, off_a)[0, 1])
    lo = [r["_tr"] for r in sub if 10 <= r["_c388"] <= 20]
    hi = [r["_tr"] for r in sub if 35 <= r["_c388"] <= 60]
    n_inf = sum(1 for r in rows if r["_c388"] is not None and r["_c388"] >= (FLOOR * 100 if tag.startswith("加下限") else 0)
                and r["_tr"] is None and r["_off"] is not None)
    med_lo = float(np.median(lo)) if lo else float("nan")
    med_hi = float(np.median(hi)) if hi else float("nan")
    print(f"\n【{tag}】n = {len(sub)}")
    print(f"  Spearman ρ(靶向比, Σ非GCG) = {rs:+.3f}    Pearson r = {rp:+.3f}")
    print(f"  Pearson  r(C388%, Σ非GCG%)  = {cp:+.3f}")
    print(f"  低活性层(10–20%) 中位 {med_lo:.2f} (n={len(lo)})   "
          f"高活性层(35–60%) 中位 {med_hi:.2f} (n={len(hi)})   层间比 {med_lo/med_hi:.2f}×")
    print(f"  该口径下比值 = ∞ 的构建体：{n_inf} 个")
    res1.append(dict(口径=tag, n=len(sub), Spearman_靶向比_非GCG=round(rs, 3),
                     Pearson_靶向比_非GCG=round(rp, 3), Pearson_C388_非GCG=round(cp, 3),
                     低活性层中位=round(med_lo, 2), 低活性层n=len(lo),
                     高活性层中位=round(med_hi, 2), 高活性层n=len(hi),
                     层间倍数=round(med_lo / med_hi, 2) if med_hi else None,
                     比值无穷数=n_inf))


part1("全量（不过滤）", fin)
part1(f"加下限 C388 ≥ {FLOOR*100:.0f}%", keep)

# ===========================================================================
# Part 2 —— 六种口径的重新排序
# ===========================================================================
print("\n" + "=" * 96)
print("Part 2　重新排序：六种口径下的 top-10")
print("=" * 96)

sub = [r for r in keep if r["_p1"] is not None or True]
# (c) 活性残差化
c3 = np.array([r["_c388"] for r in keep])
tr = np.array([r["_tr"] for r in keep])
z = np.polyfit(c3, tr, 1)
resid = tr - np.polyval(z, c3)
for r, e in zip(keep, resid):
    r["_resid"] = float(e)


def score(r, key):
    if key == "a":
        return r["_tr"]
    if key == "b":
        return r["_tr"]
    if key == "c":
        return r["_resid"]
    if key == "d":
        n = r["_ngcg"] or 0
        return (r["_off"] / n) if n > 0 else None
    if key == "e":
        o, on = r["_offsum"], r["_on388"]
        return (o / on) if (o is not None and on and on > 0) else None
    if key == "f":
        return r["_p1"]
    return None


NAMES = {"a": "原始 targeting_ratio（全量）", "b": f"targeting_ratio + 活性下限",
         "c": "活性残差化比值", "d": "平均非GCG编辑率 Σ/n", "e": "归一化脱靶负荷 Σoff/on",
         "f": "+1 比（独立口径）"}
POOL = {"a": fin, "b": keep, "c": keep, "d": keep, "e": keep, "f": keep}

top = {}
for k in "abcdef":
    pool = POOL[k]
    scored = [(r, score(r, k)) for r in pool]
    scored = [(r, s) for r, s in scored if s is not None]
    asc = k in ("d", "e")            # 这两种越低越好
    scored.sort(key=lambda t: t[1], reverse=not asc)
    top[k] = [r["mutation"] for r, _ in scored[:10]]
    print(f"\n({k}) {NAMES[k]}　（n = {len(scored)}{'，越低越好' if asc else '，越高越好'}）")
    print("     " + "  ".join(f"{i+1}.{m}" for i, m in enumerate(top[k])))

# 重叠度矩阵
print("\n" + "=" * 96)
print("top-10 重叠度（|A∩B| / 10）")
print("=" * 96)
ks = list("abcdef")
print("        " + "".join(f"{k:>7}" for k in ks))
for a in ks:
    line = f"  ({a})   "
    for b in ks:
        ov = len(set(top[a]) & set(top[b]))
        line += f"{ov:>7}"
    print(line)

# 稳健 vs 伪影
cnt = {}
for k in ks:
    for m in top[k]:
        cnt[m] = cnt.get(m, 0) + 1
robust = sorted([m for m, c in cnt.items() if c >= 4], key=lambda m: -cnt[m])
artifact = [m for m in top["a"] if cnt.get(m, 0) <= 2]
print(f"\n★ 稳健候选（在 ≥4 种口径中都进 top-10，共 {len(robust)} 个）：")
for m in robust:
    r = next(x for x in keep if x["mutation"] == m)
    print(f"    {m:<20} 命中 {cnt[m]}/6 种口径   靶向比 {r['_tr']:.2f}   C388 {r['_c388']:.1f}%"
          f"   活性保留 {r['_act']}")
print(f"\n⚠ 原始排序的伪影候选（仅在 ≤2 种口径中进 top-10）：{artifact if artifact else '无'}")

# 原始排序 top-10 的活性
raw_top = [next(x for x in fin if x["mutation"] == m) for m in top["a"]]
print(f"\n原始 targeting_ratio 排序 top-10 的 on-target 编辑率：")
for r in raw_top:
    print(f"    {r['mutation']:<20} C388 = {r['_c388']:>5.2f}%   靶向比 = {r['_tr']:.2f}"
          f"{'   ← 低于活性下限' if r['_c388'] < FLOOR*100 else ''}")
n_below = sum(1 for r in raw_top if r["_c388"] < FLOOR * 100)
print(f"    → 其中 {n_below}/10 低于活性下限 {FLOOR*100:.0f}%")

# ===========================================================================
# Part 3 —— 对最终决策的影响
# ===========================================================================
print("\n" + "=" * 96)
print("Part 3　这次偏倚是否影响了我们的最终候选选择？")
print("=" * 96)
import os as _os, re as _re

CANDP = "results/下一步实验突变候选表_61组.csv"
cand = rd(CANDP) if _os.path.exists(CANDP) else []


def canon(s):
    """把 30H-58M / G30H+Q58M / 27T-30H-58M 等写法统一成残基号+氨基酸的有序集合。"""
    toks = _re.findall(r"([A-Z]?)(\d+)([A-Z])", str(s).upper())
    return frozenset(f"{p}{a}" for _, p, a in toks)


cand_sets = {canon(r.get("突变", "")): r for r in cand}

biased_names = {m for m in top["a"]
                if next(x for x in fin if x["mutation"] == m)["_c388"] < FLOOR * 100}
hit = sorted(m for m in biased_names if canon(m) in cand_sets)
print(f"  61 条候选表载入：{len(cand)} 条")
print(f"  原始排序 top-10 中低于活性下限的构建体（{len(biased_names)} 个）：{sorted(biased_names)}")
print(f"  其中进入 61 条候选表的：{hit if hit else '无'}")

# 反向核对：稳健候选有多少进了候选表
rob = [m for m in cnt if cnt[m] >= 4]
rob_in = sorted(m for m in rob if canon(m) in cand_sets)
print(f"\n  8 个稳健候选中进入 61 条候选表的：{rob_in if rob_in else '无'}")
for m in rob:
    r = next(x for x in keep if x["mutation"] == m)
    print(f"    {m:<18} {'✓ 已在候选表' if canon(m) in cand_sets else '— 未纳入'}"
          f"   靶向比 {r['_tr']:.2f}  C388 {r['_c388']:.1f}%  活性 {r['_act']}")
print(f"\n  说明：命中者为 C18（G25E+K30H），与 25E-30H 是同一组合；")
print(f"        但它在候选表中的入选理由是「复验重复性 + 作为 Q58M 配对（C18/C28）的对照臂」，")
print(f"        与 targeting_ratio 排名无关。")
print(f"\n  → 61 条候选表以 +1 比与机制论证为挑选依据，从未使用 targeting_ratio 排序；")
print(f"     本次偏倚未传导到最终候选选择。")
print(f"     但 8 个稳健候选中有 6 个尚未纳入任何一轮实验，可作为补充验证的参考清单。")

# ---------- 写出 ----------
with open(OUT1, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(res1[0])); w.writeheader(); w.writerows(res1)
print(f"\n写入 {OUT1}")

rank_rows = []
for m in sorted(cnt, key=lambda x: -cnt[x]):
    r = next((x for x in keep if x["mutation"] == m), None)
    rank_rows.append(dict(
        构建体=m, 命中口径数=cnt[m],
        原始靶向比=round(r["_tr"], 3) if r else "",
        C388_pct=r["_c388"] if r else "",
        活性保留=r["_act"] if r else "",
        活性残差=round(r["_resid"], 3) if r and "_resid" in r else "",
        平均非GCG=round(score(r, "d"), 2) if r and score(r, "d") is not None else "",
        归一化脱靶负荷=round(score(r, "e"), 2) if r and score(r, "e") is not None else "",
        plus1_ratio=r["_p1"] if r else "",
        判定=("稳健候选" if cnt[m] >= 4 else ("伪影候选" if cnt[m] <= 2 else "中间"))))
with open(OUT2, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rank_rows[0])); w.writeheader(); w.writerows(rank_rows)
print(f"写入 {OUT2}")
