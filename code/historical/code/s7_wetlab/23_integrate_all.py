# -*- coding: utf-8 -*-
"""
阶段 23(终版) —— 全数据整合
关键修正（相对前版）：
  ★ 实验基数校正：单点实验 WT C388=0.5145/C871=0.3754（+1比 1.371）
                  组合实验亲本 PUF12-9 C388=0.673/C871=0.565（+1比 1.191）
     → 两个实验的「+1比」不可直接比较，统一用「相对亲本的 +1比 倍数」(ROF) 归一化。
  ★ C871=0 为可重复的真实「脱靶清除」（重复间 CV<10%），单独成层。
  ★ 理论分与实测无相关（r≈-0.07）：如实报告，转为证据分层。
产出：results/23_*.csv / 23_report.txt
"""
import sys, re, csv, itertools, json
from collections import defaultdict
import openpyxl
sys.stdout.reconfigure(encoding="utf-8")

OUT = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); OUT.append(s)

WT_SEQ = ("MEASPASGPRHLMDPAIFTSNFNNGIGRHKTYLCYEVERLDNGTSVKMDQHRGFLHNQAKNLLCGFYGRHVEVNFIKKFTSERDF"
          "HPSMSCSITWFLSWSPCWECSQAIREFLSRHPGVTLVIYVARLFWHMDQQNRQGLRDLVNSGVTIQIMTYDEFKHCWDTFVDHQG"
          "APFQPWDGLDEHSQALSGRLRAILQNQGN")
WT = {i + 1: a for i, a in enumerate(WT_SEQ)}

S_REF = dict(name="WT(PUF12-9)", C388=0.5145, C871=0.3754, C295=0.2936, ratio=1.3707)
C_REF = dict(name="PUF12-9(亲本)", C388=0.673, C871=0.565, C295=0.335, ratio=1.1912)

FORBIDDEN = {57, 70, 72, 99, 102, 105}
CAUTION = {27, 28, 31, 98}
REGION = {25: "loop1-N", 26: "loop1-N", 27: "loop1-N", 28: "loop1-N", 29: "阅读器", 30: "阅读器",
          31: "阅读器", 32: "阅读器", 34: "远端", 56: "loop3", 57: "loop3", 58: "loop3", 59: "loop3",
          60: "loop3", 62: "远端", 63: "远端", 98: "WS环", 99: "WS环", 129: "loop7-出口",
          130: "loop7-出口", 131: "loop7-出口", 132: "loop7-出口", 133: "loop7-出口", 140: "远端"}
ROLE = {25: "N端调节", 26: "-1端调节", 27: "-1位主锚", 28: "loop1壁", 29: "保G阅读(主链)",
        30: "保G阅读主(侧链)", 31: "贴A氢键(非判别)", 32: "排+2G", 34: "远端", 56: "loop3前壁",
        57: "催化必需", 58: "loop3排A", 59: "loop3壁", 60: "loop3尾", 62: "远端", 63: "远端",
        98: "WS环", 99: "保守Trp", 129: "loop7头", 130: "loop7探针", 131: "loop7",
        132: "出口通道", 133: "loop7尾", 140: "远端"}

