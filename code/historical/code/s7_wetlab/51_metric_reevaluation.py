# -*- coding: utf-8 -*-
"""
阶段 51 —— 用 top-5 / top-10 回收率重新评价此前所有方法

背景（Peng et al. 2026 Mol Cell 的启示）：
  此前一律用 Pearson / Spearman 评价预测方法，结论是「全部失败」。
  但真正决定实用价值的是「能不能把最好的几个排进前几名」——即 top-N 回收率。
  本脚本对每个方法同时给出：Pearson、Spearman、NDCG@10、top-5 回收、top-10 回收，
  并用置换检验给出 top-N 回收率的经验 p 值（小样本下 top-N 的方差很大，必须做检验）。

被评价的方法：
  mCSM-NA      results/mcsm_single_rerank.csv        （score = combined）
  PremPRI      results/prempri_single_rerank.csv     （score = score）
  Δd_E72       results/dE72_regression.csv           （score = delta_d_E72，假设越大越好）
  加性先验模型  results/23_pair_score_matrix.csv       （score = theory）
  CP / ΔCP     results/mut_cp_summary_保G排A.csv      （score = 排A指数 − 保G指数）

产出：results/方法重评价_topN.csv
"""
import csv, sys, math, re, json
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np

# ---------------------------------------------------------------------------
# 指标
# ---------------------------------------------------------------------------
def pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x - x.mean(); y = y - y.mean()
    d = math.sqrt((x ** 2).sum() * (y ** 2).sum())
    return float((x * y).sum() / d) if d > 0 else float("nan")


def spearman(x, y):
    def rk(v):
        s = np.argsort(np.asarray(v, float)); r = np.empty(len(v))
        r[s] = np.arange(len(v)); return r
    return pearson(rk(x), rk(y))


def ndcg_at(y_true, y_pred, k):
    yt = np.asarray(y_true, float)
    if np.ptp(yt) <= 0: return float("nan")
    yt = (yt - yt.min()) / np.ptp(yt)
    k = min(k, len(yt))
    order = np.argsort(-np.asarray(y_pred, float))[:k]
    ideal = np.argsort(-yt)[:k]
    disc = 1.0 / np.log2(np.arange(2, k + 2))
    idcg = float((yt[ideal] * disc).sum())
    return float((yt[order] * disc).sum()) / idcg if idcg > 0 else float("nan")


def topn_recovery(y_true, y_pred, n):
    yt = np.asarray(y_true, float)
    n = min(n, len(yt))
    a = set(np.argsort(-np.asarray(y_pred, float))[:n])
    b = set(np.argsort(-yt)[:n])
    return len(a & b) / n


def exact_topn_p(n, k, m):
    """精确超几何 p 值：从 n 个里随机挑 k 个，与真实 top-k 的重叠 >= m 的概率。"""
    from math import comb
    if k > n: return float("nan")
    tot = comb(n, k)
    p = sum(comb(k, j) * comb(n - k, k - j) for j in range(m, k + 1)
            if 0 <= k - j <= n - k)
    return p / tot


def evaluate(score, outcome, n_perm=5000, seed=0):
    """返回指标字典。top-N 回收率用精确超几何 p 值（置换只能给近似，且小样本下不稳）。
    护栏：n < 10 不报 top-5（组合数太少，无区分力）；n < 15 不报 top-10。"""
    s = np.asarray(score, float); o = np.asarray(outcome, float)
    m = np.isfinite(s) & np.isfinite(o)
    s, o = s[m], o[m]
    n = len(s)
    if n < 6:
        return None
    out = dict(n=n, pearson=pearson(s, o), spearman=spearman(s, o),
               ndcg10=ndcg_at(o, s, 10) if n >= 15 else float("nan"),
               top5=float("nan"), top5_p=float("nan"), top5_note="",
               top10=float("nan"), top10_p=float("nan"), top10_note="")
    if n >= 10:
        m5 = int(round(topn_recovery(o, s, 5) * 5))
        out.update(top5=m5 / 5, top5_p=exact_topn_p(n, 5, m5))
    else:
        out["top5_note"] = f"n={n}<10，组合数仅 {comb_n(n,5)} 种，无区分力"
    if n >= 15:
        m10 = int(round(topn_recovery(o, s, 10) * 10))
        out.update(top10=m10 / 10, top10_p=exact_topn_p(n, 10, m10))
    else:
        out["top10_note"] = f"n={n}<15，不报 top-10"
    return out


