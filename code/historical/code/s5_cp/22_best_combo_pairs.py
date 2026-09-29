# -*- coding: utf-8 -*-
"""
阶段 22 —— 最佳组合位点对综合筛选
「进化共变(MI) × 空间耦合(3D距离) × 实验可行性(单点/组合湿实验)」
产出：results/best_combo_pairs.csv（最终清单，含证据分层）
"""
import csv, sys, re, itertools
sys.stdout.reconfigure(encoding="utf-8")

FORBIDDEN = {57, 70, 72, 99, 102, 105}
ROLE = {25:"loop1-N调节",26:"loop1-N调节",27:"-1位压ACA锚",28:"loop1壁",29:"保G阅读",
        30:"保G阅读主",31:"贴A(T31)",32:"排+2G",56:"loop3前",58:"loop3排A",59:"loop3壁",
        60:"loop3尾",98:"WS环",129:"loop7头",130:"loop7探针",131:"loop7",132:"出口M132",
        133:"loop7尾"}
REGION = {25:"loop1-N",26:"loop1-N",27:"loop1-N",28:"loop1-N",29:"阅读",30:"阅读",31:"阅读",
          32:"阅读",56:"loop3",57:"loop3",58:"loop3",59:"loop3",60:"loop3",98:"WS环",99:"WS环",
          129:"loop7",130:"loop7",131:"loop7",132:"loop7",133:"loop7"}

# ---- 1. 共进化 MI ----
MI = {}
for r in csv.DictReader(open("results/coevolution_pairs.csv", encoding="utf-8-sig")):
    a, b = int(r["pos1"]), int(r["pos2"])
    MI[(a, b)] = MI[(b, a)] = float(r["MI"])

# ---- 2. 空间距离 ----
SP = {}
for r in csv.DictReader(open("results/mutation_site_spatial_distances.csv", encoding="utf-8-sig")):
    a, b = int(r["resi1"]), int(r["resi2"])
    if r["minatom_dist_A"]:
        SP[(a, b)] = SP[(b, a)] = float(r["minatom_dist_A"])

# ---- 3. 单点实验：每位点保留≥0.6 中 ratio 最高者 ----
EXP = {}
for r in csv.DictReader(open("results/experimental_ranking.csv", encoding="utf-8-sig")):
    m = re.match(r'(\d+)([A-Z])', r["mut"])
    if not m: continue
    resi = int(m.group(1))
    EXP.setdefault(resi, []).append(dict(aa=r["mut"][-1], ratio=float(r["ratio"]),
                                         retain=float(r["retain"]), active=r["active"] == "True"))
BEST = {}
for resi, es in EXP.items():
    ok = [e for e in es if e["retain"] >= 0.6]
    best = max(ok if ok else es, key=lambda e: e["ratio"])
    BEST[resi] = dict(mut=f"{resi}{best['aa']}", ratio=best["ratio"], retain=best["retain"],
                      usable=bool(ok))

# ---- 4. 组合湿实验：位点对 -> 实测组合 ratio（只取全点突变组合，排除P域名变体）----
import openpyxl
wb = openpyxl.load_workbook("组合突变结果/merged_data_var8_C295_C388_C871_C_to_T_重新核实_按var1格式.xlsx", data_only=True)
ws = wb[wb.sheetnames[0]]
COMBO_FULL = {}     # frozenset(sites) -> mean ratio
for row in ws.iter_rows(values_only=True):
    name = str(row[0]) if row[0] else ""
    if not name or "G2260" in name: continue
    if re.match(r'^P\d|^PUF|^P\d', name):   # P域名变体排除
        continue
    m = re.match(r'^b?(\d+)-(.*)$', name)
    combo = m.group(2) if m else name
    c388, c871 = row[3], row[4]
    if not isinstance(c388, (int, float)) or not isinstance(c871, (int, float)) or c871 <= 0:
        continue
    sites = set()
    for tok in combo.split("-"):
        mm = re.match(r'(\d+)([A-Z]+)$', tok)
        if mm and int(mm.group(1)) not in FORBIDDEN:
            sites.add(int(mm.group(1)))
    if len(sites) >= 2:
        ratio = c388 / c871
        COMBO_FULL.setdefault(frozenset(sites), []).append(ratio)

PAIR_TRIAL = {}   # pair -> best combo ratio containing pair (排除超过3位点、避免归因混淆)
PAIR_BEST3 = {}
for sites, ratios in COMBO_FULL.items():
    r = sum(ratios) / len(ratios)
    for a, b in itertools.combinations(sorted(sites), 2):
        if len(sites) == 2:
            PAIR_TRIAL.setdefault((a, b), []).append(r)
        elif len(sites) == 3:
            PAIR_BEST3.setdefault((a, b), []).append(r)

