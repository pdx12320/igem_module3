# -*- coding: utf-8 -*-
"""
阶段 43 —— 把「完全失活阴性对照」并入偏离诊断（36）与 PCA（38），重做一次

核心问题：
  CP 类特征能否识别「完全失活」突变体？
  若不能，且失活组的偏离反而更大，则说明该指标读到的是「突变了哪个保守位点」，而非功能后果。

核心判据（决定性）：
  T31A（活性 0.97）与 T31D（活性 0.000）——同为位点 31、同为单点替换。
  若两者 CP 偏离相近 → 指标对功能无分辨力（已由 36 的保守性混杂 r=+0.85 预言）。

数据来源：
  WT             GUGCGCG_20/ , GUGCACG_20/            （20 seed × 5 model）
  既有突变体      new/mut/**                          （1 seed × 5 model）
  阴性对照        new/negctrl/**                      （5 seed × 5 model，脚本 42 生成的作业）

产出：
  results/阴性对照_偏离与PCA.csv
  results/figs/fig12_阴性对照_偏离诊断.png
  results/figs/fig13_阴性对照_PCA.png
"""
import json, glob, os, sys, math, csv
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import af_utils as U

PROT, RNA, TARGET_C = U.PROT_CHAIN, U.RNA_CHAIN, 4
N_MODEL_PER_SEED = 5
POCKET = list(range(25, 33)) + list(range(57, 61)) + list(range(70, 73)) + \
         list(range(99, 106)) + list(range(129, 134))
WT_SEQ = json.load(open("af3_submit/WT_GCG.json", encoding="utf-8"))[0]["sequences"][0]["proteinChain"]["sequence"]

# ---------------------------------------------------------------- 构建体登记
# 既有突变体：(GCG 目录, GCA 目录, 展示名, 湿实验键)
EXISTING = []
for key, disp in [("a59p", "A59P"), ("g25e", "G25E"), ("g25ek30h", "G25E-K30H"),
                  ("g27d", "G27D"), ("g27dk30h", "G27D-K30H"),
                  ("g27dk30hq58m", "G27D-K30H-Q58M"), ("g27t", "G27T"),
                  ("g27tk30h", "G27T-K30H"), ("g27tk30hq58m", "G27T-K30H-Q58M"),
                  ("k30h", "K30H"), ("k30hq58m", "K30H-Q58M"), ("k60r", "K60R"),
                  ("m132d", "M132D"), ("m132e", "M132E")]:
    EXISTING.append((f"new/mut/{key}_gcg", f"new/mut/{key}_gca", disp, None))
F16 = "new/mut/folds_2026_09_08_16_18"
for key, disp in [("q58m", "Q58M"), ("r28a", "R28A"), ("r28s", "R28S"),
                  ("t31i", "T31I"), ("t31l", "T31L"), ("t31v", "T31V"), ("y32f", "Y32F")]:
    EXISTING.append((f"{F16}/{key}_gcg", f"{F16}/{key}_gca", disp, None))

# 阴性对照面板：突变 -> (展示名, 湿实验活性, 类别)
NEG_PANEL = {
    (31, "D"): ("T31D", 0.000, "完全失活"),
    (57, "W"): ("N57W", 0.000, "完全失活"),
    (27, "D", 130, "G"): ("G27D-M130G", 0.000, "完全失活"),
    (31, "A"): ("T31A", 0.970, "★同位点活性对照"),
    (57, "A"): ("N57A", None, "新失活对照（未测）"),
    (72, "A"): ("E72A", None, "新失活对照（未测）"),
}

# ---------------------------------------------------------------- 湿实验活性
ACT = {}
for r in csv.DictReader(open("results/experimental_ranking.csv", encoding="utf-8-sig")):
    try: ACT[r["mut"]] = float(r["retain"])
    except ValueError: pass
for r in csv.DictReader(open("results/GCG_vs_off_ranking_WT.csv", encoding="utf-8-sig")):
    try: ACT.setdefault(r["mutation"], float(r["activity_retention"]))
    except ValueError: pass

def wet_key_of(disp):
    """G27D-M130G -> 27D-130G；A59P -> 59P；M132D -> 132D"""
    import re
    parts = disp.split("-")
    out = []
    for p in parts:
        m = re.match(r"([A-Z])(\d+)([A-Z])$", p)
        out.append(f"{m.group(2)}{m.group(3)}" if m else p)
    return "-".join(out)

def classify(a):
    if a is None: return "未测"
    if a <= 0.15: return "完全失活"
    if a < 0.50: return "部分失活"
    return "有活性"

