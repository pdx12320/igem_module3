# -*- coding: utf-8 -*-
"""
阶段 26 —— 「突变 × 脱靶位点」矩阵
横轴 = 每个不同的脱靶位点（C→T，freq≥5%，排除 on-target 388）
纵轴 = 每个突变体（a/b 重复取均值）
单元格 = 该位点平均编辑频率（%），空 = 未检出

产出：results/offtarget_matrix.csv          完整矩阵（含 motif 注释行）
      results/offtarget_matrix_heatmap.png  热图
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

# ---- 收集 ----
data = {}
for f in sorted(glob.glob("Seq/Var/*.var.xls")):
    if ".filt." in f: continue
    n = os.path.basename(f).replace(".var.xls", "")
    data[n] = dict(mut=mut_of(n), sites=parse(f))

by_mut = defaultdict(list)
for s in data.values(): by_mut[s["mut"]].append(s["sites"])

# 全部脱靶位点
allpos = set()
for sites in by_mut.values():
    for st in sites:
        for p in st:
            if p != ON: allpos.add(p)
allpos = sorted(allpos)

# 列排序：按跨突变总编辑量降序（最普遍的脱靶位点在左）
col_tot = {p: sum(st.get(p, 0.0) for st in [x for ss in by_mut.values() for x in ss]) for p in allpos}
# 重新按突变聚合算列总计
col_tot = {}
for p in allpos:
    tot = 0.0
    for ss in by_mut.values():
        for st in ss:
            tot += st.get(p, 0.0)
    col_tot[p] = tot
order_pos = sorted(allpos, key=lambda p: -col_tot[p])

# 行排序：按脱靶负荷 Σoff 降序（最混杂的在上）
row_stat = []
for mut, ss in by_mut.items():
    on = statistics.mean([st.get(ON, 0) for st in ss])
    load = statistics.mean([sum(v for k, v in st.items() if k != ON) for st in ss])
    n_off = statistics.mean([sum(1 for k in st if k != ON) for st in ss])
    row_stat.append((mut, on, load, n_off))
row_stat.sort(key=lambda x: -x[2])

# ---- 输出 CSV ----
with open("results/offtarget_matrix.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["mutation", "on_388(%)", "off_load(%)", "n_off"] + [f"{p}" for p in order_pos])
    w.writerow(["motif", "", "", ""] + [motif(p) for p in order_pos])
    for mut, on, load, n_off in row_stat:
        ss = by_mut[mut]
        vals = []
        for p in order_pos:
            fr = [st[p] for st in ss if p in st]
            vals.append(f"{statistics.mean(fr)*100:.1f}" if fr else "")
        w.writerow([mut, f"{on*100:.1f}", f"{load*100:.0f}", f"{n_off:.0f}"] + vals)

# ---- 控制台：关键突变的脱靶谱（可读版，取前 30 个位点）----
KEY = ["PUF12-9", "P4-SNE", "P7-SNE", "P8-GVD", "32F", "25E-58M",
       "27T-30H-58M", "32F-132E", "25E-27D", "27T-32F", "30H-58M", "27T-32F-132E"]
show_pos = order_pos[:30]
d = {m: dict(zip([r[0] for r in row_stat], row_stat)) for m in KEY}
print(f"共 {len(allpos)} 个脱靶位点 × {len(row_stat)} 个突变体（完整矩阵见 CSV）")
print(f"下表：编辑频率 %（仅显示跨突变最普遍的 30 个位点，motif 标注于位点下方）\n")
hdr1 = "突变".ljust(16)
for p in show_pos: hdr1 += f"{p:>6}"
print(hdr1)
hdr2 = "".ljust(16)
for p in show_pos: hdr2 += f"{motif(p):>6}"
print(hdr2)
print("-" * len(hdr1))
for mut in KEY:
    if mut not in by_mut: continue
    ss = by_mut[mut]
    line = mut.ljust(16)
    for p in show_pos:
        fr = [st[p] for st in ss if p in st]
        line += f"{statistics.mean(fr)*100:>6.0f}" if fr else f"{'·':>6}"
    print(line)
print("\n注：数值 = 平均编辑频率(%), · = 未检出(<5%)；完整 74 位点矩阵见 results/offtarget_matrix.csv")

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
    fig, ax = plt.subplots(figsize=(20, 12), dpi=150)
    im = ax.imshow(M, aspect="auto", cmap="YlOrRd", vmin=0, vmax=45)
    ax.set_xticks(range(len(order_pos)))
    ax.set_xticklabels([f"{p}\n{motif(p)}" for p in order_pos], fontsize=5.5, rotation=90)
    ax.set_yticks(range(len(row_stat)))
    ax.set_yticklabels([f"{m}  (on={o*100:.0f}%,Σ={l*100:.0f})" for m, o, l, _ in row_stat], fontsize=7)
    # 标注高值
    for i in range(len(row_stat)):
        for j in range(len(order_pos)):
            if not np.isnan(M[i, j]) and M[i, j] >= 20:
                ax.text(j, i, f"{M[i,j]:.0f}", ha="center", va="center", fontsize=4.5, color="black")
    cb = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    cb.set_label("编辑频率 %", fontsize=9)
    ax.set_xlabel("脱靶位点（位置 + motif）—— 按跨突变总编辑量降序", fontsize=11)
    ax.set_ylabel("突变体（按脱靶负荷 Σoff 降序）", fontsize=11)
    ax.set_title("各突变体的脱靶谱矩阵（C→T，freq≥5%；on-target 388 未列入）", fontsize=13, pad=12)
    fig.tight_layout()
    fig.savefig("results/offtarget_matrix_heatmap.png")
    print("写入 results/offtarget_matrix_heatmap.png")
except Exception as e:
    print("绘图跳过:", e)
