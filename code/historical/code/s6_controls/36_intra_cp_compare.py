# -*- coding: utf-8 -*-
"""
阶段 36 —— 检验「师姐假说」：突变体的「蛋白内部 CP」与「蛋白–靶C CP」相对 WT 的偏离，
是否与实测活性保留率同序？

假说（师姐原文要点）：
  H1  132D/E 靶活性仅 5–10% 变化  → 两指标应接近 WT（偏离小）
  H2  30H / 27T-30H-58M 编辑效率降 20–30% → 两指标相对 WT 的差距应更大
  H3  但 30H 与 27T-30H-58M 之间，两指标可能差别不大

方法学（关键）：
  WT 有 20 个 seed × 5 model；突变体只有 1 seed × 5 model。
  故用「WT 的 seed 间两两差异（190 对）」构造零假设分布 = 噪声地板，
  只有超出该地板的偏离才可归因于突变本身，而非 AF3 采样噪声。

指标：
  A. 蛋白内部 CP（199×199）
     intra_lr_rmsd   长程对 |i-j|>=5 的 CP 矩阵 RMSD
     pocket_rmsd     活性口袋区(25–32,57–60,70–72,99–105,129–133)内部 CP RMSD
     prof_rmsd       逐残基长程耦合谱的 RMSD
  B. 蛋白–靶C CP（靶C = RNA resi 4 = 0 位被编辑 C）
     protC_rmsd / protC_alpha(整体缩放系数) / protC_maxabs
  C. 几何（cif，内部距离，不受 AF3 全局朝向影响）
     d_E72 / d_W99 / d_H70 = 靶C C4/N4 到该残基的最小重原子距离
  D. 实测活性保留率（湿实验）

产出：
  results/CP偏离_汇总.csv
  results/protC_cp_profile.csv
  results/figs/fig7_CP偏离_vs_活性.png
"""
import json, os, glob, csv, math, sys
sys.stdout.reconfigure(encoding="utf-8")
import af_utils as U

PROT, RNA, TARGET_C = U.PROT_CHAIN, U.RNA_CHAIN, 4
WT_DIRS = {"GCG": "GUGCGCG_20", "GCA": "GUGCACG_20"}
MUT_ROOT = "new/mut"

# (目录名, 展示名, 湿实验名候选)
VARIANTS = [
    ("m132d",         "M132D",           ["132D"]),
    ("m132e",         "M132E",           ["132E"]),
    ("k30h",          "K30H",            ["30H"]),
    ("g27tk30hq58m",  "G27T-K30H-Q58M",  ["27T-30H-58M"]),
    ("g27t",          "G27T",            ["27T"]),
    ("g27d",          "G27D",            ["27D"]),
    ("g27dk30h",      "G27D-K30H",       ["27D-30H"]),
    ("g27tk30h",      "G27T-K30H",       ["27T-30H"]),
    ("g27dk30hq58m",  "G27D-K30H-Q58M",  ["27D-30H-58M"]),
    ("k30hq58m",      "K30H-Q58M",       ["30H-58M"]),
    ("g25e",          "G25E",            ["25E"]),
    ("g25ek30h",      "G25E-K30H",       ["25E-30H"]),
    ("a59p",          "A59P",            ["59P"]),
    ("k60r",          "K60R",            ["60R"]),
]
POCKET = list(range(25, 33)) + list(range(57, 61)) + list(range(70, 73)) + \
         list(range(99, 106)) + list(range(129, 134))

# ---------------------------------------------------------------------------
# 湿实验活性
# ---------------------------------------------------------------------------
def load_activity():
    act = {}
    for r in csv.DictReader(open("results/experimental_ranking.csv", encoding="utf-8-sig")):
        try:
            act[r["mut"]] = float(r["retain"])
        except (ValueError, KeyError):
            pass
    for r in csv.DictReader(open("results/GCG_vs_off_ranking_WT.csv", encoding="utf-8-sig")):
        try:
            act.setdefault(r["mutation"], float(r["activity_retention"]))
        except (ValueError, KeyError):
            pass
    return act
