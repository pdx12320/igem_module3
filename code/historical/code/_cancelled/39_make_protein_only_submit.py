# -*- coding: utf-8 -*-
"""
阶段 39 —— 生成「纯蛋白模型」AF3 提交文件（只给蛋白链，不给 RNA）

目的（对照实验）：
  现有 38 的 F1/F2 特征虽只取「蛋白–蛋白」子矩阵，但它来自 蛋白+RNA 复合物模型，
  RNA 的存在会影响 AF3 的预测。本作业把 RNA 从输入中去掉，得到「纯蛋白折叠」预测，
  用于回答：突变造成的 CP 偏离，是蛋白自身折叠的变化，还是 RNA 诱导的？

提交对象（与 38 的 PCA 一致）：
  WT / M132D / M132E / K30H / G27T-K30H-Q58M

seed 设置（与既有数据对齐）：
  WT     20 seed（拆成 2 个作业 × 10 seed）→ 可重建与 38 相同的 seed 零假设
  突变体  各 10 seed（1 个作业）→ 提供 10 个独立单位（远优于现有的 1 seed）

产出目录：af3_submit_protein_only/
用法：uv run python 39_make_protein_only_submit.py
"""
import json, os, sys, glob
sys.stdout.reconfigure(encoding="utf-8")

OUT = "af3_submit_protein_only"
os.makedirs(OUT, exist_ok=True)

# 从既有作业读取 WT 序列（避免手抄出错）
ref = sorted(glob.glob("af3_submit/WT_GCG.json")) or sorted(glob.glob("af3_submit/*_GCG.json"))
if not ref:
    sys.exit("找不到 af3_submit/*.json 作为序列来源")
WT_SEQ = json.load(open(ref[0], encoding="utf-8"))[0]["sequences"][0]["proteinChain"]["sequence"]
assert len(WT_SEQ) == 199, f"序列长度异常：{len(WT_SEQ)}"

# 突变定义（1-based 位点，已按序列核对）
MUTS = {
    "WT":             {},
    "M132D":          {132: "D"},
    "M132E":          {132: "E"},
    "K30H":           {30: "H"},
    "G27T-K30H-Q58M": {27: "T", 30: "H", 58: "M"},
}
# 与既有数据的对应关系（便于核对）
CHECK = {"WT": "M", "M132D": "M", "M132E": "M", "K30H": "K", "G27T-K30H-Q58M": "G"}

def apply_muts(seq, muts):
    s = list(seq)
    for pos, aa in muts.items():
        i = pos - 1
        s[i] = aa
    return "".join(s)

def make(name, seq, seeds, fname):
    job = [{
        "name": name,
        "modelSeeds": [str(s) for s in seeds],
        "sequences": [{
            "proteinChain": {
                "sequence": seq,
                "count": 1,
                "useStructureTemplate": True,   # 与既有作业保持一致
            }
        }],
        "dialect": "alphafoldserver",
        "version": 3,
    }]
    p = os.path.join(OUT, fname)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=1, ensure_ascii=False)
    return p

print(f"WT 序列长度 {len(WT_SEQ)}，来源 {ref[0]}")
print(f"突变位点核对（1-based，括号内为 WT 残基）：")
for n, m in MUTS.items():
    for pos in m:
        got = WT_SEQ[pos - 1]
        ok = "✓" if got == CHECK[n] else "✗"
        print(f"  {n:<18} pos{pos}: {got} -> {m[pos]}  {ok}")
    if not m:
        print(f"  {n:<18} （无突变）")

print("\n生成提交文件：")
made = []
made.append(make("WT_pure_seed1-10", WT_SEQ, range(1, 11), "WT_pure_seed01-10.json"))
made.append(make("WT_pure_seed11-20", WT_SEQ, range(11, 21), "WT_pure_seed11-20.json"))
for name, muts in MUTS.items():
    if not muts:
        continue
    seq = apply_muts(WT_SEQ, muts)
    made.append(make(f"{name}_pure", seq, range(1, 11),
                     f"{name.replace('-', '')}_pure_seed01-10.json"))
for p in made:
    print("  " + p)

print(f"\n共 {len(made)} 个作业文件，覆盖 {20 + 4 * 10} 个 seed。")
print("提交后请把下载结果放到 new/protein_only/ 下（任意目录名，脚本按序列自动归类）。")
