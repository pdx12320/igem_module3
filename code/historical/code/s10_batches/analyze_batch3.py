# -*- coding: utf-8 -*-
"""
第三批补充数据（64 样本 / 29 同名组）分析。

数据源：merged_data_64样本_同名分组_C295_C388_C871.xlsx（工作表「分组核对结果」）
产出：results/第三批_分组分析.csv、results/第三批_绘图用表.csv
用法：uv run --with openpyxl python analyze_batch3.py
"""
import collections, csv, io, os, re, statistics as st, sys
import openpyxl

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = (r"data\external"
       r"\01a0ebae-7d96-70fe-9b5b-e61e328d0def.xlsx")
OUT = os.path.join(ROOT, "results")

# 同批亲本（PUF12，n=2）实测值，用于计算保留率与 ROF
PARENT_C388 = None      # 下面由数据算出
WT_REF = 0.8            # 源表「列2」使用的固定参照

wb = openpyxl.load_workbook(SRC, data_only=True)
rows = list(wb["分组核对结果"].iter_rows(values_only=True))[1:]

gkey = lambda n: re.sub(r"^G\d+-(b?\d+)-", "", n)
groups = collections.OrderedDict()
for r in rows:
    groups.setdefault(gkey(r[0]), []).append(r)

mean = lambda v: st.mean([x for x in v if x is not None])
dp_of = lambda txt: [int(m.group(1)) for m in re.finditer(r"DP=(\d+)", str(txt))]

parent = groups["PUF12"]
PARENT_C388 = mean([r[2] for r in parent])
PARENT_C871 = mean([r[3] for r in parent])
PARENT_RATIO = PARENT_C388 / PARENT_C871

order = ["PUF10", "PUF12", "PUF12-129Y", "PUF12-129Y-132T"]
names = list(groups)
muts = [n for n in names if n not in order]
# 展示顺序：单点按位点、组合在后
def sort_key(n):
    parts = n.split("-")
    lead = int(re.match(r"(\d+)", parts[0]).group(1))
    return (len(parts), lead, n)
muts.sort(key=sort_key)

recs = []
for name in names:
    v = groups[name]
    c295, c388, c871 = (mean([r[i] for r in v]) for i in (1, 2, 3))
    ratio = c388 / c871 if c871 else None
    recs.append(dict(
        mut=name, n=len(v), c295=c295, c388=c388, c871=c871,
        n295=sum(1 for r in v if r[1] is not None),
        ratio=ratio,
        ret=c388 / PARENT_C388,
        rof=ratio / PARENT_RATIO if ratio else None,
        dp_min=min([d for r in v for d in dp_of(r[7])] or [0]),
        is_ref="TRUE" if name in order else "FALSE",
    ))

# ------------------------------------------------------------------ CSV 输出
def wr(path, header, data):
    with io.open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(header)
        for row in data: w.writerow(row)
    print("  写入", os.path.basename(path), f"({len(data)} 行)")

def f(x, nd=5):
    return "" if x is None else round(x, nd)

wr(os.path.join(OUT, "第三批_分组分析.csv"),
   ["mutant", "n_samples", "n_with_C295_record", "C295_mean", "C388_mean", "C871_mean",
    "plus1_ratio_defined", "plus1_ratio_GCG_over_GCA", "activity_retention_vs_batch_parent",
    "ROF_ratio_over_same_batch_parent", "min_read_depth", "is_reference_group"],
   [[r["mut"], r["n"], r["n295"], f(r["c295"]), f(r["c388"]), f(r["c871"]),
     "TRUE" if r["ratio"] else "FALSE", f(r["ratio"]), f(r["ret"]), f(r["rof"]),
     r["dp_min"], r["is_ref"]] for r in recs])

wr(os.path.join(OUT, "第三批_绘图用表.csv"),
   ["mut", "grp", "ratio", "rof", "ret", "c388", "c871", "c295",
    "c295_not_detected", "n", "is_ref"],
   [[r["mut"],
     "ref" if r["is_ref"] == "TRUE" else ("single" if "-" not in r["mut"] else "combo"),
     f(r["ratio"]), f(r["rof"]), f(r["ret"]), f(r["c388"]), f(r["c871"]), f(r["c295"]),
     "TRUE" if (r["c295"] is not None and r["c295"] == 0) else "FALSE",
     r["n"], r["is_ref"]] for r in recs])

# ------------------------------------------------------------------ 控制台
print(f"\n同批亲本 PUF12：C388 = {PARENT_C388:.4f}、C871 = {PARENT_C871:.4f}、比值 = {PARENT_RATIO:.4f}")
print(f"{'组':<20}{'n':>2}{'C388':>9}{'C871':>9}{'比值':>8}{'保留':>8}{'ROF':>8}  C295")
print("-" * 74)
for r in recs:
    c295 = "未检出" if r["c295"] == 0 else (f"{r['c295']:.4f}" if r["c295"] is not None else "无记录")
    print(f"{r['mut']:<20}{r['n']:>2}{r['c388']:>9.4f}{r['c871']:>9.4f}"
          f"{r['ratio']:>8.3f}{r['ret']:>8.3f}{r['rof']:>8.3f}  {c295}")

print("\n【单点】按 ROF 排序：")
singles = [r for r in recs if r["is_ref"] == "FALSE" and "-" not in r["mut"]]
for r in sorted(singles, key=lambda x: -x["rof"]):
    print(f"  {r['mut']:<8} ROF {r['rof']:.3f}  比值 {r['ratio']:.3f}  保留 {r['ret']:.3f}")

print("\n【组合】")
for r in recs:
    if r["is_ref"] == "FALSE" and "-" in r["mut"]:
        print(f"  {r['mut']:<18} ROF {r['rof']:.3f}  比值 {r['ratio']:.3f}  保留 {r['ret']:.3f}")
