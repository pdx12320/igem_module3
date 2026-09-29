# -*- coding: utf-8 -*-
"""
阶段 27 —— 「突变 × 脱靶位点」矩阵（去除全部 P 相关突变后重绘）

去除：所有以 P 开头的样本/突变（PUF12-9 亲本、P4-SNE、P5-TWD、P6-WFD、
      P7-THE、P7-SNE、P8-GVD）—— 即 P 系列 loop 重设计变体及其亲本。
保留：全部编号点突变组合（如 27T-30H-58M、32F-132E …）。
说明：亲本 PUF12-9 的数值仍作为水平参考标注，避免失去基线对照。

产出：results/offtarget_matrix_noP.csv
      results/offtarget_matrix_heatmap_noP.png
"""
import glob, os, re, sys, csv, statistics
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

REF = "".join(l for l in open("Seq/Bam/G22609034389-1-32F.for.ref.fa", encoding="utf-8").read().splitlines()
              if not l.startswith(">"))
L = len(REF); ON = 388; FLOOR = 0.05

def motif(p):
    i = p - 1
    return (REF[i-1] if i-1 >= 0 else "-") + "C" + (REF[i+1] if i+1 < L else "-")

def parse(p):
    out = {}
    for i, l in enumerate(open(p, encoding="latin-1")):
        if i == 0: continue
        c = l.rstrip("\n").split("\t")
        if len(c) < 11 or c[2] != "C" or c[3] != "T": continue
        try: pos, freq = int(c[1]), float(c[7])
        except ValueError: continue
        if freq >= FLOOR: out[pos] = freq
    return out

def mut_of(n):
    m = re.match(r'G\d+-(b?)(\d+)-(.*)$', n)
    return m.group(3) if m else n

# ---- 收集全部样本 ----
data = {}
for f in sorted(glob.glob("Seq/Var/*.var.xls")):
    if ".filt." in f: continue
    n = os.path.basename(f).replace(".var.xls", "")
    data[n] = dict(mut=mut_of(n), sites=parse(f))

# ---- 计算亲本参考（仍然解析，用于画参考线）----
parent_loads, parent_ons, parent_ns = [], [], []
for s in data.values():
    if s["mut"] == "PUF12-9":
        parent_ons.append(s["sites"].get(ON, 0))
        parent_loads.append(sum(v for k, v in s["sites"].items() if k != ON))
        parent_ns.append(sum(1 for k in s["sites"] if k != ON))
par_on = statistics.mean(parent_ons); par_load = statistics.mean(parent_loads)
par_n = statistics.mean(parent_ns)

# ---- 过滤：去掉一切 P 开头（PUF12-9 / P4-SNE / P5-TWD / P6-WFD / P7-THE / P7-SNE / P8-GVD）----
by_mut = defaultdict(list)
removed = set()
for s in data.values():
    if s["mut"].startswith("P"):
        removed.add(s["mut"]); continue
    by_mut[s["mut"]].append(s["sites"])

print(f"去除的 P 相关突变 ({len(removed)}): {', '.join(sorted(removed))}")
print(f"保留突变数: {len(by_mut)}")
print(f"亲本 PUF12-9 参考：on={par_on:.3f}  脱靶数={par_n:.0f}  脱靶负荷={par_load:.2f}\n")

# ---- 位点集（仅保留突变中检出的）----
allpos = sorted({p for ss in by_mut.values() for st in ss for p in st if p != ON})
col_tot = {p: sum(st.get(p, 0.0) for ss in by_mut.values() for st in ss) for p in allpos}
order_pos = sorted(allpos, key=lambda p: -col_tot[p])

# 行排序：按脱靶负荷降序
row_stat = []
for mut, ss in by_mut.items():
    on = statistics.mean([st.get(ON, 0) for st in ss])
    load = statistics.mean([sum(v for k, v in st.items() if k != ON) for st in ss])
    n_off = statistics.mean([sum(1 for k in st if k != ON) for st in ss])
    row_stat.append((mut, on, load, n_off))
row_stat.sort(key=lambda x: -x[2])