# ---- 5. 综合筛选 ----
cand = sorted(set(EXP) - FORBIDDEN)
rows = []
for a, b in itertools.combinations(cand, 2):
    if abs(a - b) <= 3:          # 排除序列相邻(非独立叠加)
        continue
    if BEST.get(a, {}).get("usable") is not True and BEST.get(b, {}).get("usable") is not True:
        # 两位点都无保留单点 -> 不可行
        continue
    ea, eb = BEST.get(a), BEST.get(b)
    if not ea or not eb: continue
    if ea["retain"] < 0.6 and eb["retain"] < 0.6: continue
    mi = MI.get((a, b)); sp = SP.get((a, b))
    pr2 = PAIR_TRIAL.get((a, b)); pr2 = max(pr2) if pr2 else None
    pr3 = PAIR_BEST3.get((a, b)); pr3 = max(pr3) if pr3 else None
    # 综合评分(理论)
    mi_s = 1.0 if (mi and mi >= 0.7) else (0.7 if (mi and mi >= 0.55) else (0.45 if (mi and mi >= 0.4) else (0.2 if mi else 0)))
    sp_s = 1.0 if (sp and sp <= 6) else (0.8 if (sp and sp <= 9) else (0.5 if (sp and sp <= 13) else (0.25 if (sp and sp <= 18) else 0.1)))
    ex_s = 0.5 * min((ea["ratio"] + eb["ratio"]) / 2, 2.0) / 2.0 + 0.25 * ea["retain"] + 0.25 * eb["retain"]
    theory = 0.4 * mi_s + 0.35 * sp_s + 0.25 * ex_s
    tested = pr2 is not None
    rows.append(dict(a=a, b=b, mutA=ea["mut"], mutB=eb["mut"], mi=mi, sp=sp,
                     theory=theory, tested2=tested, combo_ratio2=pr2, combo_ratio3=pr3,
                     region=f"{REGION.get(a,'?')}×{REGION.get(b,'?')}",
                     roleA=ROLE.get(a, ''), roleB=ROLE.get(b, '')))
rows.sort(key=lambda x: -x["theory"])

# 实验验证优先级：已实测 2 位点组合 ratio 排前
print("="*100)
print("A 类：已湿实验实测（2点组合 ratio≥1.9 或 3点含此对 ratio≥2.0）")
print("="*100)
print(f"{'位点对':<8}{'实测2点':>8}{'含于3点':>9}{'MI':>6}{'空间Å':>7}{'理论分':>7}  区域×区域 (建议突变)")
a_list = [r for r in rows if (r["combo_ratio2"] and r["combo_ratio2"] >= 1.9) or (r["combo_ratio3"] and r["combo_ratio3"] >= 2.0)]
for r in sorted(a_list, key=lambda x: -(x["combo_ratio2"] or 0)):
    print(f"{r['a']:>3}-{r['b']:<3}  {r['combo_ratio2'] or 0:>7.2f}  {r['combo_ratio3'] or 0:>8.2f}  "
          f"{r['mi'] or 0:.2f}  {r['sp'] or 0:.1f}  {r['theory']:>6.2f}   {r['region']}  {r['mutA']}+{r['mutB']}")

print()
print("="*100)
print("B 类：未实测，理论高分（进化共变×空间耦合×单点可行）Top 15")
print("="*100)
print(f"{'位点对':<8}{'MI':>6}{'空间Å':>7}{'理论分':>7}  区域×区域 (建议突变)")
b_list = [r for r in rows if not r["tested2"]]
for r in b_list[:15]:
    print(f"{r['a']:>3}-{r['b']:<3}  {r['mi'] or 0:.2f}  {r['sp'] or 0:.1f}  {r['theory']:>6.2f}   {r['region']}  {r['mutA']}+{r['mutB']}  ({r['roleA']}/{r['roleB']})")

# 存 CSV
with open("results/best_combo_pairs.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["rank_class", "pair", "mutA", "mutB", "region", "roleA", "roleB",
                "MI", "space_A", "theory_score", "tested_2combo_ratio", "in_3combo_ratio"])
    for r in a_list:
        w.writerow(["A已实测", f"{r['a']}+{r['b']}", r["mutA"], r["mutB"], r["region"], r["roleA"], r["roleB"],
                    round(r["mi"] or 0, 3), round(r["sp"] or 0, 1), round(r["theory"], 3),
                    round(r["combo_ratio2"] or 0, 2), round(r["combo_ratio3"] or 0, 2)])
    for r in b_list[:20]:
        w.writerow(["B理论", f"{r['a']}+{r['b']}", r["mutA"], r["mutB"], r["region"], r["roleA"], r["roleB"],
                    round(r["mi"] or 0, 3), round(r["sp"] or 0, 1), round(r["theory"], 3), "", ""])
print("\n写入 results/best_combo_pairs.csv")
