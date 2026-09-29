# -*- coding: utf-8 -*-
"""
阶段 46 —— 纯蛋白模型（AF3 输入不含 RNA）的内部 CP 能否分开聚类？

问题：
  38 / 43 的结论建立在「蛋白 + RNA 复合物」的 CP 上。本脚本用「只给蛋白链」的 AF3 作业，
  检验同一批构建体在**纯蛋白内部 CP** 上能否分开，并与复合物模型的结果并排比较。
  两者结论一致 → CP 偏离是蛋白自身折叠的变化；纯蛋白中消失 → 偏离依赖 RNA。

特征（纯蛋白模型没有 RNA，只能用蛋白内部 CP）：
  P1 内部CP(全)     i<j 上三角
  P2 内部CP(长程)   |i−j| ≥ 5
  P3 口袋内部CP     活性口袋残基之间

统计口径与脚本 43 完全一致：
  · 分析单位 = seed 质心（每个 seed 的 5 个 model 取均值）
  · 零假设 = WT 的 20 个 seed 质心的留一马氏距离
  · 分离度 D_M = 在「仅由 WT 20 个 seed 定义」的基底上白化的马氏距离

数据放置：把 af3_submit_pure/ 的 60 个作业提交后，下载结果丢到 new/protein_only/
          （目录名随意，脚本读 job_request.json 按蛋白序列自动归类）

产出：
  results/纯蛋白_分离度.csv
  results/figs/fig14_纯蛋白_PCA.png
  results/figs/fig15_纯蛋白_vs_复合物.png
"""
import json, glob, os, sys, math, csv
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import af_utils as U

PROT = U.PROT_CHAIN
SRC = "new/pure"          # 纯蛋白 AF3 结果的根目录；若改名为 new/protein_only 亦可，下面的
SRC_ALT = "new/protein_only"
WT_SEQ = json.load(open("af3_submit/WT_GCG.json", encoding="utf-8"))[0]["sequences"][0]["proteinChain"]["sequence"]
POCKET = list(range(25, 33)) + list(range(57, 61)) + list(range(70, 73)) + \
         list(range(99, 106)) + list(range(129, 134))

# 突变 -> (展示名, 湿实验活性, 功能类别)
# 注意：空元组 () = 无突变 = WT，必须登记，否则 WT 会被判为「序列不匹配任何构建体」
PANEL = {
    ():                          ("WT", None, "WT 基准"),
    (132, "D"):                  ("M132D", 0.890, "有活性"),
    (132, "E"):                  ("M132E", 0.830, "有活性"),
    (30, "H"):                   ("K30H", 0.840, "有活性"),
    (27, "T", 30, "H", 58, "M"): ("G27T-K30H-Q58M", 0.772, "有活性"),
    (31, "D"):                   ("T31D", 0.000, "完全失活"),
    (57, "W"):                   ("N57W", 0.000, "完全失活"),
    (27, "D", 130, "G"):         ("G27D-M130G", 0.000, "完全失活"),
    (31, "A"):                   ("T31A", 0.970, "★同位点活性对照"),
    (57, "A"):                   ("N57A", None, "新失活对照（未测）"),
    (72, "A"):                   ("E72A", None, "新失活对照（未测）"),
}
CLR = {"有活性": "#2E7D32", "完全失活": "#C62828", "★同位点活性对照": "#1565C0",
       "新失活对照（未测）": "0.62"}


# ---------------------------------------------------------------------------
def load_models(d):
    """返回该目录下每个 model 的蛋白内部 CP 矩阵（199×199）。"""
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        j = json.load(open(f, encoding="utf-8"))
        cids = j["token_chain_ids"]
        cpm = np.asarray(j["contact_probs"], dtype=np.float64)
        idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
        M = cpm[np.ix_(idx, idx)]
        out.append(np.maximum(M, M.T))
    return out