# ---------------------------------------------------------------- 读 AF3
def load_seed(d):
    mats, vecs = [], []
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids, rids = j["token_chain_ids"], j["token_res_ids"]
        cpm = np.asarray(j["contact_probs"], dtype=np.float64)
        idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
        t = next(i for i in range(len(cids)) if cids[i] == RNA and rids[i] == TARGET_C)
        sub = cpm[np.ix_(idx, idx)]
        mats.append(np.maximum(sub, sub.T))
        vecs.append(np.maximum(cpm[idx, t], cpm[t, idx]))
    if not mats: return None, None
    return np.mean(mats, axis=0), np.mean(vecs, axis=0)

def geom(d):
    ds = []
    for f in sorted(glob.glob(os.path.join(d, "*model_*.cif"))):
        _, rows = U.parse_atom_site(f)
        tc = U.atoms_of(rows, "B", resid=TARGET_C, names={"C4", "N4"}) or \
             U.atoms_of(rows, "B", resid=TARGET_C)
        x = U.min_dist(tc, U.atoms_of(rows, "A", resid=72, names={"OE1", "OE2"}))
        if x is not None: ds.append(x)
    return (sorted(ds)[len(ds) // 2] if ds else float("nan")), ds

def seq_to_negs(seq):
    muts = {}
    for i in range(min(len(WT_SEQ), len(seq))):
        if WT_SEQ[i] != seq[i]:
            muts[i + 1] = seq[i]
    key = tuple(x for p in sorted(muts) for x in (p, muts[p]))
    return NEG_PANEL.get(key)

def discover_negctrl(root="new/negctrl"):
    """按 job_request 的蛋白序列把阴性对照作业归类。返回 {展示名: (gcg_dir, gca_dir, act, cls)}"""
    out = {}
    if not os.path.isdir(root): return out
    dirs = sorted({os.path.dirname(p) for p in
                   glob.glob(os.path.join(root, "**", "*full_data*.json"), recursive=True)})
    for d in dirs:
        jr = glob.glob(os.path.join(d, "*job_request.json"))
        if not jr: continue
        j = json.load(open(jr[0], encoding="utf-8"))[0]
        if len(j["sequences"]) < 2: continue
        rna = j["sequences"][1]["rnaSequence"]["sequence"]
        hit = seq_to_negs(j["sequences"][0]["proteinChain"]["sequence"])
        if not hit: continue
        disp, act, cls = hit
        tag = "gcg" if rna == "GUGCGCG" else "gca" if rna == "GUGCACG" else None
        if tag is None: continue
        rec = out.setdefault(disp, {"act": act, "cls": cls, "gcg": None, "gca": None})
        rec[tag] = d
    return out

# ---------------------------------------------------------------- WT 零假设
print("读取 WT …", flush=True)
def wt_seeds(root):
    out = []
    for s in sorted(x for x in glob.glob(os.path.join(root, "*")) if os.path.isdir(x)):
        M, v = load_seed(s)
        if M is not None and M.shape[0] == 199: out.append((M, v))
    return out

WT = {s: wt_seeds(r) for s, r in [("GCG", "GUGCGCG_20"), ("GCA", "GUGCACG_20")]}
N_SEED = len(WT["GCG"])
print(f"  WT: {N_SEED} seed × {N_MODEL_PER_SEED} model")

n_prot = 199
iu = np.triu_indices(n_prot, k=1)
lr = np.array([(i, j) for i in range(n_prot) for j in range(i + 5, n_prot)])
rmsd = lambda a, b: math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)) / len(a))

def cp_metrics(Ma, va, Mb, vb):
    d = [abs(x - y) for x, y in zip(va, vb)]
    num = sum(x * y for x, y in zip(va, vb)); den = sum(y * y for y in vb)
    return dict(intra_lr_rmsd=rmsd([Ma[i, j] for i, j in lr], [Mb[i, j] for i, j in lr]),
                pocket_rmsd=rmsd([Ma[i, j] for i in range(n_prot) for j in range(i + 1, n_prot)
                                  if i + 1 in POCKET and j + 1 in POCKET],
                                 [Mb[i, j] for i in range(n_prot) for j in range(i + 1, n_prot)
                                  if i + 1 in POCKET and j + 1 in POCKET]),
                protC_rmsd=rmsd(va, vb),
                protC_alpha=num / den if den > 0 else float("nan"),
                protC_maxabs=max(d), protC_argmax=d.index(max(d)) + 1)

# 预计算 pocket 索引，避免重复
PK = [(i, j) for i in range(n_prot) for j in range(i + 1, n_prot)
      if i + 1 in POCKET and j + 1 in POCKET]

def cp_metrics(Ma, va, Mb, vb):
    d = [abs(x - y) for x, y in zip(va, vb)]
    num = sum(x * y for x, y in zip(va, vb)); den = sum(y * y for y in vb)
    return dict(intra_lr_rmsd=rmsd([Ma[i, j] for i, j in lr], [Mb[i, j] for i, j in lr]),
                pocket_rmsd=rmsd([Ma[i, j] for i, j in PK], [Mb[i, j] for i, j in PK]),
                protC_rmsd=rmsd(va, vb),
                protC_alpha=num / den if den > 0 else float("nan"),
                protC_maxabs=max(d), protC_argmax=d.index(max(d)) + 1)

