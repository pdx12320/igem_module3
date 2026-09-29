# -*- coding: utf-8 -*-
"""
位点 29 近饱和扫描（及位点 30 等）的数据分析。

关键约束（用户提供）：某位点的测序深度 DP < 500 时，该位点的编辑效率不可信。

产出：控制台报告 + results/位点29_30扫描_深度筛选后.csv
"""
import csv, os, sys, statistics as st
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
import openpyxl

XLSX = r"data\external\01a0cc4e-6941-7658-85b3-ea7882dadd61.xlsx"
OUT = os.path.join("results", "位点29_30扫描_深度筛选后.csv")
DP_MIN = 500
POS = {"295": (4, 9), "388": (5, 10), "871": (6, 11)}   # 列索引：(编辑值, 深度)


def load():
    ws = openpyxl.load_workbook(XLSX, data_only=True)["Sheet1"]
    rows = [r for r in ws.iter_rows(values_only=True)][1:]
    return [r for r in rows if r and r[2]]


def label_of(pair, names):
    """样本名形如 '1-29G' 与 '1-129G'（第二个把配对号重复了一遍）。
    取最短的后缀作为突变标签——重复编号的那个必然更长。"""
    sufs = [str(n).split("-", 1)[1] for n in names if "-" in str(n)]
    return min(sufs, key=len) if sufs else str(names[0])


def build(rows):
    """只有「Pair_Number-标签」形式的样本才归入构建体。
    文件后段有若干行（a1/1/c1/D1/Z3 等）复用了 pair 编号但没有该前缀，
    把它们并入会把无关样本混进同一构建体。"""
    by_pair = defaultdict(list)
    stray = []
    for r in rows:
        name = r[2]
        ok = (r[0] is not None and isinstance(name, str)
              and name.startswith(f"{r[0]}-") and len(name.split("-", 1)[1]) > 0)
        if ok:
            by_pair[r[0]].append(r)
        else:
            stray.append(r)
    recs = []
    for pair, group in by_pair.items():
        lab = label_of(pair, [g[2] for g in group])
        rec = {"pair": pair, "label": lab, "n": len(group)}
        for name, (ci, di) in POS.items():
            # 逐样本配对（值, 深度）；深度缺失单独记为 None，不影响其它样本
            pairs = []
            for g in group:
                v, d = g[ci], g[di]
                pairs.append((float(v) if isinstance(v, (int, float)) else None,
                              int(d) if isinstance(d, (int, float)) else None))
            rec[f"p_{name}"] = pairs
        recs.append(rec)
    return recs, stray


def summarize(rec):
    """对每个位点：只保留 DP≥500 的样本，返回均值与可用样本数。"""
    out = {}
    for name in POS:
        pairs = rec[f"p_{name}"]
        ok = [v for v, d in pairs if v is not None and d is not None and d >= DP_MIN]
        lows = [d for v, d in pairs if d is not None and d < DP_MIN]
        nod = [1 for v, d in pairs if d is None and v is not None]
        out[f"n_{name}"] = len(ok)
        out[f"m_{name}"] = st.mean(ok) if ok else None
        out[f"dmin_{name}"] = min(d for _, d in pairs if d is not None) if any(
            d is not None for _, d in pairs) else None
        out[f"dmax_{name}"] = max(d for _, d in pairs if d is not None) if any(
            d is not None for _, d in pairs) else None
        out[f"nopd_{name}"] = len(lows) + len(nod)      # 不可信的样本数
    # +1 比：388 与 871 都要可信，且 871 > 0
    if out["m_388"] is not None and out["m_871"] not in (None, 0):
        out["ratio"] = out["m_388"] / out["m_871"]
    else:
        out["ratio"] = None
    return out