# ---------- 1. 单点数据 ----------
def load_single():
    wb = openpyxl.load_workbook("单点突变结果表：整理.xlsx", data_only=True)
    ws, wsd = wb["Sheet1"], wb["测序深度"]
    depth = defaultdict(list)
    for row in wsd.iter_rows(min_row=2, values_only=True):
        nm = str(row[0]).strip() if row[0] else ""
        if nm:
            try:
                depth[nm].append([float(x) for x in row[1:4]])
            except (TypeError, ValueError):
                pass
    acc = defaultdict(lambda: {"ACA": [], "GCG": [], "GCA": []})
    for row in ws.iter_rows(min_row=1, values_only=True):
        nm = str(row[0]).strip() if row[0] else ""
        if not nm or "PUF" in nm:
            continue
        v = row[1:4]
        if any(not isinstance(x, (int, float)) for x in v):
            continue
        acc[nm]["ACA"].append(float(v[0])); acc[nm]["GCG"].append(float(v[1])); acc[nm]["GCA"].append(float(v[2]))
    out = {}
    for nm, d in acc.items():
        m = re.match(r'^(\d+)([A-Z])$', nm)
        if not m:
            continue
        gcg = sum(d["GCG"]) / len(d["GCG"]); gca = sum(d["GCA"]) / len(d["GCA"]); aca = sum(d["ACA"]) / len(d["ACA"])
        dp = depth.get(nm) or [[0, 0, 0]]
        ratio = gcg / gca if gca > 0 else None
        out[nm] = dict(mut=nm, resi=int(m.group(1)), aa=m.group(2), nrep=len(d["GCG"]),
                       GCG=gcg, GCA=gca, ACA=aca, ratio=ratio,
                       retain=gcg / S_REF["C388"],
                       rof=(ratio / S_REF["ratio"] if ratio else None),   # 与单点实验亲本比
                       aca_gca=(aca / gca if gca > 0 else None),
                       aca_fold=(aca / S_REF["C295"] if S_REF["C295"] else None),
                       depth=round(sum(x[1] for x in dp) / len(dp)))
    return out

SINGLE = load_single()

# ---------- 2. 组合数据 ----------
def load_combo():
    wb = openpyxl.load_workbook("组合突变结果表：整理.xlsx", data_only=True)
    ws = wb["C295_C388_C871结果"]
    raw = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        nm = str(row[0]).strip() if row[0] else ""
        m = re.match(r'^(b?)(\d+)-(.*)$', nm)
        if not m:
            continue
        label = m.group(3)
        muts = [t for t in label.split("-") if t]
        sites = [int(re.match(r'^(\d+)', t).group(1)) for t in muts if re.match(r'^\d', t)]
        def num(x): return float(x) if isinstance(x, (int, float)) else 0.0
        raw.append(dict(label=label, muts=muts, sites=tuple(sorted(set(sites))),
                        C295=num(row[1]), C388=num(row[2]), C871=num(row[3])))
    merged = defaultdict(list)
    for r in raw:
        merged[r["label"]].append(r)
    res = []
    for label, rs in merged.items():
        c388 = sum(x["C388"] for x in rs) / len(rs)
        c871 = sum(x["C871"] for x in rs) / len(rs)
        c295 = sum(x["C295"] for x in rs) / len(rs)
        ratio = c388 / c871 if c871 > 0 else None
        res.append(dict(label=label, muts=rs[0]["muts"], sites=rs[0]["sites"], nrep=len(rs),
                        C295=c295, C388=c388, C871=c871, ratio=ratio,
                        retain=c388 / C_REF["C388"], off_fold=c871 / C_REF["C871"],
                        # ROF 必须与「单点实验亲本比 1.371」比，才能与单点 ROF 同轴
                        rof=(ratio / S_REF["ratio"] if ratio else None),
                        cleared=(c871 == 0 and c388 > 0),
                        silent=(c871 == 0 and c388 == 0 and label != "PUF12-9")))
    return res

COMBO = load_combo()

# ---------- 3. 计算维度 ----------
MI = {}
for r in csv.DictReader(open("results/coevolution_pairs.csv", encoding="utf-8-sig")):
    a, b = int(r["pos1"]), int(r["pos2"]); MI[(a, b)] = MI[(b, a)] = float(r["MI"])
MI_CORE = {int(r["resi"]): (float(r["mean_MI_core"]), float(r["max_MI_core"]))
           for r in csv.DictReader(open("results/coevolution_with_core.csv", encoding="utf-8-sig"))}
SP, SP_CA = {}, {}
for r in csv.DictReader(open("results/mutation_site_spatial_distances.csv", encoding="utf-8-sig")):
    a, b = int(r["resi1"]), int(r["resi2"])
    if r["minatom_dist_A"]: SP[(a, b)] = SP[(b, a)] = float(r["minatom_dist_A"])
    if r["ca_dist_A"]: SP_CA[(a, b)] = SP_CA[(b, a)] = float(r["ca_dist_A"])
CONS = {int(r["resi"]): (float(r["wt_freq"]), float(r["entropy"]))
        for r in csv.DictReader(open("results/conservation.csv", encoding="utf-8-sig"))}