NULL = {sub: [cp_metrics(WT[sub][i][0], WT[sub][i][1], WT[sub][j][0], WT[sub][j][1])
              for i in range(N_SEED) for j in range(i + 1, N_SEED)] for sub in ("GCG", "GCA")}
def ns(sub, k):
    v = [x[k] for x in NULL[sub]]
    m = sum(v) / len(v)
    sd = math.sqrt(sum((a - m) ** 2 for a in v) / (len(v) - 1))
    return m, sd, max(v)

# ---------------------------------------------------------------- 逐构建体
NEG = discover_negctrl()
print(f"在 new/negctrl/ 发现 {len(NEG)} 个阴性对照构建体"
      + ("" if NEG else "（尚未提交；本次仅跑既有突变体，管线自检）"))

ROWS = []
def add(disp, gcg, gca, act, cls, is_neg):
    for sub, d in [("GCG", gcg), ("GCA", gca)]:
        if not d or not os.path.isdir(d): continue
        Mv, vv = load_seed(d)
        if Mv is None: continue
        ms = [cp_metrics(Mv, vv, Mw, vw) for Mw, vw in WT[sub]]
        avg = {k: sum(x[k] for x in ms) / len(ms) for k in ms[0]}
        g, _ = geom(d)
        m, sd, mx = ns(sub, "protC_rmsd")
        m2, sd2, _ = ns(sub, "pocket_rmsd")
        m3, sd3, _ = ns(sub, "intra_lr_rmsd")
        ROWS.append(dict(sub=sub, name=disp, activity=act, cls=cls, is_neg=is_neg,
                         intra=avg["intra_lr_rmsd"], z_intra=(avg["intra_lr_rmsd"] - m3) / sd3,
                         pocket=avg["pocket_rmsd"], z_pocket=(avg["pocket_rmsd"] - m2) / sd2,
                         protC=avg["protC_rmsd"], z_protC=(avg["protC_rmsd"] - m) / sd,
                         alpha=avg["protC_alpha"], dE72=g))

for gcg, gca, disp, _ in EXISTING:
    if not os.path.isdir(gcg): continue
    wk = wet_key_of(disp); a = ACT.get(wk)
    add(disp, gcg, gca, a, classify(a), False)
for disp, r in NEG.items():
    add(disp, r["gcg"], r["gca"], r["act"],
        r["cls"] if r["act"] is None else classify(r["act"]), True)

# ---------- WT 参照点（加入 fig12）----------
# ① WT 亲本（GCG）：活性按定义 = 1.0，偏离恒为 0，是图的参考原点
_wt_v = np.mean([v for _, v in WT["GCG"]], axis=0)
ROWS.append(dict(sub="GCG", name="WT（GCG 亲本）", activity=1.0, cls="WT 参照",
                 is_neg=False, intra=0.0, z_intra=0.0, pocket=0.0, z_pocket=0.0,
                 protC=0.0, z_protC=0.0, alpha=1.0, dE72=geom("GUGCGCG_20/001")[0]))

# ② 第二组 WT（GCA 底物）：蛋白完全相同，只换 RNA。
#    偏离按「GCG 的 WT」为参考计算 —— 与 PCA 里的 D_M 口径一致。
_wt2_dirs = sorted(x for x in glob.glob(os.path.join("GUGCACG_20", "*")) if os.path.isdir(x))
_wt2 = [load_seed(d) for d in _wt2_dirs]
_wt2 = [(M, v) for M, v in _wt2 if M is not None]
if _wt2:
    M2 = np.mean([M for M, _ in _wt2], axis=0)
    v2 = np.mean([v for _, v in _wt2], axis=0)
    ms = [cp_metrics(M2, v2, Mw, vw) for Mw, vw in WT["GCG"]]
    avg = {k: sum(x[k] for x in ms) / len(ms) for k in ms[0]}
    m, sd, _ = ns("GCG", "protC_rmsd")
    m2_, sd2, _ = ns("GCG", "pocket_rmsd")
    m3, sd3, _ = ns("GCG", "intra_lr_rmsd")
    _d72 = np.median([geom(d)[0] for d in _wt2_dirs if geom(d)[0] == geom(d)[0]])
    ROWS.append(dict(sub="GCG", name="WT（GCA 底物）", activity=1.0, cls="WT 参照",
                     is_neg=False,
                     intra=avg["intra_lr_rmsd"], z_intra=(avg["intra_lr_rmsd"] - m3) / sd3,
                     pocket=avg["pocket_rmsd"], z_pocket=(avg["pocket_rmsd"] - m2_) / sd2,
                     protC=avg["protC_rmsd"], z_protC=(avg["protC_rmsd"] - m) / sd,
                     alpha=avg["protC_alpha"], dE72=float(_d72)))
    print(f"\n★ WT 参照点：GCA 底物的蛋白–靶C CP 偏离 = {avg['protC_rmsd']:.5f}"
          f"（z = {(avg['protC_rmsd'] - m) / sd:+.1f}），靶C–E72 = {_d72:.2f} Å")

