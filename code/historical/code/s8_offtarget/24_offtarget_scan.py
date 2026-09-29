# -*- coding: utf-8 -*-
"""
阶段 24 —— 组合突变体的「总体脱靶」筛查（不限于 388/871）

数据：Seq/Var/*.var.xls（APOE 扩增子 951 bp 深度测序变异表，117 样本 = a/b 重复）
参考：Seq/Bam/*.for.ref.fa（APOE CDS，291 个 C 位点）

思路：
  1) 提取每个样本全部 C→T 位点（APOBEC 脱氨特征）；
  2) 以 pos388 为 on-target，其余全部 C→T 位点视为 off-target；
  3) 计算总体脱靶指标：脱靶位点数、平均/中位/最大脱靶频率、脱靶负荷(Σfreq)、
     全基因尺度特异性 S = on / (on + Σoff)；
  4) 与亲本 PUF12-9 比较，识别「脱靶负荷降低」与「新增脱靶位点」；
  5) 按突变类型聚合 a/b 重复，输出组合筛查清单。

产出：results/offtarget_per_sample.csv
      results/offtarget_by_mutant.csv
      results/offtarget_hotspots.csv（高频脱靶位点及 motif）
"""
import glob, os, re, sys, statistics
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

REF_FA = "Seq/Bam/G22609034389-1-32F.for.ref.fa"
VAR_DIR = "Seq/Var"
ON_TARGET = 388          # APOE c.388（GCG，on-target）
KNOWN_871 = 871          # APOE c.871（GCA，已知主要脱靶）
FREQ_FLOOR = 0.05        # 变异检出下限（caller 报告下限 ~5%）
PASS_THR = 0.08          # PASS 阈值

# ---------- 参考序列 ----------
lines = open(REF_FA, encoding="utf-8").read().splitlines()
REF = "".join(l for l in lines if not l.startswith(">"))
L = len(REF)


def motif(pos):
    """返回 (pos-1 碱基, 编辑C, pos+1 碱基) 的局部序列 5'-NCN-3'"""
    i = pos - 1
    return (REF[i-1] if i-1 >= 0 else "-") + "C" + (REF[i+1] if i+1 < L else "-")


def parse(path):
    """解析单样本 var.xls，返回 {pos: (freq, dp, ref, alt, status)}"""
    out = {}
    with open(path, encoding="latin-1") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 11: continue
            try:
                pos = int(p[1]); freq = float(p[7]); dp = int(p[4])
            except ValueError:
                continue
            out[pos] = dict(freq=freq, dp=dp, ref=p[2], alt=p[3], status=p[10])
    return out


def mutant_of(name):
    """G22609034433-45-27T-30H-58M -> 27T-30H-58M；b 重复去前缀"""
    m = re.match(r'G\d+-(b?)(\d+)-(.*)$', name)
    if not m: return name
    return m.group(3)


# ---------- 遍历全部样本 ----------
per_sample = []
for f in sorted(glob.glob(os.path.join(VAR_DIR, "*.var.xls"))):
    if ".filt." in f: continue
    name = os.path.basename(f).replace(".var.xls", "")
    d = parse(f)
    ct = {pos: v for pos, v in d.items() if v["ref"] == "C" and v["alt"] == "T"}
    # 只用频率≥下限的位点
    calls = {pos: v for pos, v in ct.items() if v["freq"] >= FREQ_FLOOR}
    on = ct.get(ON_TARGET, {}).get("freq", 0.0)
    off = {pos: v["freq"] for pos, v in calls.items() if pos != ON_TARGET}
    off_pass = {pos: v for pos, v in calls.items() if pos != ON_TARGET and v["freq"] >= PASS_THR}
    dp_list = [v["dp"] for v in d.values()]
    med_dp = statistics.median(dp_list) if dp_list else 0
    off_sum = sum(off.values())
    off_mean = statistics.mean(off.values()) if off else 0.0
    off_med = statistics.median(off.values()) if off else 0.0
    off_max = max(off.values()) if off else 0.0
    per_sample.append(dict(
        sample=name, mutant=mutant_of(name), rep="b" if re.search(r'-b\d+-', name) else "a",
        med_dp=med_dp, on=on, f871=ct.get(KNOWN_871, {}).get("freq", 0.0),
        n_off=len(off), n_off_pass=len(off_pass),
        off_mean=off_mean, off_med=off_med, off_max=off_max, off_sum=off_sum,
        S_global=(on / (on + off_sum)) if (on + off_sum) > 0 else 0.0,
        ratio_388_871=(on / ct[KNOWN_871]["freq"]) if ct.get(KNOWN_871, {}).get("freq", 0) > 0 else None,
        off_positions=set(off.keys()),
    ))

