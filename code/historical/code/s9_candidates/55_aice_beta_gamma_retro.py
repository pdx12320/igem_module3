# -*- coding: utf-8 -*-
"""
阶段 55 —— 回溯检验 AiCE 的 β/γ 结构约束过滤器

【检验对象】
AiCE（Gao Caixia 组, Cell 2025, DOI 10.1016/j.cell.2025.06.014）官方代码
scripts/predicted_single_HF_mutations.py 的核心过滤规则：
    -beta : Frequency threshold if SS != 'C'   （结构化区，推荐 0.8）
    -gama : Frequency threshold if SS == 'C'   （无规卷曲区，推荐 0.5）
即：逆折叠模型在某位点提名的氨基酸（该位最高频者），其采样频率必须超过阈值；
阈值随二级结构变化——结构化区严(0.8)、卷曲区松(0.5)。

【回溯检验的三个问题】
 Q1  AiCE 过滤器在这条蛋白上会提名多少个突变？分布在哪？
 Q2  它能提前剔除我们后来发现失败的突变吗？（阈值扫描 + 精确率/召回）
 Q3  它预测的是「活性」还是「+1 特异性」？（与 retain / ratio 的相关性）

【数据】
反设计采样：Apobec前期设计附件/.../全长反设计.fa   （48 条 T=0.3 采样序列 + 1 条参考）
二级结构  ：prohA1 单体 rank1 PDB → pydssp（纯 Python DSSP）
湿实验    ：results/experimental_ranking.csv（102 个单点，n=2）

【产出】results/AiCE过滤器_回溯检验.xlsx / .csv / _位点级.csv
"""
import os, re, sys, csv
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from collections import OrderedDict

FA = "Apobec前期设计附件/Apobec前期设计附件/全长反设计.fa"
PDB = ("Apobec前期设计附件/Apobec前期设计附件/prohA1单体/prohA1_monomer_63e3b/"
       "prohA1_monomer_63e3b_unrelaxed_rank_001_alphafold2_ptm_model_2_seed_000.pdb")
EXP = "results/experimental_ranking.csv"

BETA, GAMMA = 0.8, 0.5
POS, NEG = 0.70, 0.30          # 活性保留分档
WT_SEQ = ("MEASPASGPRHLMDPAIFTSNFNNGIGRHKTYLCYEVERLDNGTSVKMDQHRGFLHNQAKNLLCGFYGRHVEVNFIKKFTSERDF"
          "HPSMSCSITWFLSWSPCWECSQAIREFLSRHPGVTLVIYVARLFWHMDQQNRQGLRDLVNSGVTIQIMTYDEFKHCWDTFVDHQG"
          "APFQPWDGLDEHSQALSGRLRAILQNQGN")
assert len(WT_SEQ) == 199
AA20 = "ACDEFGHIKLMNPQRSTVWY"


def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    def rk(v):
        s = np.argsort(v); r = np.empty(len(v)); r[s] = np.arange(len(v)); return r
    a, b = rk(x), rk(y)
    a, b = a - a.mean(), b - b.mean()
    d = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    return float((a * b).sum() / d) if d > 0 else float("nan")


