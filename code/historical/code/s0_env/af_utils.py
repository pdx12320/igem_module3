# -*- coding: utf-8 -*-
"""
AF3 cif 质控 + 接触分析 共享工具（纯标准库，无第三方依赖）。

数据约定（已对照实际文件核实）：
- 蛋白链 chain A（asym_id "A"），199 残基，编号 1..199，与 FASTA 编号 1:1 对应。
- RNA 链  chain B（asym_id "B"），7 个核苷酸，编号 1..7。
- 编辑 C 为 0 位 = resi 4；+1 位 = resi 5（三个 RNA 模型一致）。
- cif 无氢原子，只有 C/N/O/P/S 重原子，故"重原子距离"= 全部原子距离。
- pLDDT 存于 _atom_site.B_iso_or_equiv 列。
"""
import json
import os

# 三个 RNA 文件夹（仅 RNA 序列不同，蛋白序列相同）
RNA_DIRS = ["GUGCGCG_20", "GUGCACG_20", "AUGCAGC_20"]

# 对应的 RNA 序列（manifest / 汇总中作为 RNA 标识，非文件夹名）
RNA_SEQS = ["GUGCGCG", "GUGCACG", "AUGCAGC"]

# +1 位残基编号（RNA 链 chain B）
PLUS1_RESI = 5

# 链标识
PROT_CHAIN = "A"
RNA_CHAIN = "B"

# 嘌呤碱基重原子（G/A 并集，程序按实际存在的原子自动取）
BASE_ATOMS = {"N9", "C8", "N7", "C5", "C6", "N6", "O6",
              "N1", "C2", "N2", "N3", "C4"}

# 碱基完整性判据：+1 为 G 或 A 时各自应具备的全部碱基重原子
PURINE_BASE = {
    "G": {"N9", "C8", "N7", "C5", "C6", "O6", "N1", "C2", "N2", "N3", "C4"},
    "A": {"N9", "C8", "N7", "C5", "C6", "N6", "N1", "C2", "N3", "C4"},
}

# 关键残基（resi -> 期望 resn）。编号已按 cif/FASTA 1:1 核对。
# 注意：交接文档中的 "R67" 应为 Y67（67 位在序列/结构中均为 Tyr，非 Arg）。
KEY_RESIDUES = {
    29: "HIS", 30: "LYS", 32: "TYR", 57: "ASN", 58: "GLN",
    59: "ALA", 60: "LYS", 67: "TYR", 68: "GLY", 69: "ARG",
    70: "HIS", 72: "GLU", 99: "TRP",
}

# 接触分析距离阈值（Å）
CUTOFFS = [3.5, 4.0, 5.0]


# ---------------------------------------------------------------------------
# JSON / cif 读取
# ---------------------------------------------------------------------------
def read_job(job_json_path):
    """从 *_job_request.json 读取 (seed, rna_sequence, protein_sequence)。

    注意：seed 必须从 job_request 读取，目录名不可靠。
    """
    with open(job_json_path, "r", encoding="utf-8") as f:
        d = json.load(f)[0]
    seed = str(d["modelSeeds"][0])
    rna = d["sequences"][1]["rnaSequence"]["sequence"]
    protein = d["sequences"][0]["proteinChain"]["sequence"]
    return seed, rna, protein


def parse_atom_site(cif_path):
    """解析 cif 的 _atom_site 循环。

    返回 (columns, rows)：
    - columns: 形如 ["atom_site.group_PDB", "atom_site.id", ...] 的列名列表
    - rows:    [{col_name: value}, ...]，value 已去除首尾引号
    """
    cols = []
    rows = []
    started = False
    with open(cif_path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.rstrip("\n")
            if s.startswith("_atom_site."):
                cols.append(s[1:])          # 去掉前导下划线
                started = True
                continue
            if started:
                if s.startswith(("ATOM", "HETATM")):
                    parts = s.split()
                    rec = {}
                    for c, v in zip(cols, parts):
                        rec[c] = v.strip('"')
                    rows.append(rec)
                else:
                    break                   # 数据行结束
    return cols, rows


# ---------------------------------------------------------------------------
# 原子筛选与几何
# ---------------------------------------------------------------------------
def atoms_of(rows, chain, resid=None, names=None, resn=None):
    """按 chain / resid / 原子名 / 残基名 过滤原子。"""
    out = []
    for a in rows:
        if a.get("atom_site.label_asym_id") != chain:
            continue
        if resid is not None and int(a["atom_site.label_seq_id"]) != resid:
            continue
        if names is not None and a.get("atom_site.label_atom_id") not in names:
            continue
        if resn is not None and a.get("atom_site.label_comp_id") not in resn:
            continue
        out.append(a)
    return out


def residues_by_chain(rows, chain):
    """返回 {resi: [atom_dict, ...]}，按链分组。"""
    res = {}
    for a in rows:
        if a.get("atom_site.label_asym_id") != chain:
            continue
        resi = int(a["atom_site.label_seq_id"])
        res.setdefault(resi, []).append(a)
    return res


def coord(a):
    return (float(a["atom_site.Cartn_x"]),
            float(a["atom_site.Cartn_y"]),
            float(a["atom_site.Cartn_z"]))


def min_dist(atoms_a, atoms_b):
    """两个原子列表间的最小重原子距离；任一侧为空返回 None。"""
    if not atoms_a or not atoms_b:
        return None
    best = None
    for a in atoms_a:
        xa, ya, za = coord(a)
        for b in atoms_b:
            xb, yb, zb = coord(b)
            dx, dy, dz = xa - xb, ya - yb, za - zb
            d = dx * dx + dy * dy + dz * dz
            if best is None or d < best:
                best = d
    return best ** 0.5


def atom_plddt(a):
    """返回单个原子的 pLDDT（B-factor 列）。"""
    try:
        return float(a["atom_site.B_iso_or_equiv"])
    except (KeyError, ValueError):
        return None
