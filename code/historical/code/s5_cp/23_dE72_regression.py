# -*- coding: utf-8 -*-
"""
阶段 23 —— Δd_E72 补齐 + 与实测 +1 比回归 + 三点复合物结构解析

定义：
  d_E72     = 靶点 C(RNA res4，编辑C/0位) 的脱氨原子 C4/N4
              到催化谷氨酸 E72 羧基(OE1/OE2) 的最小重原子距离
  Δd_E72    = d_E72(GCA) − d_E72(GCG)
              >0 = +1=A 时靶点C被推离催化中心（排A几何）；<0 = 拉近
  回归      = Δd_E72 vs 实测 +1 比(GCG/GCA)

三点复合物（已存在，无需重建）：
  g27tk30hq58m = G27T+K30H+Q58M = 27T-30H-58M
  g27dk30hq58m = G27D+K30H+Q58M = 27D-30H-58M
  各 × {GCG,GCA} × 5 models；额外测「锌配位完整性」：
  锌配位残基 H70(NE2/ND1)、C102(SG)、C105(SG) 的两两距离。

产出：results/dE72_regression.csv、results/zinc_coordination.csv、results/dE72_scatter.png
"""
import os, csv, glob, sys, math
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")
import af_utils as U

C0_RESI = 4          # 靶点 C（编辑C，0位）
ZINC = {70: ("NE2", "ND1"), 102: ("SG",), 105: ("SG",)}
E72 = 72
MAINCHAIN_RNA = {"P", "OP1", "OP2", "O5'", "C5'", "C4'", "O4'", "C3'", "O3'", "C2'", "O2'", "C1'"}

BATCH1 = "new/mut"                                   # {m}_{rna}
BATCH2 = "new/mut/folds_2026_09_08_16_18"            # {m}_{rna}
B1_MUTS = ["a59p","g25e","g25ek30h","g27d","g27dk30h","g27dk30hq58m","g27t",
           "g27tk30h","g27tk30hq58m","k30h","k30hq58m","k60r","m132d","m132e"]
B2_MUTS = ["q58m","r28a","r28s","t31i","t31l","t31v","wt","y32f"]

def dmut(name):
    if name in B1_MUTS: return f"{BATCH1}/{name}"
    return f"{BATCH2}/{name}"

def base_atoms(atoms):
    return [a for a in atoms if a.get("atom_site.label_atom_id") not in MAINCHAIN_RNA]

def pick(atoms, names):
    return [a for a in atoms if a.get("atom_site.label_atom_id") in names]

def process(dirname):
    """返回 (d_C4N4_E72, d_base_E72, zinc_pairwise) 的 5-model 均值"""
    d_c4n4, d_base = [], []
    zinc = defaultdict(list)
    for jf in sorted(glob.glob(os.path.join(dirname, "*full_data*.json"))):
        cif = jf.replace("full_data", "model").replace(".json", ".cif")
        if not os.path.exists(cif): continue
        cols, atoms = U.parse_atom_site(cif)
        prot = U.residues_by_chain(atoms, U.PROT_CHAIN)
        c0 = base_atoms(U.atoms_of(atoms, U.RNA_CHAIN, C0_RESI))
        if not c0: continue
        e72 = pick(prot.get(E72, []), ("OE1", "OE2"))
        c4n4 = pick(c0, ("C4", "N4"))
        if e72:
            if c4n4: d_c4n4.append(U.min_dist(c4n4, e72))
            d_base.append(U.min_dist(c0, e72))
        # 锌配位残基侧链配位原子两两距离
        coord = {}
        for r, names in ZINC.items():
            at = pick(prot.get(r, []), names)
            if at: coord[r] = at
        keys = sorted(coord)
        for i in range(len(keys)):
            for j in range(i+1, len(keys)):
                d = U.min_dist(coord[keys[i]], coord[keys[j]])
                if d is not None:
                    zinc[f"{keys[i]}-{keys[j]}"].append(d)
    mean = lambda xs: sum(xs)/len(xs) if xs else None
    return (mean(d_c4n4), mean(d_base), {k: mean(v) for k, v in zinc.items()})