print(f"\n共纳入 {len([r for r in ROWS if r['sub']=='GCG'])} 个构建体（GCG，含 2 个 WT 参照点）")

# ---------------------------------------------------------------- 控制台
with_act = [r for r in ROWS if r["sub"] == "GCG" and r["activity"] is not None
            and r["cls"] != "WT 参照"]          # 统计只用真实突变体，WT 参照单独报告
print("\n" + "=" * 112)
print("【GCG】偏离指标 vs 实测活性（按活性升序）")
print("=" * 112)
print(f"{'构建体':<18}{'活性保留':>9}{'类别':<14}{'靶C-CP偏离':>11}{'z':>8}{'口袋CP偏离':>11}{'z':>8}{'d_E72':>8}")
for r in sorted(with_act, key=lambda x: x["activity"]):
    print(f"{r['name']:<18}{r['activity']:>9.3f}{r['cls']:<14}{r['protC']:>11.5f}"
          f"{r['z_protC']:>+8.1f}{r['pocket']:>11.5f}{r['z_pocket']:>+8.1f}{r['dE72']:>8.2f}")

def pearson(xs, ys):
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs); syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")

print("\n" + "=" * 112)
print("相关性：偏离指标 vs 活性保留率")
print("=" * 112)
acts = [r["activity"] for r in with_act]
for k, lab in [("z_protC", "蛋白–靶C CP 偏离 z"), ("z_pocket", "口袋内部 CP 偏离 z"),
               ("z_intra", "蛋白内部 CP 偏离 z"), ("dE72", "靶C–E72 距离")]:
    print(f"  {lab:<24} r = {pearson([r[k] for r in with_act], acts):+.3f}   (n={len(with_act)})")

# 关键同位点对照
print("\n" + "=" * 112)
print("★ 决定性判据：同位点、相反功能的两两对照")
print("=" * 112)
PAIRS = [("T31A", "T31D", 31), ("N57A", "N57W", 57)]
for a, b, pos in PAIRS:
    ra = next((r for r in ROWS if r["sub"] == "GCG" and r["name"] == a), None)
    rb = next((r for r in ROWS if r["sub"] == "GCG" and r["name"] == b), None)
    if not ra or not rb:
        print(f"  位点 {pos}：{a} 或 {b} 尚无模型（待 AF3 结果）")
        continue
    aa = "—" if ra["activity"] is None else f"{ra['activity']:.3f}"
    ab = "—" if rb["activity"] is None else f"{rb['activity']:.3f}"
    print(f"  位点 {pos}：{a}(活性 {aa}) vs {b}(活性 {ab})")
    print(f"     靶C-CP 偏离 {ra['protC']:.5f} vs {rb['protC']:.5f}   "
          f"比值 {ra['protC']/rb['protC']:.2f}")
    print(f"     口袋CP 偏离 {ra['pocket']:.5f} vs {rb['pocket']:.5f}   "
          f"比值 {ra['pocket']/rb['pocket']:.2f}")
    print(f"     → 若两者相近，则指标无法分辨「活性 0.97」与「活性 0.000」")

# ---------------------------------------------------------------- 导出
with open("results/阴性对照_偏离与PCA.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["substrate", "construct", "activity_retention", "functional_class", "is_negctrl",
                "intra_lr_rmsd", "z_intra", "pocket_rmsd", "z_pocket",
                "protC_rmsd", "z_protC", "protC_alpha", "d_E72"])
    for r in ROWS:
        w.writerow([r["sub"], r["name"], "" if r["activity"] is None else round(r["activity"], 4),
                    r["cls"], r["is_neg"], round(r["intra"], 5), round(r["z_intra"], 2),
                    round(r["pocket"], 5), round(r["z_pocket"], 2), round(r["protC"], 5),
                    round(r["z_protC"], 2), round(r["alpha"], 4), round(r["dE72"], 3)])
print("\n写入 results/阴性对照_偏离与PCA.csv")

# ---------------------------------------------------------------- 图
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
CLR = {"有活性": "#2E7D32", "部分失活": "#F9A825", "完全失活": "#C62828",
       "★同位点活性对照": "#1565C0", "未测": "0.6", "WT 参照": "#9C27B0"}