ACT = load_activity()

# ---------------------------------------------------------------------------
# AF3 CP 读取
# ---------------------------------------------------------------------------
def seed_map(d):
    mats, vecs, resis = [], [], None
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids, rids, cpm = j["token_chain_ids"], j["token_res_ids"], j["contact_probs"]
        prot = [i for i in range(len(cids)) if cids[i] == PROT]
        resis = [rids[i] for i in prot]
        t = next(i for i in range(len(cids)) if cids[i] == RNA and rids[i] == TARGET_C)
        n = len(prot)
        M = [[max(cpm[prot[a]][prot[b]], cpm[prot[b]][prot[a]]) for b in range(n)] for a in range(n)]
        v = [max(cpm[prot[a]][t], cpm[t][prot[a]]) for a in range(n)]
        mats.append(M); vecs.append(v)
    k = len(mats); n = len(mats[0])
    M = [[sum(m[i][j] for m in mats) / k for j in range(n)] for i in range(n)]
    v = [sum(x[i] for x in vecs) / k for i in range(n)]
    return M, v, resis

def rmsd(xs, ys):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(xs, ys)) / len(xs))

def profile(M, n, minsep=5):
    return [sum(M[i][j] for j in range(n) if abs(i - j) >= minsep) /
            max(1, len([j for j in range(n) if abs(i - j) >= minsep])) for i in range(n)]

def cp_metrics(Ma, va, Mb, vb, resis):
    n = len(resis)
    lr = [(i, j) for i in range(n) for j in range(i + 5, n)]
    pa = [resis.index(r) for r in POCKET if r in resis]
    pk = [(i, j) for i in pa for j in pa if i < j]
    d = [abs(a - b) for a, b in zip(va, vb)]
    num = sum(a * b for a, b in zip(va, vb)); den = sum(b * b for b in vb)
    return dict(
        intra_lr_rmsd=rmsd([Ma[i][j] for i, j in lr], [Mb[i][j] for i, j in lr]),
        pocket_rmsd=rmsd([Ma[i][j] for i, j in pk], [Mb[i][j] for i, j in pk]),
        prof_rmsd=rmsd(profile(Ma, n), profile(Mb, n)),
        protC_rmsd=rmsd(va, vb),
        protC_alpha=(num / den if den > 0 else float("nan")),
        protC_maxabs=max(d), protC_argmax=resis[d.index(max(d))],
    )

