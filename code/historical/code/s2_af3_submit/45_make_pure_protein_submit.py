# -*- coding: utf-8 -*-
"""
阶段 45 —— 生成「纯蛋白模型」AF3 提交文件（只给蛋白链，不给 RNA），共 60 个单 seed JSON

目标：验证「纯蛋白质内部的 CP」能否把不同功能类别的突变体分开聚类，
      并与复合物模型（含 RNA）的结论对照 —— 判断 CP 偏离是蛋白自身折叠变化，还是 RNA 诱导的。

文件分配（60 = 20 + 10 × 4）：
  WT                      20 个 seed（重建零假设，与复合物模型口径一致）
  每个突变体               4 个 seed

构建体（10 个）：
  ── 核心对照（有活性数据）──
  M132D              活性 0.89
  M132E              活性 0.83
  K30H               活性 0.84
  G27T-K30H-Q58M     活性 0.77（复合物模型中偏离最大者，关键反例）
  ── 完全失活组（活性 0.000）──
  T31D               ＋1 阅读器位点
  N57W               催化必需残基
  G27D-M130G         失活组合
  ── 同位点活性对照 ──
  T31A               活性 0.970（与 T31D 同为位点 31）
  ── 新失活对照（未测活性，机制更干净）──
  N57A               与 N57W 同位点、扰动最小
  E72A               催化碱，APOBEC 领域标准阴性对照

产出：af3_submit_pure/（60 个 JSON，每个 1 个 seed）+ _提交清单.csv
用法：uv run python 45_make_pure_protein_submit.py
"""
import json, os, sys, glob, csv, shutil
sys.stdout.reconfigure(encoding="utf-8")

OUT = "af3_submit_pure"
WT_SEEDS = range(1, 21)      # 20 个
MUT_SEEDS = range(1, 5)      # 各 4 个

# 构建体：(文件名基, 突变字典, 湿实验活性, 说明)
PANEL = [
    ("M132D",           {132: "D"},              0.89,  "核心对照·出口通道"),
    ("M132E",           {132: "E"},              0.83,  "核心对照·出口通道（132D 的安全对照臂）"),
    ("K30H",            {30: "H"},               0.84,  "核心对照·最佳单点"),
    ("G27TK30HQ58M",    {27: "T", 30: "H", 58: "M"}, 0.77, "核心对照·复合物模型中偏离最大（关键反例）"),
    ("T31D",            {31: "D"},               0.000, "★完全失活·＋1 阅读器位点"),
    ("N57W",            {57: "W"},               0.000, "★完全失活·催化必需残基"),
    ("G27DM130G",       {27: "D", 130: "G"},     0.000, "★完全失活·组合"),
    ("T31A",            {31: "A"},               0.970, "★同位点活性对照（与 T31D 同为位点 31）"),
    ("N57A",            {57: "A"},               None,  "新失活对照·与 N57W 同位点、扰动最小"),
    ("E72A",            {72: "A"},               None,  "新失活对照·催化碱（领域标准）"),
]

ref = sorted(glob.glob("af3_submit/WT_GCG.json"))
WT_SEQ = json.load(open(ref[0], encoding="utf-8"))[0]["sequences"][0]["proteinChain"]["sequence"]
assert len(WT_SEQ) == 199, f"序列长度异常：{len(WT_SEQ)}"


def apply_muts(seq, muts):
    s = list(seq)
    for pos, aa in muts.items():
        s[pos - 1] = aa
    return "".join(s)


# 清空旧的同名输出（避免残留），但保留归档目录
if os.path.isdir(OUT):
    for f in glob.glob(os.path.join(OUT, "*.json")):
        os.remove(f)
os.makedirs(OUT, exist_ok=True)

print("位点核对（1-based，WT 残基 -> 突变）：")
for name, muts, act, why in PANEL:
    for pos, aa in sorted(muts.items()):
        got = WT_SEQ[pos - 1]
        print(f"  {name:<16} pos{pos}: {got} -> {aa}   {'✓' if got != aa else '✗ 与 WT 相同！'}")
print()


def emit(base, seq, seeds, label, note):
    made = []
    for s in seeds:
        job = [{
            "name": f"{base}_s{int(s):02d}",
            "modelSeeds": [str(s)],
            "sequences": [{
                "proteinChain": {"sequence": seq, "count": 1,
                                 "useStructureTemplate": True}
            }],
            "dialect": "alphafoldserver",
            "version": 3,
        }]
        p = os.path.join(OUT, f"{base}_s{int(s):02d}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=1, ensure_ascii=False)
        made.append(p)
    return made


rows = []
for p in emit("WT_pure", WT_SEQ, WT_SEEDS, "WT", "野生型（纯蛋白）"):
    rows.append([os.path.basename(p), "WT", "WT（纯蛋白）", "", "P0"])
for name, muts, act, why in PANEL:
    seq = apply_muts(WT_SEQ, muts)
    for p in emit(f"{name}_pure", seq, MUT_SEEDS, name, why):
        rows.append([os.path.basename(p), name, why,
                     "" if act is None else f"{act:.3f}", "P0"])

with open(os.path.join(OUT, "_提交清单.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["文件名", "构建体", "说明", "湿实验活性", "优先级"])
    w.writerows(rows)

n_json = len(glob.glob(os.path.join(OUT, "*.json")))
print(f"生成 {n_json} 个 JSON（每个 1 个 seed）")
print(f"  WT           : {len(list(WT_SEEDS))} 个 seed -> WT_pure_s01..s{max(WT_SEEDS):02d}")
for name, muts, act, why in PANEL:
    print(f"  {name:<16}: {len(list(MUT_SEEDS))} 个 seed -> {name}_pure_s01..s{max(MUT_SEEDS):02d}")
print(f"\n清单：{OUT}/_提交清单.csv")
print("提交后把结果放到 new/protein_only/ 下（目录名随意，分析脚本按蛋白序列自动归类）。")
