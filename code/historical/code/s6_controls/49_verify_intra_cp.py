# -*- coding: utf-8 -*-
"""
阶段 49 —— 核验：蛋白内部 CP 到底是怎么算出来的 + 修正一处残基编号标注错误

起因：脚本 47 打印 PC 载荷最大的残基对时用的是 0-based 索引，
      而蛋白残基编号是 1-based，故此前报出的「55-73、80-84、37-50」等
      实际应为「56-74、81-85、38-51」。本脚本用 1-based 编号重算并输出。

产出：results/PC载荷_修正.csv
"""
import json, glob, os, sys, math, csv
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
import af_utils as U

PROT, RNA, TARGET_C = U.PROT_CHAIN, U.RNA_CHAIN, 4

# ===========================================================================
# 一、逐步展示「蛋白内部 CP」的提取过程
# ===========================================================================
print("=" * 100)
print("一、蛋白内部 CP 的提取过程（以 GUGCGCG_20/001 的 model_0 为例）")
print("=" * 100)

f0 = sorted(glob.glob("GUGCGCG_20/001/*full_data*.json"))[0]
j = json.load(open(f0, encoding="utf-8"))
print(f"\n源文件：{f0}")
print(f"  contact_probs 形状 = {np.asarray(j['contact_probs']).shape}")
cpm = np.asarray(j["contact_probs"], dtype=np.float64)
cids, rids = j["token_chain_ids"], j["token_res_ids"]
print(f"  token 总数 = {len(cids)}")
from collections import Counter
print(f"  链组成 = {dict(Counter(cids))}")
print(f"  蛋白链 A 的残基号范围 = {min(r for c, r in zip(cids, rids) if c == PROT)}"
      f"–{max(r for c, r in zip(cids, rids) if c == PROT)}")
print(f"  RNA 链 B 的残基号 = {sorted(r for c, r in zip(cids, rids) if c == RNA)}")

idx = np.array([i for i in range(len(cids)) if cids[i] == PROT])
sub = cpm[np.ix_(idx, idx)]
M = np.maximum(sub, sub.T)
print(f"\n  第 1 步  取 chain==A 的行列 → {sub.shape}")
print(f"  第 2 步  对称化 max(CP[i,j], CP[j,i]) → {M.shape}（= 蛋白内部 CP 矩阵）")
print(f"  第 3 步  取上三角 i<j → {len(np.triu_indices(199, k=1)[0])} 个值（F1）")
lr = np.array([(i, k) for i in range(199) for k in range(i + 5, 199)])
print(f"  第 4 步  再筛 |i−j|≥5 → {len(lr)} 个值（F2）")

# 用 1-based 残基号举几个可核对的例子
print(f"\n  几个具体值（1-based 残基号）：")
print(f"    {'残基对':<12}{'CP':>10}   说明")
for a, b, note in [(57, 99, "催化核心 N57–W99"), (70, 72, "锌配位 H70 – 催化 E72"),
                   (1, 5, "序列近邻（|i−j|=4，F2 会剔除）"),
                   (1, 6, "序列间隔 5（F2 保留）")]:
    print(f"    {f'{a}–{b}':<12}{M[a-1, b-1]:>10.4f}   {note}")

# ===========================================================================
# 二、各组「蛋白内部 CP」的总体数值（可交叉核对）
# ===========================================================================
print("\n" + "=" * 100)
print("二、各组蛋白内部 CP 的总体数值")
print("=" * 100)


def load_dir(d):
    out = []
    for f in sorted(glob.glob(os.path.join(d, "*full_data*.json"))):
        jj = json.load(open(f, encoding="utf-8"))
        c = np.asarray(jj["contact_probs"], dtype=np.float64)
        ii = np.array([t for t in range(len(jj["token_chain_ids"]))
                       if jj["token_chain_ids"][t] == PROT])
        s = c[np.ix_(ii, ii)]
        out.append(np.maximum(s, s.T))
    return out