# ---------------------------------------------------------------------------
# 几何（cif）
# ---------------------------------------------------------------------------
def geom(d):
    out = {"d_E72": [], "d_W99": [], "d_H70": []}
    for f in sorted(glob.glob(os.path.join(d, "*model_*.cif"))):
        _, rows = U.parse_atom_site(f)
        tc = U.atoms_of(rows, "B", resid=TARGET_C, names={"C4", "N4"})
        if not tc:
            tc = U.atoms_of(rows, "B", resid=TARGET_C)
        for k, resi, names in [("d_E72", 72, {"OE1", "OE2"}),
                               ("d_W99", 99, None), ("d_H70", 70, {"NE2", "ND1"})]:
            x = U.min_dist(tc, U.atoms_of(rows, "A", resid=resi, names=names))
            if x is not None:
                out[k].append(x)
    med = lambda v: sorted(v)[len(v) // 2] if v else float("nan")
    return {k: med(v) for k, v in out.items()}, out["d_E72"]

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def run(sub):
    root = WT_DIRS[sub]
    seeds = []
    for d in sorted(x for x in glob.glob(os.path.join(root, "*")) if os.path.isdir(x)):
        try:
            M, v, resis = seed_map(d)
        except Exception:
            continue
        if len(resis) == 199:
            seeds.append((M, v, resis))
    resis = seeds[0][2]
    null = [cp_metrics(seeds[i][0], seeds[i][1], seeds[j][0], seeds[j][1], resis)
            for i in range(len(seeds)) for j in range(i + 1, len(seeds))]

    def ns(k):
        vals = [x[k] for x in null if isinstance(x[k], float) and not math.isnan(x[k])]
        m = sum(vals) / len(vals)
        sd = math.sqrt(sum((a - m) ** 2 for a in vals) / (len(vals) - 1))
        return m, sd, min(vals), max(vals)

    rows = []
    for key, name, wetnames in VARIANTS:
        d = os.path.join(MUT_ROOT, f"{key}_{sub.lower()}")
        if not os.path.isdir(d):
            continue
        Mv, vv, _ = seed_map(d)
        ms = [cp_metrics(Mv, vv, Mw, vw, resis) for Mw, vw, _ in seeds]
        avg = {k: (sum(x[k] for x in ms) / len(ms) if isinstance(ms[0][k], float)
                   else max(set(x[k] for x in ms), key=[x[k] for x in ms].count))
               for k in ms[0]}
        g, dall = geom(d)
        act = next((ACT[w] for w in wetnames if w in ACT), None)
        rows.append(dict(substrate=sub, variant=name, **avg, **g, _v=vv,
                         d_E72_models=dall, activity=act,
                         z_protC=(avg["protC_rmsd"] - ns("protC_rmsd")[0]) / ns("protC_rmsd")[1],
                         z_intra=(avg["intra_lr_rmsd"] - ns("intra_lr_rmsd")[0]) / ns("intra_lr_rmsd")[1],
                         z_pocket=(avg["pocket_rmsd"] - ns("pocket_rmsd")[0]) / ns("pocket_rmsd")[1]))
    return dict(sub=sub, seeds=seeds, resis=resis, null=null, ns=ns, rows=rows)

print("=" * 112)
print("阶段 36 —— 蛋白内部 CP / 蛋白–靶C CP 的突变体偏离，与实测活性的关系")
print("=" * 112)
ALL = {s: run(s) for s in ["GCG", "GCA"]}

# ---------------- 零假设 ----------------
for s in ["GCG", "GCA"]:
    D = ALL[s]
    print(f"\n【{s}】零假设：WT seed 间两两差异（n={len(D['null'])} 对）= 噪声地板")
    print(f"{'指标':<18}{'均值':>10}{'SD':>10}{'最小':>10}{'最大':>10}")
    for k in ["intra_lr_rmsd", "pocket_rmsd", "prof_rmsd", "protC_rmsd", "protC_alpha", "protC_maxabs"]:
        m, sd, lo, hi = D["ns"](k)
        print(f"{k:<18}{m:>10.5f}{sd:>10.5f}{lo:>10.5f}{hi:>10.5f}")

# ---------------- 主表 ----------------
for s in ["GCG", "GCA"]:
    D = ALL[s]
    print("\n" + "=" * 112)
    print(f"【{s}】突变体 vs WT（z = 偏离噪声地板的 SD 数；z>3 视为超出噪声）")
    print("=" * 112)
    print(f"{'突变体':<18}{'内部CP':>9}{'z':>7}{'口袋CP':>9}{'z':>7}{'靶C-CP':>9}{'z':>7}"
          f"{'缩放α':>8}{'靶C最大Δ':>9}{'d_E72':>8}{'d_W99':>8}{'活性保留':>9}")
    order = ["M132D", "M132E", "K30H", "G27T-K30H-Q58M", "G27T", "G27D",
             "G27D-K30H", "K30H-Q58M", "G25E", "G25E-K30H", "A59P", "K60R",
             "G27T-K30H", "G27D-K30H-Q58M"]
    for name in order:
        r = next((x for x in D["rows"] if x["variant"] == name), None)
        if not r:
            continue
        a = f"{r['activity']:.2f}" if r["activity"] is not None else "—"
        print(f"{name:<18}{r['intra_lr_rmsd']:>9.5f}{r['z_intra']:>+7.1f}"
              f"{r['pocket_rmsd']:>9.5f}{r['z_pocket']:>+7.1f}"
              f"{r['protC_rmsd']:>9.5f}{r['z_protC']:>+7.1f}"
              f"{r['protC_alpha']:>8.3f}{r['protC_maxabs']:>9.3f}"
              f"{r['d_E72']:>8.2f}{r['d_W99']:>8.2f}{a:>9}")

# ---------------- 相关分析 ----------------
def pearson(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs); syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")

print("\n" + "=" * 112)
print("偏离指标 vs 实测活性保留率（仅取有实测值的变体）")
print("=" * 112)
for s in ["GCG", "GCA"]:
    D = ALL[s]
    rr = [r for r in D["rows"] if r["activity"] is not None]
    if len(rr) < 4:
        print(f"【{s}】可用变体不足（n={len(rr)}），跳过"); continue
    acts = [r["activity"] for r in rr]
    print(f"\n【{s}】n = {len(rr)}：{', '.join(r['variant'] for r in rr)}")
    for k, lab in [("protC_rmsd", "蛋白–靶C CP 偏离"), ("intra_lr_rmsd", "蛋白内部 CP 偏离"),
                   ("pocket_rmsd", "口袋内部 CP 偏离"), ("d_E72", "靶C–E72 距离(G)")]:
        xs = [r[k] for r in rr]
        print(f"  {lab:<22} r = {pearson(xs, acts):+.3f}")

# ---------------- 导出 ----------------
with open("results/CP偏离_汇总.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["substrate", "variant", "intra_lr_rmsd", "z_intra", "pocket_rmsd", "z_pocket",
                "prof_rmsd", "protC_rmsd", "z_protC", "protC_alpha", "protC_maxabs", "protC_argmax",
                "d_E72", "d_W99", "d_H70", "activity_retention"])
    for s in ["GCG", "GCA"]:
        for r in sorted(ALL[s]["rows"], key=lambda x: -x["protC_rmsd"]):
            w.writerow([s, r["variant"], round(r["intra_lr_rmsd"], 5), round(r["z_intra"], 2),
                        round(r["pocket_rmsd"], 5), round(r["z_pocket"], 2), round(r["prof_rmsd"], 5),
                        round(r["protC_rmsd"], 5), round(r["z_protC"], 2), round(r["protC_alpha"], 4),
                        round(r["protC_maxabs"], 4), r["protC_argmax"],
                        round(r["d_E72"], 3), round(r["d_W99"], 3), round(r["d_H70"], 3),
                        "" if r["activity"] is None else round(r["activity"], 4)])