print(f"解析样本数: {len(per_sample)}  参考长度: {L}  C位点总数: {REF.count('C')}")

# ---------- 按突变类型聚合 a/b ----------
by_mut = defaultdict(list)
for r in per_sample:
    by_mut[r["mutant"]].append(r)

agg = []
for mut, rs in by_mut.items():
    n = len(rs)
    def m(k):
        vals = [r[k] for r in rs if r[k] is not None]
        return statistics.mean(vals) if vals else 0.0
    agg.append(dict(
        mutant=mut, n=n, med_dp=m("med_dp"),
        on=m("on"), f871=m("f871"), n_off=m("n_off"), n_off_pass=m("n_off_pass"),
        off_mean=m("off_mean"), off_med=m("off_med"), off_max=m("off_max"), off_sum=m("off_sum"),
        S_global=m("S_global"),
        ratio_388_871=statistics.mean([r["ratio_388_871"] for r in rs if r["ratio_388_871"]] or [0]),
    ))
agg.sort(key=lambda x: -x["S_global"])

# 亲本
parent = next((a for a in agg if a["mutant"] == "PUF12-9"), None)

print()
print("=" * 118)
print("表1  全基因尺度脱靶筛查（按「全尺度特异性 S = on/(on+Σoff)」降序；S 越高 = 编辑越集中在靶点）")
print("=" * 118)
print(f"{'突变':<20}{'n':>2}{'DP':>6}{'388(on)':>9}{'871':>7}{'脱靶数':>7}{'脱靶均值':>9}"
      f"{'脱靶中位':>9}{'脱靶最大':>9}{'脱靶负荷':>9}{'S全尺度':>8}")
for a in agg:
    if a["on"] < 0.02 and a["mutant"] != "PUF12-9":
        continue
    print(f"{a['mutant']:<20}{a['n']:>2}{a['med_dp']:>6.0f}{a['on']:>9.3f}{a['f871']:>7.3f}"
          f"{a['n_off']:>7.1f}{a['off_mean']:>9.3f}{a['off_med']:>9.3f}{a['off_max']:>9.3f}"
          f"{a['off_sum']:>9.2f}{a['S_global']:>8.3f}")

# ---------- 与亲本比较：脱靶负荷变化 ----------
if parent:
    print()
    print("=" * 118)
    print(f"表2  相对亲本 PUF12-9（on={parent['on']:.3f}, 脱靶数={parent['n_off']:.0f}, 脱靶负荷={parent['off_sum']:.2f}）的变化")
    print("=" * 118)
    print(f"{'突变':<20}{'Δon':>8}{'Δ脱靶数':>9}{'Δ脱靶负荷':>11}{'负荷倍数':>9}{'ΔS全尺度':>10}  判读")
    cmp_rows = []
    for a in agg:
        if a["mutant"] == "PUF12-9": continue
        if a["on"] < 0.02: continue
        d_on = a["on"] - parent["on"]
        d_n = a["n_off"] - parent["n_off"]
        d_load = a["off_sum"] - parent["off_sum"]
        fold = a["off_sum"] / parent["off_sum"] if parent["off_sum"] > 0 else 0
        dS = a["S_global"] - parent["S_global"]
        verdict = ""
        if d_load < -parent["off_sum"] * 0.5 and d_on > -0.2:
            verdict = "★ 脱靶大幅降低且保活性"
        elif d_load < 0:
            verdict = "脱靶降低"
        elif d_load > parent["off_sum"] * 0.3:
            verdict = "⚠ 脱靶升高"
        cmp_rows.append((a["mutant"], d_on, d_n, d_load, fold, dS, verdict))
    for row in sorted(cmp_rows, key=lambda x: x[3]):
        print(f"{row[0]:<20}{row[1]:>+8.3f}{row[2]:>+9.1f}{row[3]:>+11.2f}{row[4]:>9.2f}{row[5]:>+10.3f}  {row[6]}")