def comb_n(n, k):
    from math import comb
    return comb(n, k) if k <= n else 0


# ---------------------------------------------------------------------------
# 实测结果
# ---------------------------------------------------------------------------
single = {}
for r in csv.DictReader(open("results/experimental_ranking.csv", encoding="utf-8-sig")):
    try:
        single[r["mut"]] = dict(ratio=float(r["ratio"]), retain=float(r["retain"]),
                                active=r["active"] == "True")
    except ValueError:
        pass
combo = {}
for r in csv.DictReader(open("results/GCG_vs_off_ranking_WT.csv", encoding="utf-8-sig")):
    try:
        tr = float(r["targeting_ratio"])
    except Exception:
        continue
    combo[r["mutation"]] = dict(tr=tr, act=float(r["activity_retention"] or 0),
                                finite=not math.isinf(tr))
print(f"实测单点 {len(single)} 个；实测组合 {len(combo)} 个")


def wet_key(name):
    """M132D -> 132D ; G25E -> 25E ; 27T-30H -> 27T-30H ; g27tk30hq58m -> 27T-30H-58M"""
    if not name: return None
    s = str(name)
    if s.upper().startswith("WT") or "PUF12-9" in s: return None
    if "-" in s and re.match(r"^\d", s) and len(s.split("-")) > 1 and not re.match(r"^[A-Z]\d+[A-Z]$", s.split("-")[0]):
        return s                                     # 已是 27T-30H 形式
    if re.match(r"^[A-Z]\d+[A-Z]$", s):
        m = re.match(r"^([A-Z])(\d+)([A-Z])$", s); return f"{m.group(2)}{m.group(3)}"
    # 小写连写形式 g27tk30hq58m
    parts = re.findall(r"([a-z])(\d+)([a-z])", s.lower())
    if parts:
        return "-".join(f"{p}{a.upper()}" for _, p, a in parts).replace("-", "-") \
               if False else "-".join(f"{int(p)}{a.upper()}" for _, p, a in parts)
    return None


def combo_key(name):
    """把各种组合写法统一成 27T-30H-58M 形式。"""
    if not name: return None
    s = str(name).strip()
    if s.upper().startswith("WT") or "PUF12-9" in s: return None
    parts = re.split(r"[+\-]", s)
    out = []
    for p in parts:
        p = p.strip()
        m = re.match(r"^([A-Z])(\d+)([A-Z])$", p)
        if m: out.append(f"{m.group(2)}{m.group(3)}"); continue
        m = re.match(r"^(\d+)([A-Z])$", p)
        if m: out.append(f"{m.group(1)}{m.group(2)}")
    return "-".join(out) if out else None


# ---------------------------------------------------------------------------
# 逐方法评价
# ---------------------------------------------------------------------------
RES = []