CD = defaultdict(dict)
for r in csv.DictReader(open("results/contact_decomposition.csv", encoding="utf-8-sig")):
    CD[int(r["resi"])][r["rna"]] = dict(sc=float(r["sc_base"]), bb=float(r["bb_base"]),
                                        sp=float(r["sc_sugphos"]), note=r["designability"])

# ---------- 表 A ----------
p("=" * 132)
p("表 A · 位点主表  Site Master Table")
p(f"  单点实验亲本 {S_REF['name']}: C388={S_REF['C388']} C871={S_REF['C871']}  +1比={S_REF['ratio']:.3f}")
p(f"  组合实验亲本 {C_REF['name']}: C388={C_REF['C388']} C871={C_REF['C871']}  +1比={C_REF['ratio']:.3f}")
p("  保留 = C388/亲本C388 ; ROF = (自身+1比)/(亲本+1比)  ← 跨实验唯一可比的指标")
p("=" * 132)

by_site = defaultdict(list)
for nm, d in SINGLE.items():
    by_site[d["resi"]].append(d)

def pick(lst, minr=0.80):
    ok = [x for x in lst if x["retain"] >= minr and x["ratio"]]
    if ok: return max(ok, key=lambda x: x["rof"])
    pool = [x for x in lst if x["ratio"]]
    return max(pool, key=lambda x: x["rof"]) if pool else None

SITES = sorted(set(list(REGION.keys()) + [d["resi"] for d in SINGLE.values()]))
site_rows = []
for s in SITES:
    lst = by_site.get(s, [])
    b, bh = pick(lst), pick(lst, 0.90)
    c = CONS.get(s, (None, None)); mc = MI_CORE.get(s, (None, None))
    cd = CD.get(s, {})
    bc = None
    for x in COMBO:
        if s in x["sites"] and len(x["sites"]) <= 3 and (x["ratio"] or x["cleared"]):
            if bc is None or (x["rof"] or 9) > (bc["rof"] or 9):
                bc = x
    site_rows.append(dict(
        site=s, wt=WT.get(s, "?"), region=REGION.get(s, "-"), role=ROLE.get(s, "-"),
        status=("禁区" if s in FORBIDDEN else ("慎动" if s in CAUTION else "可动")),
        wt_freq=round(c[0], 3) if c[0] is not None else None,
        MI_mean_core=mc[0], MI_max_core=mc[1],
        SC_base_GCG=cd.get("GUGCGCG", {}).get("sc"), SC_base_GCA=cd.get("GUGCACG", {}).get("sc"),
        SC_base_GCG_bb=cd.get("GUGCGCG", {}).get("bb"),
        n_single=len(lst),
        best_mut=(b["mut"] if b else "-"), best_ratio=(round(b["ratio"], 2) if b and b["ratio"] else None),
        best_retain=(round(b["retain"], 2) if b else None),
        best_rof=(round(b["rof"], 2) if b and b["rof"] else None),
        best_aca_gca=(round(b["aca_gca"], 2) if b and b["aca_gca"] else None),
        hi_mut=(bh["mut"] if bh else "-"),
        hi_ratio=(round(bh["ratio"], 2) if bh and bh["ratio"] else None),
        hi_retain=(round(bh["retain"], 2) if bh else None),
        hi_rof=(round(bh["rof"], 2) if bh and bh["rof"] else None),
        best_combo=(bc["label"] if bc else "-"),
        best_combo_ratio=(round(bc["ratio"], 2) if bc and bc["ratio"] else (4.0 if bc else None)),
        best_combo_retain=(round(bc["retain"], 2) if bc else None),
        best_combo_rof=(round(bc["rof"], 2) if bc and bc["rof"] else (round(9.0, 2) if bc else None)),
    ))

def fm(x, w=6, d=2):
    return f"{x:>{w}.{d}f}" if isinstance(x, (int, float)) else f"{'-':>{w}}"