G = [r for r in ROWS if r["sub"] == "GCG"]
fig, axes = plt.subplots(1, 3, figsize=(19, 5.8))
fig.suptitle("图12　把完全失活阴性对照并入偏离诊断：CP 偏离能识别失活吗？\n"
             "★ 紫菱形 = 两组 WT 参照（活性按定义 1.0）：GCG 亲本偏离恒为 0；"
             "GCA 底物蛋白完全相同、只换 RNA，其偏离却与失活组同量级",
             fontsize=13, fontweight="bold")
for ax, key, lab in zip(axes, ["protC", "pocket", "dE72"],
                        ["蛋白–靶C CP 偏离（RMSD）", "活性口袋内部 CP 偏离（RMSD）",
                         "靶C C4/N4 – E72 距离（Å）"]):
    for cls in ["WT 参照", "有活性", "部分失活", "完全失活", "★同位点活性对照", "未测"]:
        pts = [r for r in G if r["cls"] == cls and r["activity"] is not None]
        if not pts: continue
        ax.scatter([r["activity"] for r in pts], [r[key] for r in pts],
                   s=190 if cls == "WT 参照" else (110 if "同位点" in cls else 80),
                   c=CLR[cls],
                   marker="D" if cls == "WT 参照" else ("*" if "同位点" in cls else "o"),
                   edgecolors="black", linewidths=0.6,
                   zorder=5 if cls == "WT 参照" else 3,
                   label=cls if cls not in ("★同位点活性对照",) else "T31A（同位点活性对照）")
        for r in pts:
            ax.annotate(r["name"], (r["activity"], r[key]), textcoords="offset points",
                        xytext=(6, 5), fontsize=8,
                        fontweight="bold" if cls == "WT 参照" else "normal",
                        color=CLR[cls] if cls == "WT 参照" else "black")
    # WT-GCA 的水平参考线：只换 RNA 造成的偏离量级
    wtg = next((r for r in G if r["name"] == "WT（GCA 底物）"), None)
    if wtg and key != "dE72":
        ax.axhline(wtg[key], color="#9C27B0", ls="--", lw=1.2, alpha=0.65,
                   zorder=1, label="只换 RNA 的偏离量级")
    elif wtg:
        ax.axhline(wtg[key], color="#9C27B0", ls="--", lw=1.2, alpha=0.65,
                   zorder=1, label="只换 RNA 的距离")
    # 连接同位点对照对
    for a, b in [("T31A", "T31D"), ("N57A", "N57W")]:
        ra = next((r for r in G if r["name"] == a and r["activity"] is not None), None)
        rb = next((r for r in G if r["name"] == b and r["activity"] is not None), None)
        if ra and rb:
            ax.plot([ra["activity"], rb["activity"]], [ra[key], rb[key]],
                    color="0.55", ls=":", lw=1.4, zorder=2)
    ax.set_xlabel("实测活性保留率", fontsize=10.5)
    ax.set_ylabel(lab, fontsize=10.5)
    ax.grid(alpha=0.25); ax.legend(fontsize=8.5)
axes[0].set_title("偏离越大 ≠ 越失活", fontsize=11.5, fontweight="bold")
axes[1].set_title("口袋内部 CP", fontsize=11.5, fontweight="bold")
axes[2].set_title("催化几何", fontsize=11.5, fontweight="bold")
plt.tight_layout(rect=[0, 0, 1, 0.91])
plt.savefig("results/figs/fig12_阴性对照_偏离诊断.png", dpi=155, bbox_inches="tight")
print("写入 results/figs/fig12_阴性对照_偏离诊断.png")

# ---- PCA（与脚本 38 完全同口径：样本 = model 级，零假设 = WT seed 质心）----
def load_models(d):
    """返回该目录下每个 model 的特征向量（不跨 model 平均）。"""
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids, rids = j["token_chain_ids"], j["token_res_ids"]
        cpm = np.asarray(j["contact_probs"], dtype=np.float64)
        idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
        t = next(i for i in range(len(cids)) if cids[i] == RNA and rids[i] == TARGET_C)
        M = np.maximum(cpm[np.ix_(idx, idx)], cpm[np.ix_(idx, idx)].T)
        v = np.maximum(cpm[idx, t], cpm[t, idx])
        out.append(np.concatenate([M[iu], v]))
    return out

rows, labels = [], []
wt_seed_dirs = sorted(x for x in glob.glob(os.path.join("GUGCGCG_20", "*")) if os.path.isdir(x))
for s in wt_seed_dirs:
    for f in load_models(s):
        rows.append(f); labels.append("WT")
