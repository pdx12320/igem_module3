# -*- coding: utf-8 -*-
"""
阶段 13 —— PSSM 可突变方向预测 与 湿实验 逐突变核对（可信度/有效性评估）

方法：
  - PSSM：从 AF3 MSA 算每个位点的氨基酸分布；某 AA 频率 ≥1% 判为「允许方向」，<1% 判为「禁止方向」。
  - 实验：GCG_388 保留率 ≥50% 判「活性」，<50% 判「失活」。
  - 逐突变核对，构建混淆矩阵，计算准确率/精确率/召回率。

产出：results/pssm_validation.csv（逐突变）、results/pssm_confusion.csv（混淆矩阵）
"""
import csv
from collections import Counter
import statistics

import openpyxl

SRC = r"data\external\01a060f6-dcce-73d7-adda-b71c6d3f7f51.xlsx"
A3M = "GUGCGCG_20/001/msas/fold_001_paired_msa_chains_a.a3m"
AA = "ACDEFGHIKLMNPQRSTVWY"
PSSM_CUT = 0.01       # 允许方向阈值：家族频率 ≥1%
RET_CUT = 0.5         # 活性阈值：保留率 ≥50%


def read_a3m(path):
    seqs, cur = [], None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if cur is not None:
                    seqs.append(cur)
                cur = []
            elif cur is not None:
                cur.append(line)
    if cur is not None:
        seqs.append(cur)
    query = "".join(seqs[0]).upper()
    aligned = [s for s in ["".join(ch for ch in "".join(s) if not ch.islower()).replace(".", "-") for s in seqs]
               if len(s) == len(query)]
    return query, aligned


query, aligned = read_a3m(A3M)
L = len(query)

# PSSM：每个位点 AA 频率
pssm = {}
for j in range(L):
    cnt = Counter(aligned[i][j] for i in range(len(aligned)) if aligned[i][j] != "-")
    tot = sum(cnt.values())
    pssm[j + 1] = {aa: cnt.get(aa, 0) / tot for aa in AA}

# 实验数据
wb = openpyxl.load_workbook(SRC, data_only=True)
ws = wb["Sheet1"]
data = {}
for row in ws.iter_rows(values_only=True):
    if row[0] is None or row[1] is None:
        continue
    n = str(row[0]).strip()
    if n == "ACA_295":
        continue
    data.setdefault(n, []).append((row[1], row[2], row[3]))

wt_gcg = statistics.mean([r[1] for r in data["PUF12-9 WT"]])


def parse_mut(name):
    """'25C' -> (25, 'C')"""
    if "WT" in name:
        return None
    pos = int("".join(ch for ch in name if ch.isdigit()))
    aa = name[-1]
    return pos, aa


rows = []
conf = {"TP": 0, "TN": 0, "FP": 0, "FN": 0}  # 正=失活
# 语义：预测「禁止方向→失活」。 TP=禁止且失活, TN=允许且活性, FP=禁止但活性, FN=允许但失活
for name, reps in data.items():
    m = parse_mut(name)
    if m is None:
        continue
    pos, aa = m
    gcg = statistics.mean([r[1] for r in reps])
    retain = gcg / wt_gcg
    freq = pssm.get(pos, {}).get(aa, 0.0)
    pcls = "允许" if freq >= PSSM_CUT else "禁止"
    ecls = "活性" if retain >= RET_CUT else "失活"
    if pcls == "禁止" and ecls == "失活":
        conf["TP"] += 1
    elif pcls == "允许" and ecls == "活性":
        conf["TN"] += 1
    elif pcls == "禁止" and ecls == "活性":
        conf["FP"] += 1
    else:
        conf["FN"] += 1
    rows.append(dict(mut=name, pos=pos, wt=query[pos-1], aa=aa,
                     pssm_freq=round(freq, 4), pssm=pcls,
                     gcg=round(gcg, 3), retain=round(retain, 2), exp=ecls,
                     match="✓" if pcls != ecls.replace("失活","禁止").replace("活性","允许") else "✗"))

# 修正 match 判断（禁止↔失活 或 允许↔活性 为一致）
for r in rows:
    r["match"] = "✓一致" if (r["pssm"] == "禁止" and r["exp"] == "失活") or (r["pssm"] == "允许" and r["exp"] == "活性") else "✗不一致"

with open("results/pssm_validation.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["mut", "pos", "wt", "aa", "pssm_freq", "pssm", "gcg", "retain", "exp", "match"])
    w.writeheader()
    w.writerows(rows)

# 汇总
n = conf["TP"] + conf["TN"] + conf["FP"] + conf["FN"]
acc = (conf["TP"] + conf["TN"]) / n
# 「禁止→失活」的精确率/召回率
prec_disallow = conf["TP"] / (conf["TP"] + conf["FP"]) if (conf["TP"] + conf["FP"]) else 0
recall_disallow = conf["TP"] / (conf["TP"] + conf["FN"]) if (conf["TP"] + conf["FN"]) else 0

print(f"== PSSM 预测 逐突变核对（PSSM≥1%=允许 / 保留≥50%=活性）==")
print(f"总突变数: {n}")
print(f"\n混淆矩阵（预测: 禁止=会失活, 允许=活性）:")
print(f"                        实际失活   实际活性")
print(f"  预测禁止(会失活):     {conf['TP']:>4}      {conf['FP']:>4}")
print(f"  预测允许(活性):       {conf['FN']:>4}      {conf['TN']:>4}")
print(f"\n准确率 = {acc:.1%}")
print(f"「禁止方向→失活」精确率 = {prec_disallow:.1%}（预测失活里真失活比例）")
print(f"「禁止方向→失活」召回率 = {recall_disallow:.1%}（真失活里被预测到比例）")

print(f"\n== 不一致的突变（PSSM 判错）==")
for r in rows:
    if r["match"] == "✗不一致":
        print(f"  {r['mut']:<6} WT={r['wt']}→{r['aa']} PSSM={r['pssm']}({r['pssm_freq']}) "
              f"实验={r['exp']}(GCG={r['gcg']},保留{r['retain']:.0%})")

with open("results/pssm_confusion.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["metric", "value"])
    w.writerow(["total", n])
    w.writerow(["TP(禁止&失活)", conf["TP"]])
    w.writerow(["TN(允许&活性)", conf["TN"]])
    w.writerow(["FP(禁止但活性)", conf["FP"]])
    w.writerow(["FN(允许但失活)", conf["FN"]])
    w.writerow(["accuracy", round(acc, 3)])
    w.writerow(["precision_disallow", round(prec_disallow, 3)])
    w.writerow(["recall_disallow", round(recall_disallow, 3)])

print(f"\n写入 results/pssm_validation.csv, results/pssm_confusion.csv")
