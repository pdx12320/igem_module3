# -*- coding: utf-8 -*-
"""
阶段 5 —— 单突变库 + 组合突变生成与合理性筛选（目标 ~1000 组）

思路（依据可行性选「理性单点 + 系统组合」，而非盲目 20 AA 饱和）：
  1) 单突变库：基于互作分析(距离/氢键/埋藏面积) + 学姐饱和数据，每个可设计位点
     给出 1–4 个有生化依据的替换（不是全部 20 种），每个带：
        est_ratio = 对 +1 特异性(GCG/GCA)的相乘贡献估计（>1 表示「保G排A」）
        est_ddG   = 对折叠稳定性的影响估计(kcal/mol，正=去稳定)
  2) 生成所有「2 位点」与「3 位点」组合（不同位点之间）。
  3) 合理性筛选：
        a. 排除累加 est_ddG > 2.0 的明显去稳定组合；
        b. 排除不含任何「排A」突变的组合（无法提升特异性）；
        c. 排除组合内同一功能位点冗余（已由「不同位点」天然保证）。
  4) 按 est_ratio(相乘) 降序排序，输出前 1000 组。

产出：results/combinations_top1000.csv
"""
import os
import csv
from itertools import combinations

OUT_DIR = "results"

# (resi, wt, sub, 类别, est_ratio, est_ddG)
# 类别：排A(+1) / 排A(-1) / 排A(+2) / 排A(出口) / 保G排A / 辅助
LIBRARY = [
    (25, "G", "E", "辅助",       1.00, 0.5),
    (26, "I", "D", "排A(-1)",    1.20, 0.8),
    (27, "G", "D", "排A(-1)",    1.50, 0.7),
    (27, "G", "T", "排A(-1)",    1.46, 0.6),
    (27, "G", "V", "排A(-1)",    1.30, 0.6),
    (27, "G", "I", "排A(-1)",    1.30, 0.7),
    (28, "R", "A", "排A(+1)",    1.10, 0.4),
    (28, "R", "S", "排A(+1)",    1.10, 0.3),
    (29, "H", "N", "保G调谐",    1.00, 0.5),
    (29, "H", "F", "保G调谐",    1.05, 0.6),
    (30, "K", "H", "保G排A",     1.71, 0.0),
    (30, "K", "N", "保G调谐",    1.00, 0.4),
    (31, "T", "A", "排A(+1)新",  1.40, 0.5),
    (31, "T", "V", "排A(+1)新",  1.40, 0.6),
    (31, "T", "I", "排A(+1)新",  1.35, 0.6),
    (31, "T", "L", "排A(+1)新",  1.30, 0.7),
    (32, "Y", "F", "排A(+2)",    1.10, 0.01),
    (59, "A", "P", "辅助",       1.10, 0.5),
    (59, "A", "S", "辅助",       1.05, 0.3),
    (60, "K", "H", "排A(+1)",    1.20, 0.4),
    (60, "K", "R", "排A(+1)",    1.20, 0.5),
    (98, "S", "A", "辅助",       1.00, 0.5),
    (132, "M", "D", "排A(出口)", 1.44, -0.83),
    (132, "M", "E", "排A(出口)", 1.19, -0.5),
]

DDG_CUTOFF = 2.0
TOP_N = 1000


def combo_key(singles):
    """按位点排序，生成可读的突变标签，如 K30H/T31A。"""
    ordered = sorted(singles, key=lambda s: s["resi"])
    return "+".join(f"{s['wt']}{s['resi']}{s['sub']}" for s in ordered)


def main():
    singles = [dict(zip(["resi", "wt", "sub", "tag", "ratio", "ddg"], s))
               for s in LIBRARY]
    by_resi = {}
    for s in singles:
        by_resi.setdefault(s["resi"], []).append(s)

    # 收集所有 2 位点 / 3 位点组合
    combos = []
    for k in (2, 3):
        for combo in combinations(singles, k):
            resis = [s["resi"] for s in combo]
            if len(set(resis)) != k:          # 同一位点不能重复
                continue
            combos.append(combo)

    # 合理性筛选
    passed = []
    for combo in combos:
        ratio = 1.0
        ddg = 0.0
        tags = set()
        for s in combo:
            ratio *= s["ratio"]
            ddg += s["ddg"]
            tags.add(s["tag"])
        if ddg > DDG_CUTOFF:
            continue                              # 明显去稳定
        if not any(t.startswith("排A") or t == "保G排A" for t in tags):
            continue                              # 不含排A → 无法提升特异性
        passed.append({
            "mutations": combo_key(combo),
            "n_sites": len(combo),
            "tags": "/".join(sorted(tags)),
            "est_ratio": ratio,
            "est_ddG": ddg,
        })

    passed.sort(key=lambda r: (-r["est_ratio"], r["est_ddG"]))

    top = passed[:TOP_N]
    fields = ["rank", "mutations", "n_sites", "tags", "est_ratio", "est_ddG"]
    with open(os.path.join(OUT_DIR, "combinations_top1000.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for i, r in enumerate(top, 1):
            w.writerow({"rank": i, **r,
                        "est_ratio": round(r["est_ratio"], 3),
                        "est_ddG": round(r["est_ddG"], 2)})

    print(f"单突变库：{len(singles)} 个（{len(by_resi)} 个位点）")
    print(f"生成组合：{len(combos)} 组（2位点+3位点，不同位点）")
    print(f"通过筛选：{len(passed)} 组")
    print(f"输出前 {len(top)} 组 -> results/combinations_top1000.csv")
    print("\n== 前 15 组预览 ==")
    for r in top[:15]:
        print(f"  {r['mutations']:<28} ratio={r['est_ratio']:<6} ddG={r['est_ddG']:<5} {r['tags']}")


if __name__ == "__main__":
    main()