def seq_to_panel(seq):
    muts = {}
    for i in range(min(len(WT_SEQ), len(seq))):
        if WT_SEQ[i] != seq[i]:
            muts[i + 1] = seq[i]
    key = tuple(x for p in sorted(muts) for x in (p, muts[p]))
    return PANEL.get(key)


def discover(root):
    if not os.path.isdir(root):
        return None
    dirs = sorted({os.path.dirname(p) for p in
                   glob.glob(os.path.join(root, "**", "*full_data*.json"), recursive=True)})
    if not dirs:
        return None
    out, unknown = {}, []
    for d in dirs:
        jr = glob.glob(os.path.join(d, "*job_request.json"))
        if not jr:
            unknown.append((d, "无 job_request")); continue
        j = json.load(open(jr[0], encoding="utf-8"))[0]
        chains = [list(s.keys())[0] for s in j["sequences"]]
        if chains != ["proteinChain"]:
            unknown.append((d, f"非纯蛋白链 {chains}")); continue
        hit = seq_to_panel(j["sequences"][0]["proteinChain"]["sequence"])
        if not hit:
            unknown.append((d, "序列不匹配任何构建体")); continue
        out.setdefault(hit[0], []).append(d)
    return out, unknown


print("=" * 108)
print("阶段 46 —— 纯蛋白模型内部 CP 的聚类可分性")
print("=" * 108)

res = discover(SRC) or discover(SRC_ALT)
if res is None:
    print(f"\n未在 {SRC}/ 下找到纯蛋白 AF3 结果。")
    print("请先提交 af3_submit_pure/ 中的 60 个 JSON（每个 1 个 seed），下载后放到该目录再运行。")
    print("（脚本已完成自检，数据到位后直接重跑即可）")
    sys.exit(0)
found, unknown = res
if unknown:
    print(f"\n⚠ {len(unknown)} 个目录未归类（已跳过）：{unknown[:5]}")
print("\n归类结果：")
for nm, dirs in sorted(found.items()):
    print(f"  {nm:<18} {len(dirs)} 个 seed 目录")
if "WT" not in found:
    print("\n未找到 WT，无法构造零假设。"); sys.exit(0)

# ---------------------------------------------------------------------------
n_prot = 199
iu = np.triu_indices(n_prot, k=1)
FSETS = {
    "P1_内部CP全": np.ones(len(iu[0]), bool),
    "P2_内部CP长程": np.array([abs(i - j) >= 5 for i, j in zip(*iu)]),
    "P3_口袋内部CP": np.array([(i + 1) in POCKET and (j + 1) in POCKET for i, j in zip(*iu)]),
}
print("\n特征维度：" + "，".join(f"{k} = {int(v.sum())}" for k, v in FSETS.items()))

# 每个 seed 目录 -> 质心向量（一次读盘，三套特征共用）
SEED_M = {}   # {构建体: [(M_flat, ...)]}  存 199×199 矩阵的展平
for nm, dirs in found.items():
    mats = []
    for d in dirs:
        ms = load_models(d)
        if ms:
            mats.append(np.mean(ms, axis=0))
    if mats:
        SEED_M[nm] = mats

N_SEED = len(SEED_M["WT"])
print(f"WT：{N_SEED} 个 seed 质心（每个 = 5 model 均值）")