# ---- CSV ----
with open("results/offtarget_matrix_noP.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["mutation", "on_388(%)", "off_load(%)", "n_off"] + [str(p) for p in order_pos])
    w.writerow(["motif", "", "", ""] + [motif(p) for p in order_pos])
    for mut, on, load, n_off in row_stat:
        ss = by_mut[mut]
        vals = []
        for p in order_pos:
            fr = [st[p] for st in ss if p in st]
            vals.append(f"{statistics.mean(fr)*100:.1f}" if fr else "")
        w.writerow([mut, f"{on*100:.1f}", f"{load*100:.0f}", f"{n_off:.0f}"] + vals)

# ---- 控制台节选 ----
TOP = order_pos[:28]
print(f"共 {len(allpos)} 个脱靶位点 × {len(row_stat)} 个突变体（完整见 CSV）")
print("下表：编辑频率 %（前 28 个最普遍位点）\n")
h1 = "突变".ljust(18)
for p in TOP: h1 += f"{p:>6}"
print(h1)
h2 = "".ljust(18)
for p in TOP: h2 += f"{motif(p):>6}"
print(h2); print("-" * len(h1))
for mut, on, load, n_off in row_stat:
    ss = by_mut[mut]
    line = mut.ljust(18)
    for p in TOP:
        fr = [st[p] for st in ss if p in st]
        line += f"{statistics.mean(fr)*100:>6.0f}" if fr else f"{'·':>6}"
    print(line)
print(f"\n[亲本参考] PUF12-9: on={par_on*100:.0f}%  Σoff={par_load*100:.0f}%  脱靶数={par_n:.0f}")

# ---- 热图 ----
try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    M = np.full((len(row_stat), len(order_pos)), np.nan)
    for i, (mut, *_ ) in enumerate(row_stat):
        for j, p in enumerate(order_pos):
            fr = [st[p] for st in by_mut[mut] if p in st]
            if fr: M[i, j] = statistics.mean(fr) * 100
    fig, ax = plt.subplots(figsize=(19, 11), dpi=150)
    im = ax.imshow(M, aspect="auto", cmap="YlOrRd", vmin=0, vmax=45)
    ax.set_xticks(range(len(order_pos)))
    ax.set_xticklabels([f"{p}\n{motif(p)}" for p in order_pos], fontsize=5.5, rotation=90)
    ax.set_yticks(range(len(row_stat)))
    ax.set_yticklabels([f"{m}   (on={o*100:.0f}%, Σoff={l*100:.0f}%, n={n:.0f})"
                        for m, o, l, n in row_stat], fontsize=7.5)
    for i in range(len(row_stat)):
        for j in range(len(order_pos)):
            if not np.isnan(M[i, j]) and M[i, j] >= 20:
                ax.text(j, i, f"{M[i,j]:.0f}", ha="center", va="center", fontsize=5, color="black")
    cb = fig.colorbar(im, ax=ax, fraction=0.018, pad=0.01)
    cb.set_label("编辑频率 %", fontsize=9)
    # 亲本参考标注
    ax.text(0.995, -0.075, f"亲本 PUF12-9 参考：on={par_on*100:.0f}%，Σoff={par_load*100:.0f}%，脱靶数={par_n:.0f}（已从图中移除）",
            transform=ax.transAxes, ha="right", va="top", fontsize=9, color="#8E8E8E")
    ax.set_xlabel("脱靶位点（位置 + motif）—— 按跨突变总编辑量降序", fontsize=11)
    ax.set_ylabel("突变体（按脱靶负荷 Σoff 降序；已去除全部 P 相关突变）", fontsize=11)
    ax.set_title("各突变体脱靶谱矩阵 · 去 P 版（C→T，freq≥5%；on-target 388 未列入）", fontsize=13, pad=12)
    fig.tight_layout()
    fig.savefig("results/offtarget_matrix_heatmap_noP.png", bbox_inches="tight")
    print("\n写入 results/offtarget_matrix_noP.csv")
    print("写入 results/offtarget_matrix_heatmap_noP.png")
except Exception as e:
    print("绘图跳过:", e)