# 第二组 WT：同一蛋白、换用 GCA 底物（20 seed × 5 model）
# 作用 = 只换底物、不改蛋白时的 CP 自然波动幅度 → 判断突变体分离是否有意义的天然标尺
wt2_dirs = sorted(x for x in glob.glob(os.path.join("GUGCACG_20", "*")) if os.path.isdir(x))
for s in wt2_dirs:
    for f in load_models(s):
        rows.append(f); labels.append("WT-GCA")
for gcg, gca, disp, _ in EXISTING:
    if not os.path.isdir(gcg): continue
    for f in load_models(gcg):
        rows.append(f); labels.append(disp)
for disp, rr in NEG.items():
    if not rr["gcg"]: continue
    for f in load_models(rr["gcg"]):
        rows.append(f); labels.append(disp)

X = np.array(rows); labels = np.array(labels)
print(f"\nPCA 输入：{X.shape[0]} 个 model × {X.shape[1]} 维"
      f"（WT {int((labels=='WT').sum())} 个 model / {N_SEED} 个 seed；"
      f"其余为各构建体的 model）")
Xc = X - X.mean(0)
U_, S_, _ = np.linalg.svd(Xc, full_matrices=False)
S_ = np.asarray(S_)
SC = U_ * S_
VE = S_ ** 2 / (S_ ** 2).sum()

# WT seed 质心（每个 seed 的 5 个 model 取均值）→ 零假设单位，与突变体同尺度
wt_idx = np.where(labels == "WT")[0]
n_per = len(wt_idx) // N_SEED

# ---- 主统计量 D_M：在「仅由 WT 20 个 seed 定义」的基底上做白化马氏距离 ----
#      为什么要这样做：
#        · 直接在全特征空间用对角协方差 → CP 矩阵元素高度相关，白化不充分，尺度失准；
#        · 在「WT + 全部构建体」的合并 PCA 上算 → 结果会随纳入了哪些构建体而变。
#      故只用 WT 的 seed 协方差定义前 K 个主方向，再把构建体质心投影进去比较。
W = X[wt_idx].reshape(N_SEED, n_per, -1).mean(1)          # (20, p) WT seed 质心
w_mean = W.mean(0)
Wc = W - w_mean
_, Sw, Vt = np.linalg.svd(Wc, full_matrices=False)
K = min(10, N_SEED - 2)
Vk = Vt[:K].T                                             # (p, K) 仅由 WT 决定的方向
sW = Wc @ Vk                                              # (20, K) WT seed 得分
cwt, sd = sW.mean(0), np.maximum(sW.std(0, ddof=1), 1e-12)
Dm = lambda s: math.sqrt(float(np.mean(((s - cwt) / sd) ** 2)))

NULLD = []
for i in range(N_SEED):
    oth = np.delete(sW, i, axis=0)
    c, s2 = oth.mean(0), np.maximum(oth.std(0, ddof=1), 1e-12)
    NULLD.append(math.sqrt(float(np.mean(((sW[i] - c) / s2) ** 2))))
D_OF = {}
for nm in sorted(set(labels) - {"WT"}):
    idx = labels == nm
    if idx.sum() == 0: continue
    D_OF[nm] = Dm((X[idx].mean(0) - w_mean) @ Vk)
p95 = float(np.percentile(NULLD, 95))
print(f"D_M 零假设（WT seed 留一，n={N_SEED}）：中位 {np.median(NULLD):.2f}，"
      f"95 分位 {p95:.2f}，最大 {max(NULLD):.2f}")
if "WT-GCA" in D_OF:
    print(f"★ 第二组 WT（GCA 底物）D_M = {D_OF['WT-GCA']:.2f}"
          f"　→ 只换底物、不改蛋白时的自然偏移"
          f"（{'超出' if D_OF['WT-GCA'] > p95 else '未超出'} WT seed 95 分位）")

