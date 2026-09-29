# -*- coding: utf-8 -*-
"""
阶段 25 —— 组合突变体「总体脱靶」最终筛查
修正阶段 24 的假阳性：低活性样本（on-target 极低）会因「检不出脱靶」而呈现 S=1.0，
必须用「活性下限 + 脱靶负荷」联合判据筛查。

指标：
  活性下限 on ≥ 0.30（≈亲本的 45%）
  脱靶负荷 off_sum（全部 off-target C→T 频率之和）
  归一化脱靶负荷 = off_sum / on（消除活性差异，越低越特异）
  新增脱靶位点 = 组合中检出而亲本未检出的位点（检验「多点突变引入全新脱靶」风险）

产出：results/offtarget_screen_final.csv
"""
import glob, os, re, sys, statistics, csv
from collections import defaultdict
sys.stdout.reconfigure(encoding="utf-8")

REF_FA = "Seq/Bam/G22609034389-1-32F.for.ref.fa"
VAR_DIR = "Seq/Var"
ON = 388; F871 = 871; FLOOR = 0.05
REF = "".join(l for l in open(REF_FA, encoding="utf-8").read().splitlines() if not l.startswith(">"))
L = len(REF)
def motif(p):
    i = p - 1
    return (REF[i-1] if i-1 >= 0 else "-") + "C" + (REF[i+1] if i+1 < L else "-")

def parse_sites(path):
    """返回 {pos: freq} (仅 C>T, freq>=FLOOR)"""
    out = {}
    with open(path, encoding="latin-1") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            p = line.rstrip("\n").split("\t")
            if len(p) < 11: continue
            if p[2] != "C" or p[3] != "T": continue
            try: pos = int(p[1]); freq = float(p[7])
            except ValueError: continue
            if freq >= FLOOR: out[pos] = freq
    return out

def mutant_of(name):
    m = re.match(r'G\d+-(b?)(\d+)-(.*)$', name)
    return m.group(3) if m else name

# ---- 收集 ----
samples = {}
for f in sorted(glob.glob(os.path.join(VAR_DIR, "*.var.xls"))):
    if ".filt." in f: continue
    name = os.path.basename(f).replace(".var.xls", "")
    samples[name] = dict(mutant=mutant_of(name), sites=parse_sites(f))

# 亲本位点集（a+b 合并，取并集）
par = [s for s in samples.values() if s["mutant"] == "PUF12-9"]
par_sites = set()
for s in par: par_sites |= set(s["sites"].keys())
par_sites.discard(ON)
par_on = statistics.mean([s["sites"].get(ON, 0) for s in par])
par_load = statistics.mean([sum(v for k, v in s["sites"].items() if k != ON) for s in par])

# ---- 按突变聚合 ----
by_mut = defaultdict(list)
for s in samples.values(): by_mut[s["mutant"]].append(s)

rows = []
for mut, ss in by_mut.items():
    n = len(ss)
    on = statistics.mean([s["sites"].get(ON, 0) for s in ss])
    offs = [ {k: v for k, v in s["sites"].items() if k != ON} for s in ss ]
    load = statistics.mean([sum(o.values()) for o in offs])
    n_off = statistics.mean([len(o) for o in offs])
    off_mean = statistics.mean([statistics.mean(o.values()) if o else 0 for o in offs])
    off_max = statistics.mean([max(o.values()) if o else 0 for o in offs])
    # 新增脱靶位点：所有重复中至少一次检出、且亲本从未检出
    combo_union = set()
    for o in offs: combo_union |= set(o.keys())
    new_sites = sorted(combo_union - par_sites)
    norm_load = load / on if on > 0 else float("inf")
    rows.append(dict(mutant=mut, n=n, on=on, load=load, n_off=n_off, off_mean=off_mean,
                     off_max=off_max, norm_load=norm_load,
                     S=on/(on+load) if (on+load) > 0 else 0,
                     fold_vs_parent=load/par_load if par_load > 0 else 0,
                     new_sites=new_sites, n_new=len(new_sites)))

rows.sort(key=lambda x: x["norm_load"])

print(f"亲本 PUF12-9：on={par_on:.3f}  脱靶位点={len(par_sites)}  脱靶负荷={par_load:.2f}")
print()
print("="*126)
print("表A  组合突变体「总体脱靶」最终筛查（活性 on≥0.30，按归一化脱靶负荷 = Σoff/on 升序，越低越特异）")
print("="*126)
print(f"{'突变':<20}{'on(388)':>8}{'脱靶数':>7}{'脱靶均值':>9}{'脱靶最大':>9}{'Σoff负荷':>9}"
      f"{'归一化负荷':>10}{'S全尺度':>8}{'vs亲本':>7}{'新增脱靶':>8}")
kept = []
for r in rows:
    if r["on"] < 0.30: continue
    kept.append(r)
    flag = "★" if r["norm_load"] < 3 and r["on"] >= 0.4 else ("⚠" if r["norm_load"] > 12 else "")
    print(f"{r['mutant']:<20}{r['on']:>8.3f}{r['n_off']:>7.1f}{r['off_mean']:>9.3f}{r['off_max']:>9.3f}"
          f"{r['load']:>9.2f}{r['norm_load']:>10.2f}{r['S']:>8.3f}{r['fold_vs_parent']:>7.2f}"
          f"{r['n_new']:>8}  {flag}")

print()
print("="*126)
print("表B  被活性下限排除的样本（on<0.30）—— 其「零脱靶」是活性过低造成的假象")
print("="*126)
print(f"{'突变':<20}{'on(388)':>9}{'脱靶数':>7}{'Σoff负荷':>9}   说明")
for r in sorted([x for x in rows if x['on'] < 0.30], key=lambda x: -x["on"]):
    print(f"{r['mutant']:<20}{r['on']:>9.3f}{r['n_off']:>7.1f}{r['load']:>9.2f}   活性仅为亲本的 {r['on']/par_on*100:.0f}%")

print()
print("="*126)
print("表C  新增脱靶位点（组合中检出、亲本从未检出）—— 检验「多点突变引入全新脱靶」")
print("="*126)
for r in sorted(rows, key=lambda x: -x["n_new"]):
    if r["n_new"] == 0 or r["on"] < 0.30: continue
    det = ", ".join(f"{p}({motif(p)},{r['off_max']:.2f}max)" for p in r["new_sites"][:6])
    print(f"{r['mutant']:<20} 新增 {r['n_new']} 个: {det}")

# 输出
with open("results/offtarget_screen_final.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["mutant", "n_rep", "on_388", "n_off", "off_mean", "off_max", "off_load_sum",
                "norm_load", "S_global", "fold_vs_parent", "n_new_offtarget", "new_offtarget_positions"])
    for r in rows:
        w.writerow([r["mutant"], r["n"], round(r["on"], 4), round(r["n_off"], 2), round(r["off_mean"], 4),
                    round(r["off_max"], 4), round(r["load"], 3), round(r["norm_load"], 3),
                    round(r["S"], 4), round(r["fold_vs_parent"], 3), r["n_new"],
                    ";".join(map(str, r["new_sites"]))])
print("\n写入 results/offtarget_screen_final.csv")