iu = np.triu_indices(199, k=1)
lr_mask = np.array([abs(i - k) >= 5 for i, k in zip(*iu)])
GROUPS = [("WT-GCG", "GUGCGCG_20", True), ("WT-GCA", "GUGCACG_20", True),
          ("132D", "new/mut/m132d_gcg", False), ("132E", "new/mut/m132e_gcg", False),
          ("30H", "new/mut/k30h_gcg", False),
          ("27T-30H-58M", "new/mut/g27tk30hq58m_gcg", False),
          ("T31D", "new/negctrl/t31d_gcg_s01", False)]
print(f"{'组':<14}{'model数':>8}{'内部CP均值':>12}{'内部CP总和':>12}{'长程部分总和':>14}")
for name, d, is_root in GROUPS:
    if not os.path.isdir(d):
        print(f"{name:<14}   （目录不存在）"); continue
    # WT 的 json 位于 seed 子目录下，需逐个子目录读
    ms = ([m for s in sorted(x for x in glob.glob(os.path.join(d, "*")) if os.path.isdir(x))
           for m in load_dir(s)] if is_root else load_dir(d))
    if not ms:
        print(f"{name:<14}   （未读到 model）"); continue
    A = np.array([m[iu] for m in ms])
    print(f"{name:<14}{len(ms):>8}{A.mean():>12.5f}{A.sum(1).mean():>12.2f}"
          f"{A[:, lr_mask].sum(1).mean():>14.2f}")

# ===========================================================================
# 三、修正脚本 47 的残基编号（0-based → 1-based）
# ===========================================================================
print("\n" + "=" * 100)
print("三、修正：PC 载荷最大的残基对（改用 1-based 残基号）")
print("=" * 100)

W1 = [m for s in sorted(x for x in glob.glob("GUGCGCG_20/*") if os.path.isdir(x))
      for m in load_dir(s)]
W2 = [m for s in sorted(x for x in glob.glob("GUGCACG_20/*") if os.path.isdir(x))
      for m in load_dir(s)]
VARS = [("132D", "new/mut/m132d_gcg"), ("132E", "new/mut/m132e_gcg"),
        ("30H", "new/mut/k30h_gcg"), ("27T-30H-58M", "new/mut/g27tk30hq58m_gcg")]
VA = {n: load_dir(d) for n, d in VARS if os.path.isdir(d)}


def feat(md, kind):
    """kind = F1（全部 i<j）或 F2（仅 |i−j|≥5）；两者都只用蛋白内部 CP。"""
    if kind == "F1":
        return np.array([m[iu] for m in md])
    return np.array([m[iu][lr_mask] for m in md])


rows = []
for kind in ["F1", "F2"]:
    A = feat(W1, kind)
    B = feat(W2, kind)
    VV = {n: feat(v, kind) for n, v in VA.items()}
    X = np.vstack([A, B] + [VV[n] for n in VV])
    Xc = X - X.mean(0)
    _, _, Vt = np.linalg.svd(Xc, full_matrices=False)
    names = (iu[0], iu[1]) if kind == "F1" else (lr[:, 0], lr[:, 1])
    print(f"\n【{kind} 内部CP{'全' if kind=='F1' else '长程'}】PC1–PC4 载荷最大的 3 对残基（1-based）")
    for k in range(4):
        top = np.argsort(-np.abs(Vt[k]))[:3]
        desc = [f"{names[0][t]+1}-{names[1][t]+1}" for t in top]
        old = [f"{names[0][t]}-{names[1][t]}" for t in top]
        print(f"  PC{k+1}  修正后 {', '.join(desc):<24}（此前误报为 {', '.join(old)}）")
        rows.append(dict(feature=kind, PC=f"PC{k+1}",
                         corrected_1based=", ".join(desc),
                         previously_reported_0based=", ".join(old)))

with open("results/PC载荷_修正.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print("\n写入 results/PC载荷_修正.csv")