def analyse(fs):
    mask = FSETS[fs]
    V = {nm: np.array([M[iu][mask] for M in mats]) for nm, mats in SEED_M.items()}
    Ws = V["WT"]
    w_mean = Ws.mean(0)
    _, Sw, Vt = np.linalg.svd(Ws - w_mean, full_matrices=False)
    K = min(10, Ws.shape[0] - 2)
    Vk = Vt[:K].T
    sW = (Ws - w_mean) @ Vk
    cwt, sd = sW.mean(0), np.maximum(sW.std(0, ddof=1), 1e-12)
    Dm = lambda s: math.sqrt(float(np.mean(((s - cwt) / sd) ** 2)))

    null = []
    for i in range(Ws.shape[0]):
        oth = np.delete(sW, i, axis=0)
        c, s2 = oth.mean(0), np.maximum(oth.std(0, ddof=1), 1e-12)
        null.append(math.sqrt(float(np.mean(((sW[i] - c) / s2) ** 2))))
    D = {nm: Dm((V[nm].mean(0) - w_mean) @ Vk) for nm in V if nm != "WT"}

    # 出图坐标（合并 PCA）
    All = np.vstack([V[nm] for nm in V])
    lab = np.concatenate([[nm] * len(V[nm]) for nm in V])
    U2, S2, _ = np.linalg.svd(All - All.mean(0), full_matrices=False)
    return dict(D=D, null=np.array(null), p95=float(np.percentile(null, 95)),
                SC=(U2 * S2), lab=lab, VE=(S2 ** 2 / (S2 ** 2).sum()))


RES = {fs: analyse(fs) for fs in FSETS}

print("\n" + "=" * 108)
print("纯蛋白模型：分离度 D_M")
print("=" * 108)
print(f"{'构建体':<20}{'活性':>7}{'类别':<18}"
      + "".join(f"{fs.split('_')[1]:>15}" for fs in FSETS))
order = sorted(RES["P1_内部CP全"]["D"], key=lambda x: -RES["P1_内部CP全"]["D"][x])
for nm in order:
    hit = next(v for k, v in PANEL.items() if v[0] == nm)
    a = "—" if hit[1] is None else f"{hit[1]:.3f}"
    print(f"{nm:<20}{a:>7}{hit[2]:<18}"
          + "".join(f"{RES[fs]['D'][nm]:>15.2f}" for fs in FSETS))
for fs in FSETS:
    print(f"  [{fs}] 零假设：中位 {np.median(RES[fs]['null']):.2f}，"
          f"95 分位 {RES[fs]['p95']:.2f}，最大 {RES[fs]['null'].max():.2f}")

# ---------------------------------------------------------------------------
comp = {}
if os.path.exists("results/阴性对照_DM.csv"):
    for r in csv.DictReader(open("results/阴性对照_DM.csv", encoding="utf-8-sig")):
        try: comp[r["construct"]] = float(r["D_M"])
        except ValueError: pass

print("\n" + "=" * 108)
print("并排对照：复合物模型（含 RNA，脚本 43）vs 纯蛋白模型（本脚本 P1）")
print("=" * 108)
pure = RES["P1_内部CP全"]["D"]
print(f"{'构建体':<20}{'活性':>7}{'类别':<18}{'复合物 D_M':>12}{'纯蛋白 D_M':>12}{'纯/复':>8}")
for nm in order:
    hit = next(v for k, v in PANEL.items() if v[0] == nm)
    a = "—" if hit[1] is None else f"{hit[1]:.3f}"
    c = comp.get(nm)
    r = f"{pure[nm] / c:.2f}" if c else "—"
    print(f"{nm:<20}{a:>7}{hit[2]:<18}"
          f"{('—' if c is None else f'{c:.2f}'):>12}{pure[nm]:>12.2f}{r:>8}")

# ---- 失活 vs 活性 最近质心分类（只用实际到货的构建体）----
R1 = RES["P1_内部CP全"]
present = set(R1["D"])
DEAD = [v[0] for v in PANEL.values() if v[2] == "完全失活" and v[0] in present]
# 本批未交付「有活性」组，故把同位点活性对照也算作活性侧参照
ALIVE = [v[0] for v in PANEL.values()
         if v[2] in ("有活性", "★同位点活性对照") and v[0] in present]