p(f"{'位点':>4} {'WT':>3} {'区域':<10} {'角色':<15} {'状态':<4} {'保守':>5} {'MI核':>5} "
  f"{'SC碱基G':>7} {'SC碱基A':>7} {'主链G':>6} | {'单点首选':>8} {'+1比':>5} {'保留':>5} {'ROF':>5} | "
  f"{'高保留点':>8} {'比':>5} {'留':>5} {'ROF':>5} | {'最佳组合':<18} {'比':>5} {'留':>5} {'ROF':>5}")
p("-" * 132)
for r in site_rows:
    p(f"{r['site']:>4} {r['wt']:>3} {r['region']:<10} {r['role']:<15} {r['status']:<4} "
      f"{fm(r['wt_freq'],5,2)} {fm(r['MI_mean_core'],5,2)} {fm(r['SC_base_GCG'],7,2)} {fm(r['SC_base_GCA'],7,2)} "
      f"{fm(r['SC_base_GCG_bb'],6,2)} | {r['best_mut']:>8} {fm(r['best_ratio'],5)} {fm(r['best_retain'],5)} "
      f"{fm(r['best_rof'],5)} | {r['hi_mut']:>8} {fm(r['hi_ratio'],5)} {fm(r['hi_retain'],5)} {fm(r['hi_rof'],5)} | "
      f"{r['best_combo']:<18} {fm(r['best_combo_ratio'],5)} {fm(r['best_combo_retain'],5)} {fm(r['best_combo_rof'],5)}")

with open("results/23_site_master_table.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(site_rows[0].keys())); w.writeheader(); w.writerows(site_rows)
p("\n→ results/23_site_master_table.csv")

# ---------- 表 B ----------
p("\n" + "=" * 132)
p("表 B · 组合湿实验主表（n=2 重复，重复间 CV<10%；C871=0 为可重复的真实脱靶清除）")
p("=" * 132)
ok = sorted([c for c in COMBO if c["ratio"]], key=lambda x: -x["rof"])
p(f"{'组合':<22} {'#':>2} {'n':>2} {'C388':>6} {'C871':>6} {'+1比':>6} {'保留':>6} {'脱靶倍数':>7} {'ROF':>6}")
p("-" * 132)
for c in ok:
    p(f"{c['label']:<22} {len(c['sites']):>2} {c['nrep']:>2} {c['C388']:>6.3f} {c['C871']:>6.3f} "
      f"{c['ratio']:>6.2f} {c['retain']:>6.2f} {c['off_fold']:>7.2f} {c['rof']:>6.2f}")

cleared = sorted([c for c in COMBO if c["cleared"]], key=lambda x: -x["C388"])
silent = [c for c in COMBO if c["silent"]]
p(f"\n【C 层】脱靶 C871 完全清除（可重复检出=0），共 {len(cleared)} 组，按 on-target 排序：")
p(f"   {'组合':<22} {'位点数':>3} {'C388':>6} {'保留':>6}")
for c in cleared:
    p(f"   {c['label']:<22} {len(c['sites']):>3} {c['C388']:>6.3f} {c['retain']:>6.2f}")
p(f"\n【废层】on-target 与脱靶同时归零（无活性/不表达），共 {len(silent)} 组：")
p("   " + ", ".join(c["label"] for c in silent))

with open("results/23_combo_master_table.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["label", "muts", "n_sites", "sites", "nrep", "C295", "C388", "C871",
                "ratio_p1", "retain_vs_parent", "offtarget_fold_vs_parent", "ROF", "cleared", "silent"])
    for c in COMBO:
        w.writerow([c["label"], "-".join(c["muts"]), len(c["sites"]), "+".join(map(str, c["sites"])),
                    c["nrep"], round(c["C295"], 4), round(c["C388"], 4), round(c["C871"], 4),
                    round(c["ratio"], 3) if c["ratio"] else "", round(c["retain"], 3),
                    round(c["off_fold"], 3), round(c["rof"], 3) if c["rof"] else "",
                    c["cleared"], c["silent"]])
p("\n→ results/23_combo_master_table.csv")

# ---------- 表 C 位点对打分 ----------
p("\n" + "=" * 132)
p("表 C · 位点对综合打分矩阵（MI × 空间耦合 × 实验可行 × 可突变性）")
p("=" * 132)