def main():
    rows = load()
    recs, stray = build(rows)
    print(f"读入 {len(rows)} 个样本行，归入 {len(recs)} 个构建体；另有 {len(stray)} 行无配对编号")
    print(f"深度阈值：DP ≥ {DP_MIN}\n")

    # ---------- 1. 深度审计 ----------
    print("=" * 78)
    print("一、深度审计")
    print("=" * 78)
    total = {"295": [0, 0, 0], "388": [0, 0, 0], "871": [0, 0, 0]}  # [可信, <500, 无记录]
    for r in recs:
        for name in POS:
            for v, d in r[f"p_{name}"]:
                if d is None:
                    total[name][2] += 1
                else:
                    total[name][0 if d >= DP_MIN else 1] += 1
    for name, (ok, low, miss) in total.items():
        tot = ok + low + miss
        print(f"  位点 {name}: 可信 {ok:>3} / 深度不足 {low:>3} / 无深度记录 {miss:>3}"
              f"   （合计 {tot}，可信占 {ok/tot*100:.0f}%）")

    # ---------- 2. 位点 29 系列 ----------
    print()
    print("=" * 78)
    print("二、位点 29 近饱和扫描（18 个替换）——深度筛选后")
    print("=" * 78)
    p29 = [r for r in recs if r["label"].startswith("29") and r["label"][2:].isupper()
           and len(r["label"]) == 3]
    print(f"  找到 {len(p29)} 个 29 位替换：{', '.join(sorted(r['label'] for r in p29))}")
    print()
    print(f"  {'突变':<7}{'n(388)':>7}{'C388':>8}{'n(871)':>7}{'C871':>8}{'+1 比':>8}   备注")
    rows_out = []
    for r in sorted(p29, key=lambda x: x["label"]):
        s = summarize(r)
        note = []
        if s["m_388"] is None:
            note.append("388 全不可信")
        if s["m_871"] is None:
            note.append("871 全不可信")
        elif s["m_871"] == 0:
            note.append("871 检出为 0")
        if s["nopd_295"]:
            note.append(f"295 深度不足×{s['nopd_295']}")
        c388 = f"{s['m_388']:.3f}" if s["m_388"] is not None else "—"
        c871 = f"{s['m_871']:.3f}" if s["m_871"] is not None else "—"
        rat = f"{s['ratio']:.2f}" if s["ratio"] else "—"
        print(f"  {r['label']:<7}{s['n_388']:>7}{c388:>8}{s['n_871']:>7}{c871:>8}{rat:>8}   {'; '.join(note)}")
        rows_out.append({"位点": 29, "突变": r["label"], **s})

    # ---------- 2b. 活性归一化后的重排（关键） ----------
    summ = {r["label"]: summarize(r) for r in recs}
    par = summ.get("PUF12-9")
    print()
    print("=" * 78)
    print("三、位点 29 系列：活性归一化后重排（同批亲本 PUF12-9）")
    print("=" * 78)
    if par and par["m_388"] and par["ratio"]:
        pc, pr = par["m_388"], par["ratio"]
        print(f"  同批亲本 PUF12-9：C388 = {pc:.3f}，C871 = {par['m_871']:.3f}，"
              f"+1 比 = {pr:.3f}（n = {par['n_388']}）")
        print(f"  注：亲本两个样本的 C388 分别为 "
              f"{'/'.join(f'{v:.3f}' for v, d in recs[[x['label'] for x in recs].index('PUF12-9')]['p_388'] if v is not None)}，"
              f"样本间本身有差异")
        print()
        print(f"  {'突变':<7}{'C388':>8}{'保留':>8}{'+1 比':>8}{'ROF':>7}{'达活性下限':>11}   结论")
        cand = [r for r in p29 if summ[r["label"]]["ratio"]]
        for r in sorted(cand, key=lambda x: -summ[x["label"]]["ratio"]):
            s = summ[r["label"]]
            keep = s["m_388"] / pc
            rof = s["ratio"] / pr
            floor = "是" if s["m_388"] >= 0.30 else "否"
            verdict = "可比" if s["m_388"] >= 0.30 else "低活性、比值不可比"
            print(f"  {r['label']:<7}{s['m_388']:>8.3f}{keep:>8.2f}{s['ratio']:>8.2f}"
                  f"{rof:>7.2f}{floor:>11}   {verdict}")
        k30 = summ.get("30H")
        if k30 and k30["ratio"]:
            print()
            print(f"  对照 K30H（本次）：C388 = {k30['m_388']:.3f}"
                  f"（保留 {k30['m_388']/pc:.2f}），+1 比 = {k30['ratio']:.2f}，"
                  f"ROF = {k30['ratio']/pr:.2f}")
            print(f"  对照 K30H（既有单点批，results/experimental_ranking.csv）："
                  f"+1 比 1.71，保留 0.84，亲本比 1.371 → ROF = {1.71/1.371:.2f}")
    else:
        print("  未取到同批亲本 PUF12-9，跳过归一化")

    # ---------- 3. 位点 30 系列（含与既有数据的对照） ----------
    print()
    print("=" * 78)
    print("三、位点 30 系列——与本项目既有单点数据的交叉验证")
    print("=" * 78)
    p30 = [r for r in recs if r["label"].startswith("30") and len(r["label"]) == 3]
    KNOWN = {"30H": 1.71, "30G": 1.34, "30N": 1.48, "30R": 1.34}   # 既有单点批
    print(f"  {'突变':<7}{'n(388)':>7}{'C388':>8}{'C871':>8}{'本次比':>8}{'既有比':>8}   备注")
    for r in sorted(p30, key=lambda x: x["label"]):
        s = summarize(r)
        c388 = f"{s['m_388']:.3f}" if s["m_388"] is not None else "—"
        c871 = f"{s['m_871']:.3f}" if s["m_871"] is not None else "—"
        rat = f"{s['ratio']:.2f}" if s["ratio"] else "—"
        old = f"{KNOWN[r['label']]:.2f}" if r["label"] in KNOWN else "—"
        flag = ""
        if r["label"] in KNOWN and s["ratio"]:
            d = s["ratio"] - KNOWN[r["label"]]
            flag = f"差 {d:+.2f}" + ("  ← 方向不一致" if d * KNOWN[r["label"]] < 0 else "")
        print(f"  {r['label']:<7}{s['n_388']:>7}{c388:>8}{c871:>8}{rat:>8}{old:>8}   {flag}")
        rows_out.append({"位点": 30, "突变": r["label"], **s})

    # ---------- 4. 参比构建体 ----------
    print()
    print("=" * 78)
    print("四、参比构建体（同批亲本与靶向模块变体）")
    print("=" * 78)
    ref = [r for r in recs if "PUF" in r["label"]]
    print(f"  {'构建体':<16}{'n(388)':>7}{'C388':>8}{'C871':>8}{'+1 比':>8}")
    for r in sorted(ref, key=lambda x: x["label"]):
        s = summarize(r)
        c388 = f"{s['m_388']:.3f}" if s["m_388"] is not None else "—"
        c871 = f"{s['m_871']:.3f}" if s["m_871"] is not None else "—"
        rat = f"{s['ratio']:.2f}" if s["ratio"] else "—"
        print(f"  {r['label']:<16}{s['n_388']:>7}{c388:>8}{c871:>8}{rat:>8}")

    if stray:
        print()
        print("=" * 78)
        print(f"五、未归入构建体的 {len(stray)} 行（缺少「配对号-标签」前缀，需你确认身份）")
        print("=" * 78)
        print(f"  {'样本':<8}{'pair':>6}{'C295':>9}{'C388':>9}{'C871':>9}"
              f"{'DP295':>7}{'DP388':>7}{'DP871':>7}   可用性")
        for r in stray:
            def g(i, j):
                v, d = r[i], r[j]
                s = f"{v:.3f}" if isinstance(v, (int, float)) else "—"
                dd = str(int(d)) if isinstance(d, (int, float)) else "—"
                return s, dd
            v295, d295 = g(4, 9); v388, d388 = g(5, 10); v871, d871 = g(6, 11)
            flags = []
            if not isinstance(r[10], (int, float)) or r[10] < DP_MIN: flags.append("388 不可信")
            if not isinstance(r[11], (int, float)) or r[11] < DP_MIN: flags.append("871 不可信")
            print(f"  {str(r[2]):<8}{str(r[0]):>6}{v295:>9}{v388:>9}{v871:>9}"
                  f"{d295:>7}{d388:>7}{d871:>7}   {'; '.join(flags) or '两者可信'}")

    # ---------- 写 CSV ----------
    if rows_out:
        keys = ["位点", "突变", "n", "n_295", "m_295", "n_388", "m_388", "n_871", "m_871",
                "dmin_388", "dmax_388", "dmin_871", "dmax_871", "nopd_295", "nopd_388",
                "nopd_871", "ratio"]
        with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            w.writeheader()
            for r in rows_out:
                w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
        print(f"\n写入 {OUT}")