# ---- D_M 与活性的关系：Pearson / Spearman / 阈值分类 ----
CLS_OF = {r["name"]: r["cls"] for r in G}
CLS_OF["WT-GCA"] = "WT（GCA 底物）"
with open("results/阴性对照_DM.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["construct", "D_M", "activity_retention", "functional_class"])
    for nm in sorted(D_OF, key=lambda x: -D_OF[x]):
        a = next((r["activity"] for r in G if r["name"] == nm and r["activity"] is not None), None)
        w.writerow([nm, round(D_OF[nm], 3), "" if a is None else round(a, 4),
                    CLS_OF.get(nm, "未测")])

# ---- 图谱坐标（fig13 左图所用的合并 PCA 前 3 轴质心）----
with open("results/阴性对照_PC坐标.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["construct", "PC1", "PC2", "PC3", "D_M", "activity_retention", "functional_class"])
    for nm in sorted(set(labels) - {"WT"}):
        c = SC[labels == nm].mean(0)
        a = next((r["activity"] for r in G if r["name"] == nm and r["activity"] is not None), None)
        w.writerow([nm] + [round(float(x), 4) for x in c[:3]] +
                   [round(D_OF.get(nm, float("nan")), 3),
                    "" if a is None else round(a, 4), CLS_OF.get(nm, "未测")])

# ---- 失活组在 PC 图上是否成簇？----
DEAD = [nm for nm, r in CLS_OF.items() if r == "完全失活"]
ALIVE = [nm for nm, r in CLS_OF.items() if r == "有活性"]
if DEAD and ALIVE:
    def cent(nms, k=3):
        return np.mean([SC[labels == nm].mean(0)[:k] for nm in nms], axis=0)
    cd, ca = cent(DEAD), cent(ALIVE)
    wt_c = SC[wt_idx][:, :3].mean(0)
    wt_sd = SC[wt_idx][:, :3].std(0, ddof=1)
    print("\n" + "=" * 104)
    print("失活组在 PC 图（fig13 左图）上的位置")
    print("=" * 104)
    print(f"  失活组（n={len(DEAD)}）：{', '.join(DEAD)}")
    print(f"  活性组（n={len(ALIVE)}）")
    print(f"  两组质心在 PC1–PC3 的距离 = {float(np.linalg.norm(cd - ca)):.3f}"
          f"　（WT 云在 PC1–PC3 的 1 SD 尺度 = {float(np.linalg.norm(wt_sd)):.3f}）")
    print(f"\n  {'构建体':<20}{'PC1':>9}{'PC2':>9}{'PC3':>9}{'D_M':>8}{'活性':>8}  {'到失活质心':>11}{'到活性质心':>11}  最近组")
    for nm in sorted(set(labels) - {"WT"}, key=lambda x: -D_OF.get(x, 0)):
        c = SC[labels == nm].mean(0)[:3]
        dd, da = float(np.linalg.norm(c - cd)), float(np.linalg.norm(c - ca))
        a = next((r["activity"] for r in G if r["name"] == nm and r["activity"] is not None), None)
        print(f"  {nm:<20}{c[0]:>9.3f}{c[1]:>9.3f}{c[2]:>9.3f}{D_OF.get(nm, float('nan')):>8.2f}"
              f"{('—' if a is None else f'{a:.3f}'):>8}  {dd:>11.3f}{da:>11.3f}  "
              f"{'失活' if dd < da else '活性'}")
    hit = sum(1 for nm in DEAD
              if np.linalg.norm(SC[labels == nm].mean(0)[:3] - cd) <
                 np.linalg.norm(SC[labels == nm].mean(0)[:3] - ca))
    print(f"\n  最近质心分类：失活组 {hit}/{len(DEAD)} 被分到失活簇；"
          f"活性组 {sum(1 for nm in ALIVE if np.linalg.norm(SC[labels == nm].mean(0)[:3]-cd) > np.linalg.norm(SC[labels == nm].mean(0)[:3]-ca))}/{len(ALIVE)} 被分到活性簇")

def spearman(xs, ys):
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v)
        i = 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and v[s[j + 1]] == v[s[i]]: j += 1
            for k in range(i, j + 1): r[s[k]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    return pearson(rank(xs), rank(ys))

PAIR = [(nm, D_OF[nm], next((r["activity"] for r in G if r["name"] == nm
                             and r["activity"] is not None), None)) for nm in D_OF]
PAIR = [(n, d, a) for n, d, a in PAIR if a is not None]
print(f"\nD_M vs 活性（n={len(PAIR)}）：Pearson r = {pearson([p[1] for p in PAIR], [p[2] for p in PAIR]):+.3f}"
      f"，Spearman ρ = {spearman([p[1] for p in PAIR], [p[2] for p in PAIR]):+.3f}")
alive = [(n, d, a) for n, d, a in PAIR if a > 0.15]
print(f"  仅「非完全失活」子集（n={len(alive)}）：Pearson r = "
      f"{pearson([p[1] for p in alive], [p[2] for p in alive]):+.3f}"
      f"，Spearman ρ = {spearman([p[1] for p in alive], [p[2] for p in alive]):+.3f}")

print("\n阈值分类（判据 D_M > 1.57 = WT seed 95 分位 → 预测「非 WT 表型」）：")
for thr_lab, thr in [("D_M > 1.57", p95)]:
    dead = [p for p in PAIR if p[2] <= 0.15]
    act = [p for p in PAIR if p[2] > 0.15]
    tp = sum(1 for p in dead if p[1] > thr); fn = len(dead) - tp
    fp = sum(1 for p in act if p[1] > thr); tn = len(act) - fp
    print(f"  {thr_lab}：失活组命中 {tp}/{len(dead)}，活性组误报 {fp}/{len(act)}")
    if tp: print(f"     → 灵敏度 {tp/len(dead):.0%}，特异度 {tn/len(act):.0%}"
                 if act else "")
    fp_names = [p[0] for p in act if p[1] > thr]
    if fp_names:
        print(f"     → 误报的活性突变体：{', '.join(fp_names)}")
        print(f"       其中 D_M 最高者 {max((p for p in act if p[1] > thr), key=lambda x: x[1])[0]}"
              f" D_M = {max(p[1] for p in act if p[1] > thr):.2f}"
              f"，已超过失活组最低者 {min(p[1] for p in dead):.2f}"
              if dead else "")

fig, axes = plt.subplots(1, 2, figsize=(16.5, 6.4))
fig.suptitle("图13　把完全失活阴性对照并入 PCA：失活组会单独成簇吗？",
             fontsize=14, fontweight="bold")
ax = axes[0]
CLS_OF = {r["name"]: r["cls"] for r in G}
CLS_OF["WT-GCA"] = "WT（GCA 底物）"
ax.scatter(SC[wt_idx, 0], SC[wt_idx, 1], s=14, c="0.78", alpha=0.55,
           edgecolors="none", label="WT（GCG 底物，零假设基准）")
wg = labels == "WT-GCA"
if wg.sum():
    ax.scatter(SC[wg, 0], SC[wg, 1], s=14, c="#9C27B0", alpha=0.55,
               edgecolors="none", label="WT（GCA 底物，第二参照）")
    ax.scatter(*SC[wg][:, :2].mean(0), marker="X", s=200, c="#9C27B0",
               edgecolors="black", linewidths=1.1, zorder=5)
    ax.annotate("WT-GCA 质心", (SC[wg][:, 0].mean(), SC[wg][:, 1].mean()),
                textcoords="offset points", xytext=(9, -14), fontsize=8.5,
                color="#6A1B9A", fontweight="bold")
for nm in set(labels) - {"WT", "WT-GCA"}:
    idx = labels == nm
    cls = CLS_OF.get(nm, "未测")
    ax.scatter(SC[idx, 0], SC[idx, 1], s=95 if "同位点" in cls else 70,
               c=CLR.get(cls, "0.6"), marker="*" if "同位点" in cls else "o",
               edgecolors="black", linewidths=0.6, zorder=3)
    ax.annotate(nm, (SC[idx][:, 0].mean(), SC[idx][:, 1].mean()),
                textcoords="offset points", xytext=(6, 5), fontsize=8)
ax.set_xlabel(f"PC1 ({VE[0]:.1%})", fontsize=10.5)
ax.set_ylabel(f"PC2 ({VE[1]:.1%})", fontsize=10.5)
ax.set_title("PC1–PC2（颜色 = 功能类别；紫色 = 第二组 WT）", fontsize=11.5, fontweight="bold")
ax.grid(alpha=0.25)
h = [plt.Line2D([], [], marker="o", ls="", color=c, markeredgecolor="black",
                label=k) for k, c in CLR.items() if k != "未测"]
h += [plt.Line2D([], [], marker="o", ls="", color="0.78", markeredgecolor="none",
                 label="WT（GCG，基准）"),
      plt.Line2D([], [], marker="o", ls="", color="#9C27B0", markeredgecolor="none",
                 label="WT（GCA，第二参照）"),
      plt.Line2D([], [], marker="X", ls="", color="#9C27B0", markeredgecolor="black",
                 markersize=9, label="WT-GCA 质心")]
ax.legend(handles=h, fontsize=8.5, loc="best")

ax = axes[1]
nm_sorted = sorted(D_OF, key=lambda x: D_OF[x])
cols = [CLR.get(CLS_OF.get(n, "未测"), "0.6") for n in nm_sorted]
ax.barh(range(len(nm_sorted)), [D_OF[n] for n in nm_sorted], color=cols,
        edgecolor="black", linewidth=0.4)
ax.axvline(p95, color="0.35", ls="--", lw=1.3, label=f"WT seed 95 分位 = {p95:.2f}")
ax.set_yticks(range(len(nm_sorted))); ax.set_yticklabels(nm_sorted, fontsize=8.5)
ax.set_xlabel("到 WT 质心的马氏距离 D_M", fontsize=10.5)
ax.set_title("分离度（按 D 排序）", fontsize=11.5, fontweight="bold")
ax.legend(fontsize=9); ax.grid(axis="x", alpha=0.25)
plt.tight_layout(rect=[0, 0, 1, 0.91])
plt.savefig("results/figs/fig13_阴性对照_PCA.png", dpi=155, bbox_inches="tight")
print("写入 results/figs/fig13_阴性对照_PCA.png")

print("\n分离度 D（GCG，前 12 名）：")
for n in nm_sorted[-12:][::-1]:
    print(f"  {n:<20} D = {D_OF[n]:>6.2f}   {CLS_OF.get(n,'')}")