print(f"\n最近质心分类：失活组 = {DEAD}；活性侧 = {ALIVE}")
if DEAD and ALIVE:
    cen = lambda nms: np.mean([R1["SC"][R1["lab"] == n].mean(0)[:3] for n in nms], axis=0)
    cd, ca = cen(DEAD), cen(ALIVE)
    d2 = lambda n, c: float(np.linalg.norm(R1["SC"][R1["lab"] == n].mean(0)[:3] - c))
    wt_scale = float(np.linalg.norm(R1["SC"][R1["lab"] == "WT"][:, :3].std(0, ddof=1)))
    print(f"  两组质心距离 = {float(np.linalg.norm(cd - ca)):.3f}"
          f"（WT 云 1 SD 尺度 = {wt_scale:.3f}）")
    print(f"  失活组 {sum(1 for n in DEAD if d2(n,cd) < d2(n,ca))}/{len(DEAD)} 分到失活簇；"
          f"活性侧 {sum(1 for n in ALIVE if d2(n,ca) < d2(n,cd))}/{len(ALIVE)} 分到活性簇")
else:
    print("  （缺组，跳过分类）")

# ---- ★ 各特征集的「失活 vs 活性」分类表现（seed 级，最近质心）----
print("\n" + "=" * 108)
print("★ 失活 vs 活性：三套特征的分类表现（seed 级最近质心，白化空间）")
print("=" * 108)
CLASS_ROWS = []
for fs in FSETS:
    R = RES[fs]
    present = set(R["D"])
    DEAD = [v[0] for v in PANEL.values() if v[2] == "完全失活" and v[0] in present]
    ACT = [v[0] for v in PANEL.values()
           if v[2] in ("有活性", "★同位点活性对照") and v[0] in present]
    V = {nm: np.array([M[iu][FSETS[fs]] for M in SEED_M[nm]]) for nm in SEED_M}
    Ws = V["WT"]; w_mean = Ws.mean(0)
    _, _, Vt = np.linalg.svd(Ws - w_mean, full_matrices=False)
    K = min(10, Ws.shape[0] - 2); Vk = Vt[:K].T
    sW = (Ws - w_mean) @ Vk
    sd = np.maximum(sW.std(0, ddof=1), 1e-12)
    proj = lambda nm: ((V[nm] - w_mean) @ Vk) / sd
    cd = np.mean([proj(n).mean(0) for n in DEAD], axis=0)
    ca = np.mean([proj(n).mean(0) for n in ACT], axis=0)
    D2 = lambda v, c: math.sqrt(float(np.mean(((v - c) ** 2))))
    print(f"\n  【{fs}】两组质心距离 = {float(np.linalg.norm(cd-ca)):.2f}"
          f"（WT seed 云尺度 {float(np.linalg.norm(sW.std(0, ddof=1))):.3f}）")
    print(f"    {'构建体':<20}{'真值':<10}{'到失活质心':>11}{'到活性质心':>11}  判定")
    hit = tot = 0
    for n, truth in [(x, "失活") for x in DEAD] + [(x, "活性") for x in ACT]:
        v = proj(n).mean(0)
        dd, da = D2(v, cd), D2(v, ca)
        pred = "失活" if dd < da else "活性"
        hit += (pred == truth); tot += 1
        flag = "" if pred == truth else "   ← 误判"
        print(f"    {n:<20}{truth:<10}{dd:>11.2f}{da:>11.2f}  {pred}{flag}")
    print(f"    构建体级准确率 = {hit}/{tot} = {hit/tot:.0%}"
          f"（质心含全部组，非留一；n 小，仅供参考）")
    CLASS_ROWS.append(dict(feature_set=fs, construct_accuracy=round(hit / tot, 4),
                           dead=len(DEAD), active=len(ACT),
                           centroid_distance=round(float(np.linalg.norm(cd - ca)), 3)))