def figure(recs, summ):
    """位点 29/30 扫描总览：活性混淆 + 与既有批次的交叉验证。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    sys.path.insert(0, os.path.join("文案数据图表整理", "APOBEC_DryLab_Complete"))
    from orca_drylab_style import (canvas, titles, footnotes, style_axes, panel,
                                   legend_below, save_checked, BLUE, ORANGE, GREEN,
                                   GREY, INK, RULE)

    par = summ["PUF12-9"]
    pc, pr = par["m_388"], par["ratio"]
    p29 = [r["label"] for r in recs if len(r["label"]) == 3 and r["label"].startswith("29")]
    p30 = [r["label"] for r in recs if len(r["label"]) == 3 and r["label"].startswith("30")]
    FLOOR = 0.30

    fig, (a, b) = canvas(w=15.8, h=9.0, ncols=2, wspace=.22, bottom=.30, top=.83)
    ok, low = [], []
    for lab in sorted(p29):
        s = summ[lab]
        if not s["ratio"]:
            continue
        (ok if s["m_388"] >= FLOOR else low).append((s["m_388"], s["ratio"], lab))
    for pts, col, name in ((low, GREY, "on-target below the 0.30 floor"),
                           (ok, BLUE, "on-target ≥ 0.30 floor")):
        if pts:
            a.scatter([p[0] for p in pts], [p[1] for p in pts], s=105, color=col,
                      edgecolor="white", linewidth=1.1, zorder=4, label=name)
    for x_, y_, lab in ok + low:
        if lab in ("29Y", "29N", "29R", "29A", "29S") or y_ >= 1.4:
            a.annotate(lab, (x_, y_), textcoords="offset points", xytext=(7, -3),
                       fontsize=9.5, color=INK)
    a.axvline(FLOOR, color=ORANGE, ls="--", lw=1.5, zorder=2)
    a.axhline(pr, color=RULE, ls=":", lw=1.5, zorder=2)
    a.text(FLOOR, a.get_ylim()[1], " floor 0.30", va="top", ha="left", fontsize=9.5,
           color=ORANGE)
    a.text(a.get_xlim()[1], pr, "parent ratio 1.32 ", va="bottom", ha="right",
           fontsize=9.5, color=GREY)
    a.set_xlabel("on-target editing, c.388 (fraction)")
    a.set_ylabel("+1 ratio (c.388 / c.871)")
    a.set_title("Position 29 substitutions", fontsize=11.5, color=INK, pad=8)
    style_axes(a, grid="both"); panel(a, "A")

    KNOWN = {"30H": 1.71, "30N": 1.48, "30R": 1.34, "30G": 1.34}
    shared = [(l, summ[l]["ratio"], KNOWN[l]) for l in sorted(p30)
              if l in KNOWN and summ[l]["ratio"]]
    if shared:
        y = np.arange(len(shared))
        for i, (lab, now, old) in enumerate(shared):
            b.plot([old, now], [i, i], color=GREY, lw=1.6, zorder=2)
        b.scatter([o for _, _, o in shared], y, s=105, facecolor="white",
                  edgecolor=ORANGE, linewidth=1.8, zorder=4, label="earlier single-mutant batch")
        b.scatter([n for _, n, _ in shared], y, s=105, color=BLUE, edgecolor="white",
                  linewidth=1.1, zorder=5, label="this sequencing run")
        for i, (lab, now, old) in enumerate(shared):
            if abs(now - old) > 0.2:
                b.annotate(f"{now - old:+.2f}", ((now + old) / 2, i),
                           textcoords="offset points", xytext=(0, 9), ha="center",
                           fontsize=9.5, color=INK, fontweight="bold")
        b.set_yticks(y); b.set_yticklabels([s[0] for s in shared])
        b.set_xlabel("+1 ratio (c.388 / c.871)")
        b.set_title("Cross-check against the earlier batch", fontsize=11.5, color=INK, pad=8)
        style_axes(b, grid="x"); panel(b, "B")
    else:
        b.text(.5, .5, "no shared substitution", ha="center", va="center",
               transform=b.transAxes, color=GREY)

    titles(fig, "Position 29 saturation, read under the sequencing-depth filter",
           "Only samples with depth ≥ 500 at the measured position are used. The parent is the "
           "same-batch construct PUF12-9 (c.388 = 0.595, ratio 1.32).")
    legend_below(fig, *[None, None], ncol=3, y=.175) if False else None
    handles = []
    if low:
        handles.append(plt.Line2D([], [], marker="o", ls="", ms=10, color=GREY,
                                  label="on-target below the 0.30 floor"))
    if ok:
        handles.append(plt.Line2D([], [], marker="o", ls="", ms=10, color=BLUE,
                                  label="on-target ≥ 0.30 floor"))
    if shared:
        handles.append(plt.Line2D([], [], marker="o", ls="", ms=10, mfc="white", mec=ORANGE,
                                  mew=1.8, label="earlier single-mutant batch"))
        handles.append(plt.Line2D([], [], marker="o", ls="", ms=10, color=BLUE,
                                  label="this sequencing run"))
    legend_below(fig, handles, None, ncol=4, y=.175)
    footnotes(fig, [
        "A  substitutions with low on-target editing occupy the upper left: their ratios rise as activity falls, the same coupling seen in the amplicon scan.",
        "B  the four substitutions measured in both batches; K30H is the only one that does not reproduce.",
        "†  c.295 was excluded: 52 of 82 samples carry no depth record at that position, so a recorded zero there cannot be interpreted.",
    ], start=.105, step=.026)
    out = os.path.join("results", "figs", "pos29_screen_depth_filtered.png")
    return save_checked(fig, out)


if __name__ == "__main__":
    main()
    print()
    print("=" * 78)
    print("六、图")
    print("=" * 78)
    try:
        rows = load()
        recs, _ = build(rows)
        summ = {r["label"]: summarize(r) for r in recs}
        print("  写入", figure(recs, summ))
    except Exception as e:
        print(f"  绘图跳过：{type(e).__name__}: {e}")