# ---------- 1. 全部 22 个突变体 ----------
ALL = B1_MUTS + B2_MUTS
res = {}
for m in ALL:
    gc = process(dmut(m) + "_gcg")
    ga = process(dmut(m) + "_gca")
    res[m] = dict(
        d_gcg_c4n4=gc[0], d_gca_c4n4=ga[0],
        d_gcg_base=gc[1], d_gca_base=ga[1],
        zinc_gcg=gc[2], zinc_gca=ga[2],
    )
    r = res[m]
    r["dd_c4n4"] = (r["d_gca_c4n4"] - r["d_gcg_c4n4"]) if (r["d_gca_c4n4"] and r["d_gcg_c4n4"]) else None
    r["dd_base"] = (r["d_gca_base"] - r["d_gcg_base"]) if (r["d_gca_base"] and r["d_gcg_base"]) else None

# ---------- 2. 实测 +1 比 ----------
MEAS = {
    "wt":1.37, "k30h":1.71, "g25e":1.55, "g27d":1.53, "q58m":1.46, "g27t":1.45,
    "m132d":1.42, "m132e":1.18, "y32f":1.47,
    "g25ek30h":2.27, "g27dk30h":2.11, "g27tk30hq58m":2.16, "k30hq58m":1.69,
}

print("="*104)
print("表1  22 个突变体的 Δd_E72（= d_E72(GCA) − d_E72(GCG)，Å；正则排A几何）")
print("="*104)
print(f"{'突变':<16}{'d_GCG(C4N4–E72)':>17}{'d_GCA(C4N4–E72)':>17}{'Δd_E72':>10}{'实测+1比':>10}")
for m in ALL:
    r = res[m]
    f = lambda v: f"{v:.2f}" if v is not None else "-"
    meas = f"{MEAS[m]:.2f}" if m in MEAS else "-"
    star = "★" if m in ("g27tk30hq58m","g27dk30hq58m") else " "
    print(f"{star}{m:<15}{f(r['d_gcg_c4n4']):>17}{f(r['d_gca_c4n4']):>17}{f(r['dd_c4n4']):>10}{meas:>10}")

# ---------- 3. 回归 ----------
xs, ys, names = [], [], []
for m in ALL:
    if m in MEAS and res[m]["dd_c4n4"] is not None:
        xs.append(res[m]["dd_c4n4"]); ys.append(MEAS[m]); names.append(m)
n = len(xs)
mx, my = sum(xs)/n, sum(ys)/n
sxy = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
sxx = sum((x-mx)**2 for x in xs); syy = sum((y-my)**2 for y in ys)
r_pearson = sxy/math.sqrt(sxx*syy)
# Fisher z 95% CI
z = math.atanh(r_pearson); se = 1/math.sqrt(n-3)
lo, hi = math.tanh(z-1.96*se), math.tanh(z+1.96*se)
# p 值（t 近似）
t = r_pearson*math.sqrt((n-2)/(1-r_pearson**2)) if abs(r_pearson) < 1 else float('inf')
# 秩相关
def rank(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0]*len(v)
    for pos, i in enumerate(order): rk[i] = pos+1
    return rk
rx, ry = rank(xs), rank(ys)
mrx, mry = sum(rx)/n, sum(ry)/n
r_spear = sum((a-mrx)*(b-mry) for a, b in zip(rx, ry))/math.sqrt(sum((a-mrx)**2 for a in rx)*sum((b-mry)**2 for b in ry))
slope = sxy/sxx; intercept = my - slope*mx

print()
print("="*104)
print(f"表2  回归：Δd_E72 vs 实测 +1 比   (n={n})")
print("="*104)
print(f"  样本: {', '.join(names)}")
print(f"  Pearson r = {r_pearson:+.3f}   95% CI = [{lo:+.3f}, {hi:+.3f}]   t = {t:+.2f}")
print(f"  Spearman ρ = {r_spear:+.3f}")
print(f"  线性拟合: +1比 = {slope:+.4f} × Δd_E72 + {intercept:.3f}")
# 留一交叉验证
loo = []
for i in range(n):
    xs2 = xs[:i]+xs[i+1:]; ys2 = ys[:i]+ys[i+1:]
    mx2, my2 = sum(xs2)/len(xs2), sum(ys2)/len(ys2)
    sxy2 = sum((a-mx2)*(b-my2) for a, b in zip(xs2, ys2)); sxx2 = sum((a-mx2)**2 for a in xs2)
    sl2 = sxy2/sxx2; it2 = my2 - sl2*mx2
    loo.append(sl2*xs[i]+it2 - ys[i])
