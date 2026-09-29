# -*- coding: utf-8 -*-
"""
分析下一批补充突变（37 个突变组 + 2 个参照）的实验结果。

关键约定（来自工作表「核对说明」与用户口径）：
  · 0 值 = 源变异表未检出对应 C>T 记录，**不等同于真实编辑效率为 0**；
    因此 C871 = 0 时 +1 比不可定义，不得当作 0 值。
  · 测序深度 DP < 500 时该位点的编辑效率不可信。
  · 保留率 = C388 ÷ 0.8（表内固定参照，非本批亲本实测值）。

用法：uv run --with openpyxl python analyze_new_batch.py
产出：results/下一批突变_分组分析.csv
"""
import csv, os, re, sys, statistics as st
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
import openpyxl

XLSX = r"data\external\01a0e5c3-d4eb-773f-bf4a-68f616d99eb1.xlsx"
OUT = os.path.join("results", "下一批突变_分组分析.csv")
WT_C388 = 0.8          # 表内固定参照
DP_MIN = 500
POS = ["295", "388", "871"]
NOTE_COL = {"295": 7, "388": 8, "871": 9}


def load():
    ws = openpyxl.load_workbook(XLSX, data_only=True)["分组核对结果"]
    rows = [r for r in ws.iter_rows(values_only=True)][1:]
    return [r for r in rows if r and r[0]]


def parse_name(n):
    """G22609263048-b1-27D-30H-58M → ('b', 1, '27D-30H-58M')"""
    core = str(n).split("-", 1)[1] if "-" in str(n) else str(n)
    m = re.match(r"^([bc]?)(\d+)-(.+)$", core)
    return (m.group(1) or "a", int(m.group(2)), m.group(3)) if m else ("a", None, core)


def dp_from_note(txt):
    """从备注里取该位点的 DP；未检出记录时返回 None。"""
    if not isinstance(txt, str):
        return None
    m = re.search(r"DP=(\d+)", txt)
    return int(m.group(1)) if m else None


def detected(txt):
    return isinstance(txt, str) and "未检出" not in txt


def build(rows):
    groups = defaultdict(list)
    for r in rows:
        rep, idx, mut = parse_name(r[0])
        rec = {"sample": r[0], "rep": rep, "mut": mut}
        for p in POS:
            v = r[1 + int(p == "388") + int(p == "871")] if False else None
        rec["c295"], rec["c388"], rec["c871"] = r[1], r[2], r[3]
        rec["ret_sheet"] = r[4]
        for p in POS:
            rec[f"dp{p}"] = dp_from_note(r[NOTE_COL[p]])
            rec[f"det{p}"] = detected(r[NOTE_COL[p]])
        groups[idx].append(rec)
    return groups


def summarize(g):
    out = {}
    for p, key in (("388", "c388"), ("871", "c871")):
        vals = [x[key] for x in g
                if isinstance(x[key], (int, float)) and x[f"dp{p}"] is not None
                and x[f"dp{p}"] >= DP_MIN]
        out[f"n{p}"] = len(vals)
        out[f"m{p}"] = st.mean(vals) if vals else None
        out[f"dp{p}"] = [x[f"dp{p}"] for x in g]
        out[f"det{p}_all"] = all(x[f"det{p}"] for x in g)
    # 比：388 与 871 都必须可信且 871 > 0
    if out["m388"] is not None and out["m871"] not in (None, 0):
        out["ratio"] = out["m388"] / out["m871"]
    else:
        out["ratio"] = None
    out["ret"] = (out["m388"] / WT_C388) if out["m388"] is not None else None
    out["n"] = len(g)
    out["c871_zero"] = all((x["c871"] == 0) for x in g)
    return out


def main():
    rows = load()
    groups = build(rows)
    print(f"读入 {len(rows)} 个样本行，归入 {len(groups)} 组；DP 阈值 {DP_MIN}\n")

    # ---- 深度审计 ----
    print("=" * 84)
    print("一、深度审计")
    print("=" * 84)
    tot = {p: [0, 0, 0] for p in POS}     # [可信, 不足, 未检出记录]
    for g in groups.values():
        for x in g:
            for p in POS:
                d = x[f"dp{p}"]
                if d is None:
                    tot[p][2] += 1
                else:
                    tot[p][0 if d >= DP_MIN else 1] += 1
    for p, (ok, low, miss) in tot.items():
        s = ok + low + miss
        print(f"  位点 {p}: 可信 {ok:>3} / 深度不足 {low:>3} / 无记录 {miss:>3}"
              f"   （可信占 {ok/s*100:.0f}%）")

    # ---- 分组结果 ----
    print()
    print("=" * 84)
    print("二、逐组结果（剔除深度不足的样本后）")
    print("=" * 84)
    out = []
    for idx in sorted(k for k in groups if k is not None):
        g = groups[idx]
        mut = sorted({x["mut"] for x in g})[0]
        s = summarize(g)
        out.append({"index": idx, "mut": mut, **s})

    print(f"  {'突变':<26}{'n':>3}{'C388':>8}{'C871':>8}{'+1 比':>8}{'保留':>7}   备注")
    for r in sorted(out, key=lambda x: (x["ratio"] is None, -(x["ratio"] or 0))):
        c388 = f"{r['m388']:.3f}" if r["m388"] is not None else "—"
        c871 = f"{r['m871']:.3f}" if r["m871"] is not None else "—"
        rat = f"{r['ratio']:.2f}" if r["ratio"] else "—"
        ret = f"{r['ret']:.2f}" if r["ret"] is not None else "—"
        note = []
        if r["c871_zero"]:
            note.append("C871 两样本均未检出 → 比不可定义")
        elif r["ratio"] is None:
            note.append("871 无可信样本")
        if r["n388"] == 0:
            note.append("388 无可信样本")
        print(f"  {r['mut']:<26}{r['n']:>3}{c388:>8}{c871:>8}{rat:>8}{ret:>7}   {'; '.join(note)}")

    # ---- 参照 ----
    print()
    print("=" * 84)
    print("三、参照构建体")
    print("=" * 84)
    for idx in (47, 48):
        if idx in groups:
            g = groups[idx]
            s = summarize(g)
            print(f"  {sorted({x['mut'] for x in g})[0]:<10} C388={s['m388']:.4f} "
                  f"C871={s['m871']:.4f} 比={s['ratio']:.3f} 保留={s['ret']:.3f}")

    # ---- 写 CSV ----
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["组号", "突变", "样本数", "n_C388可信", "C388均值", "n_C871可信",
                    "C871均值", "plus1_ratio", "ratio_defined", "retention_vs_0.8",
                    "C871未检出"])
        for r in sorted(out, key=lambda x: x["index"]):
            w.writerow([r["index"], r["mut"], r["n"], r["n388"],
                        "" if r["m388"] is None else round(r["m388"], 4),
                        r["n871"], "" if r["m871"] is None else round(r["m871"], 4),
                        "" if r["ratio"] is None else round(r["ratio"], 4),
                        "TRUE" if r["ratio"] else "FALSE",
                        "" if r["ret"] is None else round(r["ret"], 4),
                        "TRUE" if r["c871_zero"] else "FALSE"])
    print(f"\n写入 {OUT}")


if __name__ == "__main__":
    main()