# ---------- 脱靶热点（跨样本高频） ----------
pos_freq = defaultdict(list)
for r in per_sample:
    for p in r["off_positions"]:
        pass  # 需要频率，重新收集
hot = defaultdict(list)
for f in sorted(glob.glob(os.path.join(VAR_DIR, "*.var.xls"))):
    if ".filt." in f: continue
    d = parse(f)
    for pos, v in d.items():
        if v["ref"] == "C" and v["alt"] == "T" and pos != ON_TARGET and v["freq"] >= FREQ_FLOOR:
            hot[pos].append(v["freq"])
hot_rows = []
for pos, frs in hot.items():
    hot_rows.append((pos, len(frs), statistics.mean(frs), max(frs), motif(pos)))
hot_rows.sort(key=lambda x: -x[1])
print()
print("=" * 118)
print("表3  跨样本高频脱靶位点 TOP20（按出现样本数）")
print("=" * 118)
print(f"{'位点':>6}{'motif':>8}{'出现样本数':>10}{'平均freq':>10}{'最大freq':>10}   位置说明")
for pos, n, mean_f, max_f, mo in hot_rows[:20]:
    tag = "← 已知主要脱靶 c.871" if pos == KNOWN_871 else ""
    print(f"{pos:>6}{mo:>8}{n:>10}{mean_f:>10.3f}{max_f:>10.3f}   {tag}")

# ---------- 输出 ----------
with open("results/offtarget_per_sample.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = None
    import csv as _csv
    w = _csv.writer(f)
    w.writerow(["sample", "mutant", "rep", "med_dp", "on_388", "f_871", "n_off",
                "n_off_pass", "off_mean", "off_med", "off_max", "off_sum", "S_global", "ratio_388_871"])
    for r in per_sample:
        w.writerow([r["sample"], r["mutant"], r["rep"], round(r["med_dp"], 0), round(r["on"], 4),
                    round(r["f871"], 4), r["n_off"], r["n_off_pass"], round(r["off_mean"], 4),
                    round(r["off_med"], 4), round(r["off_max"], 4), round(r["off_sum"], 3),
                    round(r["S_global"], 4), round(r["ratio_388_871"], 3) if r["ratio_388_871"] else ""])

with open("results/offtarget_by_mutant.csv", "w", newline="", encoding="utf-8-sig") as f:
    import csv as _csv
    w = _csv.writer(f)
    w.writerow(["mutant", "n_rep", "med_dp", "on_388", "f_871", "n_off", "n_off_pass",
                "off_mean", "off_med", "off_max", "off_sum", "S_global", "ratio_388_871"])
    for a in agg:
        w.writerow([a["mutant"], a["n"], round(a["med_dp"], 0), round(a["on"], 4), round(a["f871"], 4),
                    round(a["n_off"], 2), round(a["n_off_pass"], 2), round(a["off_mean"], 4),
                    round(a["off_med"], 4), round(a["off_max"], 4), round(a["off_sum"], 3),
                    round(a["S_global"], 4), round(a["ratio_388_871"], 3)])

with open("results/offtarget_hotspots.csv", "w", newline="", encoding="utf-8-sig") as f:
    import csv as _csv
    w = _csv.writer(f)
    w.writerow(["pos", "motif", "n_samples", "mean_freq", "max_freq"])
    for pos, n, mean_f, max_f, mo in hot_rows:
        w.writerow([pos, mo, n, round(mean_f, 4), round(max_f, 4)])

print("\n写入 results/offtarget_per_sample.csv / offtarget_by_mutant.csv / offtarget_hotspots.csv")