def record(method, scope, score_name, score, names, keyfn, outcome_name, outcome_map, getter):
    pts = []
    for nm, sc in zip(names, score):
        k = keyfn(nm)
        if k is None or k not in outcome_map: continue
        v = getter(outcome_map[k])
        if v is None: continue
        pts.append((float(sc), float(v)))
    if len(pts) < 6:
        print(f"  [跳过] {method} / {outcome_name}：可比样本仅 {len(pts)} 个")
        return
    s, o = zip(*pts)
    e = evaluate(s, o)
    e.update(method=method, scope=scope, score=score_name,
             outcome=outcome_name, matched=len(pts))
    RES.append(e)
    def fmt(v, p):
        if not np.isfinite(v): return "   —    "
        return f"{v:.2f}" + ("★" if np.isfinite(p) and p <= 0.05 else " ") + f"(p={p:.3f})"
    print(f"  {method:<14}{outcome_name:<14}n={e['n']:<3} "
          f"r={e['pearson']:+.3f} ρ={e['spearman']:+.3f}  "
          f"top5={fmt(e['top5'], e['top5_p']):<14}top10={fmt(e['top10'], e['top10_p'])}")


print("\n" + "=" * 116)
print("一、mCSM-NA（单点，score = combined）")
print("=" * 116)
rows = list(csv.DictReader(open("results/mcsm_single_rerank.csv", encoding="utf-8-sig")))
nm = [r["mut"] for r in rows]; sc = [r["combined"] for r in rows]
record("mCSM-NA", "单点", "combined", sc, nm, wet_key, "+1比（特异性）", single, lambda d: d["ratio"])
record("mCSM-NA", "单点", "combined", sc, nm, wet_key, "活性保留", single, lambda d: d["retain"])
# 子分单独评价：综合分可能把有信号的子分压掉
record("mCSM-swap子分", "单点", "score_swap", [r["score_swap"] for r in rows], nm, wet_key,
       "+1比（特异性）", single, lambda d: d["ratio"])
record("mCSM-off子分", "单点", "score_off", [r["score_off"] for r in rows], nm, wet_key,
       "+1比（特异性）", single, lambda d: d["ratio"])
# 去掉标记 unreliable 的（RSA=0，工具本身说不可信）
rel = [r for r in rows if r["unreliable"] == "False"]
print(f"  去掉 unreliable 后剩 {len(rel)} 个")
record("mCSM-NA(仅可信)", "单点", "combined", [r["combined"] for r in rel], [r["mut"] for r in rel],
       wet_key, "+1比（特异性）", single, lambda d: d["ratio"])

print("\n" + "=" * 116)
print("二、PremPRI（单点，score = score）")
print("=" * 116)
rows = list(csv.DictReader(open("results/prempri_single_rerank.csv", encoding="utf-8-sig")))
nm = [r["mut"] for r in rows]; sc = [r["score"] for r in rows]
record("PremPRI", "单点", "score", sc, nm, wet_key, "+1比（特异性）", single, lambda d: d["ratio"])
record("PremPRI", "单点", "score", sc, nm, wet_key, "活性保留", single, lambda d: d["retain"])
record("PremPRI-swap子分", "单点", "score_swap", [r["score_swap"] for r in rows], nm, wet_key,
       "+1比（特异性）", single, lambda d: d["ratio"])
record("PremPRI-off子分", "单点", "score_off", [r["score_off"] for r in rows], nm, wet_key,
       "+1比（特异性）", single, lambda d: d["ratio"])

print("\n" + "=" * 116)
print("三、Δd_E72（几何指标；假设越大越好）")
print("=" * 116)
rows = list(csv.DictReader(open("results/dE72_regression.csv", encoding="utf-8-sig")))
nm = [r["mut"] for r in rows]; sc = [r["delta_d_E72"] for r in rows]
_d72meas = {r["mut"]: float(r["measured_ratio"]) for r in rows if r["measured_ratio"].strip()}
print(f"  文件自带配对实测 +1比：{len(_d72meas)} 个")
record("Δd_E72", "单点+组合", "delta_d_E72", sc, nm, lambda x: x, "实测 +1比（配对）", _d72meas, lambda d: d)
record("Δd_E72", "单点+组合", "delta_d_E72", sc, nm, wet_key, "活性保留", single, lambda d: d["retain"])
# 反向，用于核对方向是否判反
record("Δd_E72(反向)", "单点+组合", "-delta_d_E72", [-float(x) for x in sc], nm, wet_key,
       "+1比（特异性）", single, lambda d: d["ratio"])