# ===========================================================================
# 1. 解析 ProteinMPNN 采样序列
# ===========================================================================
recs, name, buf = [], None, []
for line in open(FA, encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith(">"):
        if name is not None:
            recs.append((name, "".join(buf)))
        name, buf = line[1:], []
    else:
        buf.append(line.strip())
recs.append((name, "".join(buf)))
REF = [s for n, s in recs if "T=" not in n]
SAMP = [s for n, s in recs if "T=" in n]
print(f"读入参考序列 {len(REF)} 条、采样序列 {len(SAMP)} 条")
assert len(REF) == 1 and REF[0] == WT_SEQ
assert {len(s) for s in SAMP} == {199}

freq = np.zeros((199, 20))
for s in SAMP:
    for i, a in enumerate(s):
        if a in AA20:
            freq[i, AA20.index(a)] += 1
freq /= len(SAMP)
top_aa = [AA20[k] for k in freq.argmax(1)]
top_freq = freq.max(1)

# ===========================================================================
# 2. 二级结构（pydssp；注意其卷曲输出为 '-'，需映射为 DSSP 的 'C'）
# ===========================================================================
import pydssp
BBD = ("N", "CA", "C", "O")
byres = OrderedDict()
for line in open(PDB, encoding="utf-8"):
    if line.startswith("ATOM") and line[21] == "A":
        atom = line[12:16].strip()
        if atom in BBD:
            byres.setdefault(int(line[22:26]), {})[atom] = \
                [float(line[30:38]), float(line[38:46]), float(line[46:54])]
xyz = np.array([[a[k] for k in BBD] for a in byres.values() if all(k in a for k in BBD)],
               dtype=np.float32)
assert len(xyz) == 199, len(xyz)
ss_raw = "".join(pydssp.assign(xyz, out_type="c3"))
ss = ss_raw.replace("-", "C")                 # ★ 修正：pydssp 用 '-' 表示卷曲
print(f"二级结构：H={ss.count('H')} E={ss.count('E')} C={ss.count('C')}"
      f"   flex_ratio = {ss.count('C')/199:.3f}")

# ===========================================================================
# 3. 湿实验数据
# ===========================================================================
exp = []
for r in csv.DictReader(open(EXP, encoding="utf-8-sig")):
    m = re.match(r"^(\d+)([A-Z])$", r["mut"])
    if not m or "PUF" in r["mut"]:
        continue
    pos, mut = int(m.group(1)), m.group(2)
    exp.append(dict(mut=r["mut"], pos=pos, wt=WT_SEQ[pos - 1], mutaa=mut,
                    ratio=float(r["ratio"]) if r["ratio"] else None,
                    retain=float(r["retain"]) if r["retain"] else None,
                    depth=int(float(r["depth"])) if r["depth"] else None,
                    active=(r["active"] == "True")))
for e in exp:
    i = e["pos"] - 1
    e["freq"] = float(freq[i, AA20.index(e["mutaa"])])
    e["is_top"] = (top_aa[i] == e["mutaa"])
    e["ss"] = ss[i]
    e["thr"] = BETA if ss[i] != "C" else GAMMA
    e["pass_aice"] = e["is_top"] and e["freq"] >= e["thr"]
print(f"湿实验单点 {len(exp)} 个；活性(retain≥{POS}) {sum(1 for e in exp if e['active'])} 个\n")

# ===========================================================================
# 4. 先澄清：交接文档点名的 4 个「MPNN 强偏好但功能失败」突变
# ===========================================================================
print("=" * 104)
print("第一部分：先澄清争议 —— 交接文档点名的 4 个突变，到底测过没有？")
print("=" * 104)
CONTROV = [("H29P", 29, "P"), ("K30T", 30, "T"), ("N57D", 57, "D"), ("A59P", 59, "P")]
tested_pos = {e["pos"] for e in exp}
print(f"  {'突变':<7}{'MPNN频率':>10}{'该位最高频aa':>13}{'位点SS':>8}{'AiCE阈值':>10}"
      f"{'过β/γ':>9}{'该位已测突变':>26}")
for nm, p, m in CONTROV:
    i = p - 1
    f = float(freq[i, AA20.index(m)])
    thr = BETA if ss[i] != "C" else GAMMA
    got = sorted(e["mut"] for e in exp if e["pos"] == p)
    print(f"  {nm:<7}{f:>10.3f}{top_aa[i]:>13}{ss[i]:>8}{thr:>10.2f}"
          f"{('通过' if f >= thr else '★剔除'):>9}"
          f"{('、'.join(got) if got else '★ 一个都没测'):>26}")

# ===========================================================================
# 5. Q1：AiCE 过滤器会提名什么
# ===========================================================================
print("\n" + "=" * 104)
print("第二部分（Q1）：AiCE 过滤器在这条蛋白上的提名行为")
print("=" * 104)
nom_all, nom_filt = [], []
for i in range(199):
    if top_aa[i] == WT_SEQ[i]:
        continue
    nom_all.append((i + 1, top_aa[i], top_freq[i]))
    if top_freq[i] >= (BETA if ss[i] != "C" else GAMMA):
        nom_filt.append((i + 1, top_aa[i], top_freq[i]))
print(f"  不加阈值（只要 top aa ≠ WT）：{len(nom_all):>3} 个提名")
print(f"  加 AiCE β/γ 阈值            ：{len(nom_filt):>3} 个提名")
print(f"  → 过滤器剔除了 {len(nom_all)-len(nom_filt)} 个位点的提名")
CAND = [25, 26, 27, 28, 29, 30, 31, 32, 57, 58, 59, 60, 98, 129, 130, 131, 132, 133]
print(f"\n  我们关注的 18 个候选位点：")
print(f"  {'位点':<6}{'WT':>4}{'SS':>4}{'阈值':>6}{'top aa':>8}{'top频率':>9}  AiCE提名？")
for p in CAND:
    i = p - 1
    thr = BETA if ss[i] != "C" else GAMMA
    ok = (top_aa[i] != WT_SEQ[i]) and (top_freq[i] >= thr)
    print(f"  {p:<6}{WT_SEQ[i]:>4}{ss[i]:>4}{thr:>6.2f}{top_aa[i]:>8}{top_freq[i]:>9.3f}"
          f"  {'✓ ' + top_aa[i] if ok else ('— 未过阈值' if top_aa[i]!=WT_SEQ[i] else '— top 即 WT')}")

# ===========================================================================
# 6. Q2：阈值扫描 —— 能否预测活性
# ===========================================================================
print("\n" + "=" * 104)
print("第三部分（Q2）：用 MPNN 频率做阈值过滤，能否预测「活性保留」？")
print("=" * 104)
F = np.array([e["freq"] for e in exp])
R = np.array([e["retain"] for e in exp])
A = np.array([e["active"] for e in exp])
print(f"  Spearman(MPNN频率, 活性保留) = {spearman(F, R):+.3f}")
print(f"  Spearman(MPNN频率, +1比)     = "
      f"{spearman(F, [e['ratio'] for e in exp]):+.3f}")
print(f"\n  {'阈值':<10}{'保留数':>7}{'其中活性':>9}{'精确率':>8}{'召回率':>8}{'判定':>12}")
base = A.mean()
for thr in [0.0, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
    k = F >= thr
    if k.sum() == 0:
        print(f"  {thr:<10.2f}{0:>7}{'—':>9}{'—':>8}{'—':>8}{'':>12}")
        continue
    prec = A[k].mean()
    rec = A[k].sum() / A.sum()
    tag = ""
    if abs(thr - GAMMA) < 1e-9: tag = "← AiCE γ(卷曲)"
    if abs(thr - BETA) < 1e-9: tag = "← AiCE β(结构)"
    print(f"  {thr:<10.2f}{int(k.sum()):>7}{int(A[k].sum()):>9}{prec:>8.2f}{rec:>8.2f}{tag:>16}")
print(f"  （全量基准：{len(A)} 个，活性 {int(A.sum())}，精确率 {base:.2f}）")

# ===========================================================================
# 7. Q3：AiCE 提名集 ∩ 我们测过的突变
# ===========================================================================
print("\n" + "=" * 104)
print("第四部分（Q3）：AiCE 提名集与我们已测突变的交集")
print("=" * 104)
inter = [e for e in exp if e["pass_aice"]]
print(f"  AiCE 会提名、且我们恰好测过的突变：{len(inter)} 个")
if inter:
    print(f"  {'突变':<8}{'MPNN频率':>10}{'SS':>4}{'+1比':>8}{'活性保留':>10}{'判定':>8}")
    for e in sorted(inter, key=lambda x: -(x["retain"] or 0)):
        print(f"  {e['mut']:<8}{e['freq']:>10.3f}{e['ss']:>4}"
              f"{(e['ratio'] if e['ratio'] else float('nan')):>8.2f}"
              f"{(e['retain'] if e['retain'] is not None else float('nan')):>10.2f}"
              f"{('活性' if e['active'] else '失活'):>8}")
print(f"\n  注：AiCE 每位点只提名 1 个替换（该位最高频者），")
print(f"      而我们测的 102 个突变中只有 {sum(1 for e in exp if e['is_top'])} 个恰好是该位的最高频提名。")

# ===========================================================================
# 8. 写出
# ===========================================================================
rows = [dict(突变=e["mut"], 位点=e["pos"], WT=e["wt"], 突变aa=e["mutaa"],
             二级结构=e["ss"], 适用阈值=round(e["thr"], 2),
             MPNN频率=round(e["freq"], 4),
             该位最高频aa=top_aa[e["pos"] - 1],
             该位最高频=round(float(top_freq[e["pos"] - 1]), 4),
             是否最高频提名=("是" if e["is_top"] else "否"),
             通过AiCE过滤=("是" if e["pass_aice"] else "否"),
             GCG比=e["ratio"], 活性保留=e["retain"],
             湿实验判定=("活性" if e["active"] else "失活/低活"))
          for e in exp]
with open("results/AiCE过滤器_回溯检验.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

site_rows = []
for p in CAND:
    i = p - 1
    t = [e for e in exp if e["pos"] == p]
    thr = BETA if ss[i] != "C" else GAMMA
    site_rows.append(dict(位点=p, WT=WT_SEQ[i], 二级结构=ss[i], 适用阈值=thr,
                          MPNN最高频aa=top_aa[i], 最高频=round(float(top_freq[i]), 3),
                          AiCE是否提名=("是" if (top_aa[i] != WT_SEQ[i] and top_freq[i] >= thr) else "否"),
                          已测数=len(t), 其中活性=sum(1 for e in t if e["active"])))
with open("results/AiCE过滤器_位点级.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(site_rows[0])); w.writeheader(); w.writerows(site_rows)

try:
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active; ws.title = "1_逐突变检验"
    ws.append(list(rows[0]))
    for r in rows:
        ws.append(list(r.values()))
    ws2 = wb.create_sheet("2_位点级")
    ws2.append(list(site_rows[0]))
    for r in site_rows:
        ws2.append(list(r.values()))
    ws3 = wb.create_sheet("3_AiCE提名集")
    ws3.append(["位点", "WT", "SS", "阈值", "top aa", "top频率", "过阈值"])
    for p, a, fr in nom_all:
        thr = BETA if ss[p - 1] != "C" else GAMMA
        ws3.append([p, WT_SEQ[p - 1], ss[p - 1], thr, a, round(float(fr), 3),
                    "是" if fr >= thr else "否"])
    wb.save("results/AiCE过滤器_回溯检验.xlsx")
    print("\n写入 results/AiCE过滤器_回溯检验.xlsx")
except ImportError:
    print("\n(未装 openpyxl，仅 CSV)")
print("写入 results/AiCE过滤器_回溯检验.csv / _位点级.csv")