# 零假设摘要
with open("results/CP偏离_零假设.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["substrate", "metric", "null_mean", "null_sd", "null_min", "null_max", "n_pairs"])
    for s in ["GCG", "GCA"]:
        for k in ["intra_lr_rmsd", "pocket_rmsd", "prof_rmsd", "protC_rmsd", "protC_alpha", "protC_maxabs"]:
            m, sd, lo, hi = ALL[s]["ns"](k)
            w.writerow([s, k, round(m, 5), round(sd, 5), round(lo, 5), round(hi, 5), len(ALL[s]["null"])])

# 蛋白–靶C 全谱
wt_v = {s: [sum(v[i] for _, v, _ in ALL[s]["seeds"]) / len(ALL[s]["seeds"]) for i in range(199)]
        for s in ["GCG", "GCA"]}
with open("results/protC_cp_profile.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    names = [n for _, n, _ in VARIANTS]
    w.writerow(["substrate", "resi", "WT"] + names)
    for s in ["GCG", "GCA"]:
        vm = {r["variant"]: r for r in ALL[s]["rows"]}
        for i, resi in enumerate(ALL[s]["resis"]):
            w.writerow([s, resi, round(wt_v[s][i], 5)] +
                       [round(vm[n]["_v"][i], 5) if n in vm else "" for n in names])

print("\n写入 results/CP偏离_汇总.csv / CP偏离_零假设.csv / protC_cp_profile.csv")