with open("results/纯蛋白_分类表现.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(CLASS_ROWS[0]))
    w.writeheader(); w.writerows(CLASS_ROWS)

# ---- ★ 决定性判据：同位点两两差异 ----
# 在「仅由 WT seed 定义」的白化基底上，直接计算 A 与 B 两个质心之间的距离，
# 并与「两个独立 WT seed 之间的同尺度距离」作对照 → 差异是否超出 WT 自身波动。
print("\n" + "=" * 108)
print("★ 决定性判据：同位点两对替换的差异（纯蛋白模型）")
print("=" * 108)
for fs in FSETS:
    R = RES[fs]
    V = {nm: np.array([M[iu][FSETS[fs]] for M in SEED_M[nm]]) for nm in SEED_M}
    Ws = V["WT"]; w_mean = Ws.mean(0)
    _, _, Vt = np.linalg.svd(Ws - w_mean, full_matrices=False)
    K = min(10, Ws.shape[0] - 2); Vk = Vt[:K].T
    sW = (Ws - w_mean) @ Vk
    sd = np.maximum(sW.std(0, ddof=1), 1e-12)
    proj = lambda nm: (V[nm].mean(0) - w_mean) @ Vk
    dist = lambda a, b: math.sqrt(float(np.mean(((a - b) / sd) ** 2)))
    # 零假设：两个独立 WT seed 之间的同尺度距离
    nd = [dist(sW[i], sW[j]) for i in range(len(sW)) for j in range(i + 1, len(sW))]
    nd = np.array(nd)
    print(f"\n【{fs}】WT seed 两两距离：中位 {np.median(nd):.2f}，95 分位 {np.percentile(nd,95):.2f}")
    for a, b, la, lb in [("T31A", "T31D", "0.970", "0.000"), ("N57A", "N57W", "未测", "0.000")]:
        if a not in V or b not in V:
            print(f"  {a} vs {b}：缺数据"); continue
        d = dist(proj(a), proj(b))
        pct = float((nd < d).mean())
        verdict = "✓ 两者可分" if d > np.percentile(nd, 95) else "✗ 两者不可分（落在 WT 自身波动内）"
        print(f"  {a}(活性 {la}) vs {b}(活性 {lb})：距离 = {d:.2f}，"
              f"超过 {pct:.0%} 的 WT seed 对　→ {verdict}")

with open("results/纯蛋白_分离度.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["construct", "activity_retention", "functional_class"]
               + [f"D_M_{fs}" for fs in FSETS] + ["D_M_complex_model", "ratio_pure_over_complex"])
    for nm in order:
        hit = next(v for k, v in PANEL.items() if v[0] == nm)
        c = comp.get(nm)
        w.writerow([nm, "" if hit[1] is None else hit[1], hit[2]]
                   + [round(RES[fs]["D"][nm], 3) for fs in FSETS]
                   + ["" if c is None else c, "" if c is None else round(pure[nm] / c, 3)])
print("\n写入 results/纯蛋白_分离度.csv")

# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
os.makedirs("results/figs", exist_ok=True)

fig, axes = plt.subplots(1, 4, figsize=(25.0, 6.2))
ACC = {r["feature_set"]: r["construct_accuracy"] for r in CLASS_ROWS}
fig.suptitle("图14　纯蛋白模型（AF3 输入不含 RNA）的内部 CP 能否分开聚类？"
             "　虚线 = WT seed 95 分位",
             fontsize=14, fontweight="bold")
ax = axes[0]
wm = R1["lab"] == "WT"
ax.scatter(R1["SC"][wm, 0], R1["SC"][wm, 1], s=42, c="0.78", alpha=0.9,
           edgecolors="none", label="WT（各 seed）")
for nm in order:
    cls = next(v[2] for k, v in PANEL.items() if v[0] == nm)
    c = R1["SC"][R1["lab"] == nm]
    ax.scatter(c[:, 0].mean(), c[:, 1].mean(), s=150 if "同位点" in cls else 105,
               c=CLR[cls], marker="*" if "同位点" in cls else "o",
               edgecolors="black", linewidths=0.7, zorder=3)
    ax.annotate(nm, (c[:, 0].mean(), c[:, 1].mean()), textcoords="offset points",
                xytext=(7, 5), fontsize=8.5)
ax.set_xlabel(f"PC1 ({R1['VE'][0]:.1%})", fontsize=10.5)
ax.set_ylabel(f"PC2 ({R1['VE'][1]:.1%})", fontsize=10.5)
ax.set_title("P1 内部CP(全)：PC1–PC2", fontsize=11.5, fontweight="bold")
ax.grid(alpha=0.25); ax.legend(fontsize=9)

for k, fs in enumerate(["P1_内部CP全", "P2_内部CP长程", "P3_口袋内部CP"]):
    ax = axes[k + 1]
    R = RES[fs]
    nms = sorted(R["D"], key=lambda x: R["D"][x])
    cols = [CLR[next(v[2] for kk, v in PANEL.items() if v[0] == n)] for n in nms]
    ax.barh(range(len(nms)), [R["D"][n] for n in nms], color=cols,
            edgecolor="black", linewidth=0.4)
    ax.axvline(R["p95"], color="0.35", ls="--", lw=1.3,
               label=f"WT seed 95 分位 = {R['p95']:.2f}")
    ax.set_yticks(range(len(nms))); ax.set_yticklabels(nms, fontsize=9)
    ax.set_xlabel("到 WT 质心的马氏距离 D_M", fontsize=10.5)
    acc = ACC.get(fs)
    ttl = fs.split("_", 1)[1]
    if acc is not None:
        ttl += "\n失活/活性判定 " + f"{acc:.0%}"
    ax.set_title(ttl, fontsize=11.5, fontweight="bold")
    ax.legend(fontsize=9); ax.grid(axis="x", alpha=0.25)
h = [plt.Line2D([], [], marker="o", ls="", color=c, markeredgecolor="black", label=k)
     for k, c in CLR.items()]
axes[0].legend(handles=h + [plt.Line2D([], [], marker="o", ls="", color="0.78",
                                       markeredgecolor="none", label="WT")],
               fontsize=8.5, loc="best")
plt.tight_layout(rect=[0, 0, 1, 0.91])
plt.savefig("results/figs/fig14_纯蛋白_PCA.png", dpi=155, bbox_inches="tight")
print("写入 results/figs/fig14_纯蛋白_PCA.png")

fig, ax = plt.subplots(figsize=(9.5, 7.2))
fig.suptitle("图15　复合物模型（含 RNA）vs 纯蛋白模型 的分离度对照",
             fontsize=13.5, fontweight="bold")
pts = [(nm, comp[nm], pure[nm]) for nm in pure if nm in comp]
for nm, x, y in pts:
    cls = next(v[2] for k, v in PANEL.items() if v[0] == nm)
    ax.scatter(x, y, s=140, c=CLR[cls], marker="*" if "同位点" in cls else "o",
               edgecolors="black", linewidths=0.7, zorder=3)
    ax.annotate(nm, (x, y), textcoords="offset points", xytext=(8, 5), fontsize=9)
lim = max(max(x for _, x, _ in pts), max(y for _, _, y in pts)) * 1.15
ax.plot([0, lim], [0, lim], color="0.6", ls="--", lw=1.2)
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
ax.set_xlabel("复合物模型 D_M（含 RNA）", fontsize=11)
ax.set_ylabel("纯蛋白模型 D_M（无 RNA）", fontsize=11)
ax.grid(alpha=0.25)
h = [plt.Line2D([], [], marker="o", ls="", color=c, markeredgecolor="black", label=k)
     for k, c in CLR.items()]
ax.legend(handles=h + [plt.Line2D([], [], ls="--", color="0.6", label="y = x（两者一致）")],
          fontsize=9, loc="upper left")
plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig("results/figs/fig15_纯蛋白_vs_复合物.png", dpi=155, bbox_inches="tight")
print("写入 results/figs/fig15_纯蛋白_vs_复合物.png")