print("\n" + "=" * 116)
print("四、加性先验模型（位点对，score = theory）")
print("=" * 116)
rows = list(csv.DictReader(open("results/23_pair_score_matrix.csv", encoding="utf-8-sig")))
nm = [r["mutA"] + "+" + r["mutB"] for r in rows]
sc = [r["theory"] for r in rows]
meas = {combo_key(r["measured_src"]): float(r["measured"]) for r in rows
        if r.get("measured") and r.get("measured_src")}
print(f"  表内实测对 {len(meas)} 个")
record("加性先验", "组合", "theory", sc, nm, combo_key, "实测 +1比", meas, lambda d: d)

print("\n" + "=" * 116)
print("五、CP / ΔCP（score = 排A指数 − 保G指数，越大越好）")
print("=" * 116)
rows = list(csv.DictReader(open("results/mut_cp_summary_保G排A.csv", encoding="utf-8-sig")))
nm, sc = [], []
for r in rows:
    bg = r["保G指数(H29+K30 ΔCP均值)"]; pa = r["排A指数(催化核心 ΔCP均值)"]
    nm.append(list(r.values())[0]); sc.append(float(pa) - float(bg))
record("CP/ΔCP", "单点+组合", "排A−保G", sc, nm, wet_key, "+1比（特异性）", single, lambda d: d["ratio"])
record("CP/ΔCP", "单点+组合", "排A−保G", sc, nm, wet_key, "活性保留", single, lambda d: d["retain"])
record("CP/ΔCP(反向)", "单点+组合", "保G−排A", [-float(x) for x in sc], nm, wet_key,
       "+1比（特异性）", single, lambda d: d["ratio"])

# ---------------------------------------------------------------------------
# 汇总表
# ---------------------------------------------------------------------------
print("\n" + "=" * 116)
print("汇总（★ = top-N 回收率置换 p ≤ 0.05）")
print("=" * 116)
print(f"{'方法':<16}{'评价对象':<16}{'n':>4}{'Pearson':>9}{'Spearman':>10}"
      f"{'top5':>8}{'p':>8}{'top10':>8}{'p':>8}")
for e in RES:
    t5 = f"{e['top5']:.2f}" if np.isfinite(e['top5']) else "—"
    t10 = f"{e['top10']:.2f}" if np.isfinite(e['top10']) else "—"
    p5 = f"{e['top5_p']:.3f}" if np.isfinite(e['top5_p']) else "—"
    p10 = f"{e['top10_p']:.3f}" if np.isfinite(e['top10_p']) else "—"
    print(f"{e['method']:<16}{e['outcome']:<16}{e['n']:>4}{e['pearson']:>+9.3f}"
          f"{e['spearman']:>+10.3f}{t5:>8}{p5:>8}{t10:>8}{p10:>8}")

with open("results/方法重评价_topN.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["method", "scope", "score_column", "outcome", "n_matched",
                "pearson", "spearman", "ndcg@10",
                "top5_recovery", "top5_exact_p", "top5_note",
                "top10_recovery", "top10_exact_p", "top10_note"])
    for e in RES:
        w.writerow([e["method"], e["scope"], e["score"], e["outcome"], e["n"],
                    round(e["pearson"], 4), round(e["spearman"], 4), round(e["ndcg10"], 4),
                    "" if not np.isfinite(e["top5"]) else round(e["top5"], 3),
                    "" if not np.isfinite(e["top5_p"]) else round(e["top5_p"], 4),
                    e.get("top5_note", ""),
                    "" if not np.isfinite(e["top10"]) else round(e["top10"], 3),
                    "" if not np.isfinite(e["top10_p"]) else round(e["top10_p"], 4),
                    e.get("top10_note", "")])
print("\n写入 results/方法重评价_topN.csv")