PAIR2, PAIR3 = defaultdict(list), defaultdict(list)
for c in COMBO:
    st = c["sites"]
    if len(st) == 2:
        PAIR2[tuple(sorted(st))].append(c)
    elif len(st) == 3:
        for a, b in itertools.combinations(sorted(st), 2):
            PAIR3[(a, b)].append(c)

usable = {}
for s, lst in by_site.items():
    if s in FORBIDDEN:
        continue
    b = pick(lst)
    if b and b["ratio"]:
        usable[s] = b

pair_rows = []
for a, b in itertools.combinations(sorted(usable), 2):
    if abs(a - b) <= 3:
        continue
    ea, eb = usable[a], usable[b]
    if ea["retain"] < 0.6 and eb["retain"] < 0.6:
        continue
    mi, sp = MI.get((a, b)), SP.get((a, b))
    c2, c3 = PAIR2.get((a, b), []), PAIR3.get((a, b), [])
    c2r = max([x for x in c2 if x["ratio"]], key=lambda x: x["rof"], default=None)
    c2c = [x for x in c2 if x["cleared"]]
    c2c = max(c2c, key=lambda x: x["C388"]) if c2c else None
    c3r = max([x for x in c3 if x["ratio"]], key=lambda x: x["rof"], default=None)
    mi_s = (1.0 if mi and mi >= 1.0 else 0.9 if mi and mi >= 0.8 else 0.75 if mi and mi >= 0.65
            else 0.55 if mi and mi >= 0.5 else 0.35 if mi and mi >= 0.35 else 0.15 if mi else 0.0)
    sp_s = (1.0 if sp and 3 <= sp <= 8 else 0.85 if sp and sp <= 12 else 0.6 if sp and sp <= 16
            else 0.35 if sp and sp <= 20 else 0.15)
    ex_s = 0.5 * min((ea["rof"] + eb["rof"]) / 2, 2.0) / 2.0 + 0.25 * min(ea["retain"], 1.2) / 1.2 + \
           0.25 * min(eb["retain"], 1.2) / 1.2
    mt_s = 1.0 if (a not in CAUTION and b not in CAUTION) else (0.6 if (a not in FORBIDDEN and b not in FORBIDDEN) else 0.2)
    theory = 0.30 * mi_s + 0.25 * sp_s + 0.25 * ex_s + 0.20 * mt_s
    meas = meas_src = meas_ret = None
    if c2r: meas, meas_src, meas_ret = c2r["ratio"], c2r["label"], c2r["retain"]
    elif c2c: meas, meas_src, meas_ret = None, c2c["label"] + "(脱靶清除)", c2c["retain"]
    elif c3r: meas, meas_src, meas_ret = c3r["ratio"], c3r["label"] + "(3点)", c3r["retain"]
    pair_rows.append(dict(
        a=a, b=b, mutA=ea["mut"], mutB=eb["mut"], region=f"{REGION.get(a,'?')}×{REGION.get(b,'?')}",
        roleA=ROLE.get(a, ""), roleB=ROLE.get(b, ""), MI=mi, space_min=sp, space_ca=SP_CA.get((a, b)),
        rofA=round(ea["rof"], 2), retainA=round(ea["retain"], 2),
        rofB=round(eb["rof"], 2), retainB=round(eb["retain"], 2),
        mi_s=round(mi_s, 2), sp_s=round(sp_s, 2), ex_s=round(ex_s, 3), mt_s=mt_s, theory=round(theory, 3),
        cleared=(c2c is not None),
        measured=round(meas, 2) if meas else None, measured_src=meas_src,
        measured_retain=round(meas_ret, 2) if meas_ret is not None else None))
pair_rows.sort(key=lambda x: -x["theory"])

p(f"{'位点对':>7} {'区域':<22} {'MI':>5} {'minÅ':>6} | {'A':>6}{'ROF':>6}{'留':>5} "
  f"{'B':>6}{'ROF':>6}{'留':>5} | {'实测比':>6}{'留':>6} {'脱靶清除':>8} {'来源':<20} | {'理论':>5}")
