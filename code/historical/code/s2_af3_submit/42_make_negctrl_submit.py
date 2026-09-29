# -*- coding: utf-8 -*-
"""
阶段 42 —— 生成「阴性对照」AF3 提交文件（用于加入 PCA 与偏离诊断）

为什么必须新提交：
  工作区 22 个已建模构建体与「完全失活组」完全不相交——
  失活的 T31D/T31Y/N57W 等没有模型，而有模型的 T31I/L/V 等没有湿数据。

面板设计（每组都对应一个可判定的问题）：
  ── 完全失活组（有湿数据，activity_retention = 0）──
  T31D        位点 31，活性 0.000（GCG 0.001%，深度 980）
  N57W        位点 57 催化必需，活性 0.000（GCG 0.002%，深度 1328）
  27D-130G    失活组合，活性 0.000（两重复深度 2494 / 3655，C388 均为 0）
  ── ★ 关键同位点活性对照 ──
  T31A        与 T31D 同为位点 31，但活性 0.97（GCG 0.501%）
              → 若 T31A 与 T31D 的 CP 偏离相近，则证明 CP 偏离反映「改了哪个位点」而非「功能后果」
  ── 机制更干净的新失活对照 ──
  N57A        与 N57W 同位点，只去掉酰胺基、体积最小
              → 区分「偏离来自大侧链 Trp」还是「来自位点 57 本身」
  E72A        催化碱（general base），APOBEC 领域标准阴性对照；保守性 >90%

共 6 个构建体 × {GCG, GCA} = 12 个作业，每个 5 个 seed（提供 5 个独立单位）。
产出目录：af3_submit_negctrl/
用法：uv run python 42_make_negctrl_submit.py
"""
import json, os, sys, glob
sys.stdout.reconfigure(encoding="utf-8")

OUT = "af3_submit_negctrl"
os.makedirs(OUT, exist_ok=True)
SEEDS = range(1, 6)          # 每个构建体 5 个 seed

ref = sorted(glob.glob("af3_submit/WT_GCG.json"))
WT_SEQ = json.load(open(ref[0], encoding="utf-8"))[0]["sequences"][0]["proteinChain"]["sequence"]
assert len(WT_SEQ) == 199

# 名称 -> (突变字典, 湿实验活性, 分类)
PANEL = [
    ("T31D",     {31: "D"},              0.000, "完全失活（＋1 阅读器位点）", "P0"),
    ("N57W",     {57: "W"},              0.000, "完全失活（催化必需残基）", "P0"),
    ("G27D-M130G", {27: "D", 130: "G"},  0.000, "完全失活（组合）", "P0"),
    ("T31A",     {31: "A"},              0.970, "★ 同位点活性对照（与 T31D 同位点、结果相反）", "P0"),
    ("N57A",     {57: "A"},              None,  "新失活对照（比 N57W 更小的扰动）", "P1"),
    ("E72A",     {72: "A"},              None,  "新失活对照（催化碱，领域标准）", "P1"),
]
# 用于生成文件名（避免与既有命名混淆）
FNAME = {"G27D-M130G": "G27DM130G"}


def apply_muts(seq, muts):
    s = list(seq)
    for pos, aa in muts.items():
        s[pos - 1] = aa
    return "".join(s)


print("位点核对（1-based，WT 残基 -> 突变）：")
for name, muts, act, why, pri in PANEL:
    for pos, aa in muts.items():
        print(f"  {name:<14} pos{pos}: {WT_SEQ[pos-1]} -> {aa}   "
              f"{'✓' if WT_SEQ[pos-1] != aa else '✗ 与 WT 相同！'}")
print()

made = []
for name, muts, act, why, pri in PANEL:
    seq = apply_muts(WT_SEQ, muts)
    for rna_tag, rna in [("GCG", "GUGCGCG"), ("GCA", "GUGCACG")]:
        job = [{
            "name": f"{FNAME.get(name, name)}_{rna_tag}",
            "modelSeeds": [str(s) for s in SEEDS],
            "sequences": [
                {"proteinChain": {"sequence": seq, "count": 1,
                                  "useStructureTemplate": True}},
                {"rnaSequence": {"sequence": rna, "count": 1}},
            ],
            "dialect": "alphafoldserver",
            "version": 3,
        }]
        p = os.path.join(OUT, f"{FNAME.get(name, name)}_{rna_tag}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=1, ensure_ascii=False)
        made.append((pri, name, rna_tag, act, why, p))

print(f"生成 {len(made)} 个作业文件（每个 {len(list(SEEDS))} 个 seed）：")
print(f"{'优先级':<6}{'构建体':<14}{'RNA':<5}{'实测活性':>9}  文件")
for pri, name, tag, act, why, p in made:
    a = "—" if act is None else f"{act:.3f}"
    print(f"{pri:<6}{name:<14}{tag:<5}{a:>9}  {p}")

with open(os.path.join(OUT, "_panel.csv"), "w", encoding="utf-8-sig") as f:
    f.write("priority,construct,rna,activity_retention,rationale\n")
    for pri, name, tag, act, why, p in made:
        f.write(f"{pri},{name},{tag},{'' if act is None else act},{why}\n")

print(f"\n面板清单另存 {OUT}/_panel.csv")
print("提交后把下载结果放到 new/negctrl/ 下（目录名随意，脚本 43 按蛋白序列自动归类）。")