print(f"  留一法(LOO) 预测残差均值={sum(loo)/n:+.2f}, RMSE={math.sqrt(sum(e*e for e in loo)/n):.2f}")

# 存 CSV
with open("results/dE72_regression.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["mut","d_GCG_C4N4_E72","d_GCA_C4N4_E72","delta_d_E72",
                "d_GCG_base_E72","d_GCA_base_E72","delta_d_base_E72","measured_ratio"])
    for m in ALL:
        r = res[m]
        w.writerow([m,
                    round(r["d_gcg_c4n4"],3) if r["d_gcg_c4n4"] else "",
                    round(r["d_gca_c4n4"],3) if r["d_gca_c4n4"] else "",
                    round(r["dd_c4n4"],3) if r["dd_c4n4"] is not None else "",
                    round(r["d_gcg_base"],3) if r["d_gcg_base"] else "",
                    round(r["d_gca_base"],3) if r["d_gca_base"] else "",
                    round(r["dd_base"],3) if r["dd_base"] is not None else "",
                    MEAS.get(m,"")])

# ---------- 4. 锌配位完整性 ----------
print()
print("="*104)
print("表3  锌配位完整性：H70–C102 / H70–C105 / C102–C105 配位原子距离（Å）")
print("="*104)
print(f"{'突变':<16}{'H70–C102':>10}{'H70–C105':>10}{'C102–C105':>11}   {'GCG/GCA':<8}判读")
zrows=[]
for m in ALL:
    r = res[m]
    for motif, zz in (("GCG", r["zinc_gcg"]), ("GCA", r["zinc_gca"])):
        vals = [zz.get("70-102"), zz.get("70-105"), zz.get("102-105")]
        zrows.append([m, motif] + [round(v,2) if v else "" for v in vals])
# 打印 WT 与三点
for m in ["wt","g27tk30hq58m","g27dk30hq58m"]:
    r = res[m]
    for motif, zz in (("GCG", r["zinc_gcg"]), ("GCA", r["zinc_gca"])):
        v = [zz.get("70-102"), zz.get("70-105"), zz.get("102-105")]
        s = "  ".join(f"{x:.2f}" if x else "-" for x in v)
        print(f"{m:<16}{'':>10}{'':>10}{'':>11}   {motif:<8}{s}")

with open("results/zinc_coordination.csv","w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["mut","motif","H70_C102","H70_C105","C102_C105"])
    for row in zrows: w.writerow(row)

# 全局：所有突变体锌配位 vs WT 的偏差
print()
print("=== 锌配位偏离 WT 最大的突变体（GCG，按最大偏差排序）===")
wt_z = res["wt"]["zinc_gcg"]
devs=[]
for m in ALL:
    zz = res[m]["zinc_gcg"]
    dmax=0
    for k in ("70-102","70-105","102-105"):
        a,b = wt_z.get(k), zz.get(k)
        if a and b: dmax=max(dmax, abs(a-b))
    devs.append((m,dmax))
for m,d in sorted(devs,key=lambda x:-x[1])[:8]:
    print(f"  {m:<16} 最大偏差 {d:.2f} Å")

print("\n写入 results/dE72_regression.csv, results/zinc_coordination.csv")

# ---------- 5. 散点图 ----------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"]=["Microsoft YaHei","SimHei","DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"]=False
    fig, ax = plt.subplots(figsize=(7,5.2), dpi=150)
    ax.scatter(xs, ys, s=55, c="#2E548B", zorder=3)
    for x,y,nm in zip(xs,ys,names):
        ax.annotate(nm, (x,y), textcoords="offset points", xytext=(6,4), fontsize=8)
    xr=[min(xs),max(xs)]
    ax.plot(xr,[slope*x+intercept for x in xr],"--",c="#C0392B",lw=1.4,
            label=f"r={r_pearson:+.3f}  95%CI[{lo:+.2f},{hi:+.2f}]  n={n}")
    ax.set_xlabel("Δd_E72 = d_E72(GCA) − d_E72(GCG)  (Å)")
    ax.set_ylabel("实测 +1 比 (GCG/GCA)")
    ax.set_title("突变体催化几何判别 vs 实测 +1 特异性")
    ax.legend(fontsize=9); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig("results/dE72_scatter.png")
    print("写入 results/dE72_scatter.png")
except Exception as e:
    print("绘图跳过:", e)