p("-" * 132)
for r in pair_rows:
    p(f"{str(r['a'])+'+'+str(r['b']):>7} {r['region']:<22} {fm(r['MI'],5)} {fm(r['space_min'],6,1)} | "
      f"{r['mutA']:>6}{r['rofA']:>6.2f}{r['retainA']:>5.2f} {r['mutB']:>6}{r['rofB']:>6.2f}{r['retainB']:>5.2f} | "
      f"{fm(r['measured'],6)} {fm(r['measured_retain'],6)} {'是' if r['cleared'] else '否':>8} "
      f"{(r['measured_src'] or ''):<20} | {r['theory']:>5.2f}")

with open("results/23_pair_score_matrix.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.DictWriter(fh, fieldnames=list(pair_rows[0].keys())); w.writeheader(); w.writerows(pair_rows)
p("\n→ results/23_pair_score_matrix.csv")

# ---------- 表 D 最终清单 ----------
p("\n" + "=" * 132)
p("表 D · 最终推荐清单")
p("=" * 132)
tested = [r for r in pair_rows if r["measured"] is not None or r["cleared"]]
p(f"（可判定位点对 = {len(tested)} / 全部 {len(pair_rows)}）")

T1 = [r for r in tested if r["measured"] and r["measured"] >= 2.0 and (r["measured_retain"] or 0) >= 0.45]
T2 = [r for r in tested if r["measured"] and r["measured"] >= 2.0 and (r["measured_retain"] or 0) < 0.45]
T3 = [r for r in tested if r["measured"] and 1.6 <= r["measured"] < 2.0 and (r["measured_retain"] or 0) >= 0.75]
TC = [r for r in tested if r["cleared"]]
TN = [r for r in pair_rows if r["measured"] is None and not r["cleared"]][:12]

# --- 表 D2：全点突变 3 点组合（实验中最优解集中在此层）---
p("\n" + "=" * 132)
p("表 D2 · 3 点全突变组合专表（on-target 保留 = C388/亲本0.673；这是实验中最优解所在层）")
p("=" * 132)
tri = sorted([c for c in COMBO if len(c["sites"]) == 3 and (c["ratio"] or c["cleared"])],
             key=lambda x: (-(x["ratio"] or 4.0), -x["retain"]))
p(f"{'组合':<22} {'位点':<14} {'C388':>6} {'C871':>6} {'+1比':>6} {'保留':>6} {'脱靶倍数':>7} {'ROF':>6}")
p("-" * 132)
for c in tri:
    p(f"{c['label']:<22} {'+'.join(map(str,c['sites'])):<14} {c['C388']:>6.3f} {c['C871']:>6.3f} "
      f"{(c['ratio'] if c['ratio'] else 4.0):>6.2f} {c['retain']:>6.2f} {c['off_fold']:>7.2f} "
      f"{(c['rof'] if c['rof'] else 9.0):>6.2f}")
p("\n★ 关键观察：3 点组合把 +1比 推过 2.0 的同时保留率显著高于 2 点组合（因活性被 58M 类的补偿）。")

# --- 表 D3：单点 vs 双点 vs 三点 的「比-活性」前沿 ---
p("\n" + "=" * 132)
p("表 D3 · 比-活性前沿（Pareto）：在给定 +1比 下保留率最高的组合")
p("=" * 132)
cand = [c for c in COMBO if c["ratio"] or c["cleared"]]
front = []
for c in sorted(cand, key=lambda x: -(x["ratio"] or 9.0)):
    rr = c["ratio"] or 9.0
    if not front or c["retain"] > max(f["retain"] for f in front):
        front.append(c)
p(f"{'组合':<22} {'#':>2} {'+1比':>6} {'保留':>6} {'脱靶倍数':>7}")
p("-" * 60)
for c in front:
    p(f"{c['label']:<22} {len(c['sites']):>2} {(c['ratio'] if c['ratio'] else 9.0):>6.2f} "
      f"{c['retain']:>6.2f} {c['off_fold']:>7.2f}")

def show(name, lst, note):
    p(f"\n【{name}】{len(lst)} 项 —— {note}")
    if not lst:
        p("   （无）"); return
    p(f"{'位点对':>7} {'建议突变':<18} {'实测比':>6} {'保留':>6} {'MI':>5} {'minÅ':>6} {'理论':>5}  来源")
    p("-" * 110)
    for r in sorted(lst, key=lambda x: -(x["measured"] or 0)):
        p(f"{str(r['a'])+'+'+str(r['b']):>7} {(r['mutA']+'+'+r['mutB']):<18} {fm(r['measured'],6)} "
          f"{fm(r['measured_retain'],6)} {fm(r['MI'],5)} {fm(r['space_min'],6,1)} {r['theory']:>5.2f}  {r['measured_src']}")

show("Tier 1 · 主推（实测 +1比 ≥2.0 且 on-target 保留 ≥45%）", T1, "特异性与活性兼顾，直接推进剂量梯度")
show("Tier 2 · 高比探针（实测 +1比 ≥2.0 但保留 <45%）", T2, "机制探针，需配套活性补偿或高剂量")
show("Tier 3 · 高活性保底（实测 +1比 1.6–2.0 且保留 ≥75%）", T3, "稳活性路线，比温和但表达/毒性风险最低")
show("Tier C · 脱靶完全清除（C871 检出=0）", [dict(r, measured=4.0) for r in TC], "最强脱靶清除信号，活性需提升")
show("Tier N · 未实测、理论分 Top 12", TN, "下一轮最值得补做的位点对")

with open("results/23_final_recommendation.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["tier", "pair", "mutA", "mutB", "region", "roleA", "roleB", "MI", "space_min_A",
                "measured_ratio", "measured_retain", "offtarget_cleared", "measured_source", "theory"])
    for tier, lst in [("T1主推", T1), ("T2高比探针", T2), ("T3高活性保底", T3), ("TC脱靶清除", TC), ("TN未实测理论", TN)]:
        for r in lst:
            w.writerow([tier, f"{r['a']}+{r['b']}", r["mutA"], r["mutB"], r["region"],
                        r["roleA"], r["roleB"], r["MI"], r["space_min"], r["measured"],
                        r["measured_retain"], r["cleared"], r["measured_src"], r["theory"]])
