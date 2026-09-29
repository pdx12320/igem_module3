# -*- coding: utf-8 -*-
"""
阶段 18 —— 生成 AF3 server 提交 JSON：突变 APOBEC × GUGCGCG / GUGCACG

对每个单点/组合突变，生成两份 JSON（突变蛋白 + GCG；突变蛋白 + GCA），
供提交后重新做 CP/ΔCP 分析，对比 WT 的 +1 判别是否被突变改变。

产出：af3_submit/*.json
"""
import json
import os

WT = ("MEASPASGPRHLMDPAIFTSNFNNGIGRHKTYLCYEVERLDNGTSVKMDQHRGFLHNQAKNLLCGFYGR"
      "HVEVNFIKKFTSERDFHPSMSCSITWFLSWSPCWECSQAIREFLSRHPGVTLVIYVARLFWHMDQQNR"
      "QGLRDLVNSGVTIQIMTYDEFKHCWDTFVDHQGAPFQPWDGLDEHSQALSGRLRAILQNQGN")
assert len(WT) == 199, f"WT 长度 {len(WT)} != 199"

# 氨基酸单字母表（用于校验）
AA = "ACDEFGHIKLMNPQRSTVWY"

def parse_mut(s):
    """'K30H' -> (30, 'K', 'H')"""
    wt, num, mt = s[0], int(s[1:-1]), s[-1]
    return num, wt, mt

def apply_muts(muts_str):
    """对 WT 应用突变，返回 (名称, 突变后序列)。校验野生型残基。"""
    seq = list(WT)
    name = muts_str
    for m in muts_str.split("+"):
        pos, wt, mt = parse_mut(m)
        assert seq[pos-1] == wt, f"位点 {pos} 应为 {wt}，实际 {seq[pos-1]}（{m}）"
        seq[pos-1] = mt
    return name, "".join(seq)

# 单点突变
SINGLES = ["K30H", "G27D", "G27T", "Q58M", "G25E", "M132D", "M132E",
           "Y32F", "T31V", "T31I", "T31L", "K60R", "A59P", "R28A", "R28S"]
# 组合突变
COMBOS = ["G27T+K30H", "G27D+K30H", "K30H+Q58M",
          "G27T+K30H+Q58M", "G27D+K30H+Q58M", "G25E+K30H"]

RNA = {"GCG": "GUGCGCG", "GCA": "GUGCACG"}

OUT = "af3_submit"
os.makedirs(OUT, exist_ok=True)

def make_job(name, seq, rna, seed="1"):
    return [{
        "name": name,
        "modelSeeds": [seed],
        "sequences": [
            {"proteinChain": {"sequence": seq, "count": 1, "useStructureTemplate": True}},
            {"rnaSequence": {"sequence": rna, "count": 1}},
        ],
        "dialect": "alphafoldserver",
        "version": 3,
    }]

n = 0
all_muts = SINGLES + COMBOS
for mut in all_muts:
    name, seq = apply_muts(mut)
    for rna_key, rna_seq in RNA.items():
        job = make_job(f"{name}_{rna_key}", seq, rna_seq)
        fname = f"{name}_{rna_key}.json"
        with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
            json.dump(job, f, indent=1)
        n += 1

# 顺带生成 WT 对照（若需重新预测 WT）
for rna_key, rna_seq in RNA.items():
    job = make_job(f"WT_{rna_key}", WT, rna_seq)
    with open(os.path.join(OUT, f"WT_{rna_key}.json"), "w", encoding="utf-8") as f:
        json.dump(job, f, indent=1)
    n += 1

print(f"已生成 {n} 个 JSON 到 {OUT}/")
print(f"单点 {len(SINGLES)} 个 + 组合 {len(COMBOS)} 个 + WT，各含 GCG/GCA 两份")
print("\n示例（K30H_GCG.json）：")
print(open(os.path.join(OUT, "K30H_GCG.json"), encoding="utf-8").read())