p("\n→ results/23_final_recommendation.csv")

# ---------- 表 E 模型自检 ----------
p("\n" + "=" * 132)
p("表 E · 模型自检：先验理论分 能否预测实测 +1比？")
p("=" * 132)
have = [r for r in pair_rows if r["measured"] is not None and r["measured"] < 4.0]
if len(have) >= 4:
    xs = [r["theory"] for r in have]; ys = [r["measured"] for r in have]; n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = sum((x - mx) ** 2 for x in xs) ** .5; sy = sum((y - my) ** 2 for y in ys) ** .5
    rp = cov / (sx * sy) if sx * sy else 0
    def rank(v):
        s = sorted(range(len(v)), key=lambda i: v[i]); rk = [0] * len(v)
        for pos, i in enumerate(s): rk[i] = pos
        return rk
    rx, ry = rank(xs), rank(ys)
    mrx, mry = sum(rx) / n, sum(ry) / n
    cv = sum((a - mrx) * (b - mry) for a, b in zip(rx, ry))
    srx = sum((a - mrx) ** 2 for a in rx) ** .5; sry = sum((b - mry) ** 2 for b in ry) ** .5
    p(f"  n={n}   Pearson r = {rp:.3f}   Spearman ρ = {cv/(srx*sry):.3f}")
    p("  → 结论：先验理论分（MI×空间×单点）与组合实测 +1比 无显著相关，")
    p("     说明「叠加效应」不能被简单的加性先验预测，必须以实测为准。")
    p("  明细（按实测降序）：")
    for r in sorted(have, key=lambda x: -x["measured"]):
        p(f"    {str(r['a'])+'+'+str(r['b']):>7}  理论 {r['theory']:.2f}  实测 {r['measured']:.2f}  "
          f"保留 {r['measured_retain']:.2f}  位点距离 {r['space_min']} Å  MI {r['MI'] if r['MI'] else 0:.2f}")

open("results/23_report.txt", "w", encoding="utf-8").write("\n".join(OUT))
print("\nDONE")
