# -*- coding: utf-8 -*-
"""
阶段 52 —— 导出「突变体基线 ΔCP（全 199 残基）」完整数据

背景：此前交付的 results/突变体ΔCP原始数据表.xlsx 只含「发生变化的 22 个残基」
      （|ΔΔCP| ≥ 0.05）。本脚本导出全 199 残基的完整 ΔCP / ΔΔCP 矩阵。

数据源：
  results/mut_cp_dcp.csv         batch1，14 个突变体 × 199 残基
                                 列：mut, resi, cp_G, cp_A, dcp, wt_cpG, wt_cpA, wt_dcp
  results/mut_cp_dcp_batch2.csv  batch2，7 个突变体 + 独立 WT 重跑 × 199 残基
                                 列：mut, resi, cp_G, cp_A, dcp, wt_dcp

定义：
  ΔCP = CP(GCA) − CP(GCG)，CP = 「该残基 ↔ +1 位核苷酸」的 AF3 接触概率
  ΔΔCP = ΔCP(突变体) − ΔCP(WT)
  正 ΔΔCP = 换成 A 后接触增强（偏向脱靶）；负 = 减弱

产出：results/突变体基线ΔCP_全199残基.xlsx
      1_ΔCP矩阵         199 残基 × (WT基线 + 21 突变体)
      2_ΔΔCP矩阵        199 残基 × 21 突变体
      3_长格式明细       每行 = 一个(突变体, 残基)
      4_WT重复性参考     batch2 独立 WT 重跑 vs 基线 → AF3 自身噪声量级
      5_汇总
"""
import csv, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

NAVY, LIGHT, ACC = "1F3B66", "F2F4F8", "B44A3C"
RED = PatternFill("solid", fgColor="F8D7DA")     # ΔΔCP ≥ +0.15
BLU = PatternFill("solid", fgColor="D6E4F7")     # ΔΔCP ≤ −0.10
HDR = PatternFill("solid", fgColor=NAVY)
THIN = Border(*[Side(style="thin", color="BFBFBF")] * 4)
N = 199

WT_SEQ = ("MEASPASGPRHLMDPAIFTSNFNNGIGRHKTYLCYEVERLDNGTSVKMDQHRGFLHNQAKNLLCGFYGRHVEVNFIKKFTSERDF"
          "HPSMSCSITWFLSWSPCWECSQAIREFLSRHPGVTLVIYVARLFWHMDQQNRQGLRDLVNSGVTIQIMTYDEFKHCWDTFVDHQG"
          "APFQPWDGLDEHSQALSGRLRAILQNQGN")
assert len(WT_SEQ) == N, f"序列长度 {len(WT_SEQ)} != {N}"
AA = {i + 1: a for i, a in enumerate(WT_SEQ)}

# ---------- 读数据 ----------
b1 = list(csv.DictReader(open("results/mut_cp_dcp.csv", encoding="utf-8-sig")))
b2 = list(csv.DictReader(open("results/mut_cp_dcp_batch2.csv", encoding="utf-8-sig")))

# 突变体展示名
NAME = {"a59p": "A59P", "g25e": "G25E", "g25ek30h": "G25E-K30H", "g27d": "G27D",
        "g27dk30h": "G27D-K30H", "g27dk30hq58m": "G27D-K30H-Q58M", "g27t": "G27T",
        "g27tk30h": "G27T-K30H", "g27tk30hq58m": "G27T-K30H-Q58M", "k30h": "K30H",
        "k30hq58m": "K30H-Q58M", "k60r": "K60R", "m132d": "M132D", "m132e": "M132E",
        "q58m": "Q58M", "r28a": "R28A", "r28s": "R28S", "t31i": "T31I", "t31l": "T31L",
        "t31v": "T31V", "y32f": "Y32F"}
ORDER = ["g25e", "g25ek30h", "g27t", "g27d", "g27tk30h", "g27dk30h", "g27tk30hq58m",
         "g27dk30hq58m", "k30h", "k30hq58m", "q58m", "r28a", "r28s", "t31v", "t31i",
         "t31l", "y32f", "a59p", "k60r", "m132d", "m132e"]

# 基线（三文件已校验逐残基一致）
WT = np.array([float(r["wt_dcp"]) for r in b1 if r["mut"] == "g25e"])

DCP, WTCP = {}, {}
for r in b1:
    DCP.setdefault(r["mut"], {})[int(r["resi"])] = float(r["dcp"])
    WTCP.setdefault(r["mut"], {})[int(r["resi"])] = (float(r["wt_cpG"]), float(r["wt_cpA"]))
WTRUN2 = None
for r in b2:
    if r["mut"] == "wt":
        WTRUN2 = DCP.get("__wt2__", {})
    DCP.setdefault(r["mut"], {})[int(r["resi"])] = float(r["dcp"])

MUTS = [m for m in ORDER if m in DCP]
print(f"突变体 {len(MUTS)} 个，基线残基数 {len(WT)}")

X = np.array([[DCP[m][i] for i in range(1, N + 1)] for m in MUTS])       # (M,199) ΔCP
D = X - WT[None, :]                                                      # ΔΔCP


def fm(v, nd=4):
    return round(float(v), nd)


# ---------- 写 Excel ----------
wb = Workbook()


def style_header(ws, ncol, widths):
    for c in range(1, ncol + 1):
        cell = ws.cell(1, c)
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.fill = HDR
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "D2"


def paint(ws, r0, c0, nr, nc, arr, hi=0.15, lo=-0.10):
    for i in range(nr):
        for j in range(nc):
            v = arr[i, j]
            if v >= hi:
                ws.cell(r0 + i, c0 + j).fill = RED
            elif v <= lo:
                ws.cell(r0 + i, c0 + j).fill = BLU


# --- Sheet1 ΔCP 矩阵 ---
ws = wb.active
ws.title = "1_ΔCP矩阵"
ws.append(["残基", "WT", "区域"] + [NAME.get(m, m) for m in MUTS])
for i in range(1, N + 1):
    ws.append([i, AA[i], ""] + [fm(DCP[m][i]) for m in MUTS])
style_header(ws, 3 + len(MUTS), [7, 6, 10] + [11] * len(MUTS))
for r in range(2, N + 2):
    ws.cell(r, 1).font = Font(bold=True, size=9)
    ws.cell(r, 2).font = Font(bold=True, size=9)
ws.cell(N + 3, 1, "ΔCP = CP(GCA) − CP(GCG)；CP 为 AF3「该残基 ↔ +1 位核苷酸」接触概率").font = Font(italic=True, size=9)

# --- Sheet2 ΔΔCP 矩阵 ---
ws2 = wb.create_sheet("2_ΔΔCP矩阵")
ws2.append(["残基", "WT", "区域"] + [NAME.get(m, m) for m in MUTS])
for i in range(1, N + 1):
    ws2.append([i, AA[i], ""] + [fm(D[k, i - 1]) for k, m in enumerate(MUTS)])
style_header(ws2, 3 + len(MUTS), [7, 6, 10] + [11] * len(MUTS))
paint(ws2, 2, 4, N, len(MUTS), D.T)
for r in range(2, N + 2):
    ws2.cell(r, 1).font = Font(bold=True, size=9)
    ws2.cell(r, 2).font = Font(bold=True, size=9)
ws2.cell(N + 3, 1, "ΔΔCP = ΔCP(突变体) − ΔCP(WT)；红 ≥ +0.15（偏脱靶），蓝 ≤ −0.10（偏 on-target）").font = Font(italic=True, size=9)

# --- Sheet3 长格式 ---
ws3 = wb.create_sheet("3_长格式明细")
ws3.append(["突变体", "残基", "WT_aa", "CP_GCG", "CP_GCA", "ΔCP_突变体", "ΔCP_WT", "ΔΔCP", "|ΔΔCP|≥0.05"])
nch = 0
for k, m in enumerate(MUTS):
    for i in range(1, N + 1):
        g, a = WTCP.get(m, {}).get(i, (None, None))
        if g is None:                       # batch2 无 wt_cpG/wt_cpA 列，用 dcp 反推：
            g, a = "", ""                   # CP_GCG/CP_GCA 留空（batch2 未导出分项）
        dd = D[k, i - 1]
        flag = "是" if abs(dd) >= 0.05 else ""
        if flag:
            nch += 1
        ws3.append([NAME.get(m, m), i, AA[i], g, a, fm(DCP[m][i]), fm(WT[i - 1]), fm(dd), flag])
style_header(ws3, 9, [16, 7, 7, 10, 10, 13, 11, 11, 15])
ws3.auto_filter.ref = f"A1:I{ws3.max_row}"
print(f"长格式行数 {ws3.max_row - 1}，其中 |ΔΔCP|≥0.05 的 {nch} 行")

# --- Sheet4 WT 重复性参考 ---
ws4 = wb.create_sheet("4_WT重复性参考")
b2wt = [float(r["dcp"]) for r in b2 if r["mut"] == "wt"]
ws4.append(["残基", "WT_aa", "ΔCP_基线(AF3批1)", "ΔCP_WT独立重跑(AF3批2)", "差值(=AF3自身噪声)"])
for i in range(1, N + 1):
    ws4.append([i, AA[i], fm(WT[i - 1]), fm(b2wt[i - 1]), fm(b2wt[i - 1] - WT[i - 1])])
style_header(ws4, 5, [7, 7, 20, 24, 20])
dif = np.array(b2wt) - WT
ws4.cell(N + 3, 1, f"均值 {dif.mean():+.4f}   SD {dif.std(ddof=1):.4f}   最大|差| {np.abs(dif).max():.4f}").font = Font(bold=True, size=9)
ws4.cell(N + 4, 1, "同一 WT 序列、不同 AF3 作业之间的差异 = 本方法噪声下限；小于此量级的 ΔΔCP 不可解读").font = Font(italic=True, size=9)

# --- Sheet5 汇总 ---
ws5 = wb.create_sheet("5_汇总")
ws5.append(["突变体", "残基数", "|ΔΔCP|≥0.05 的残基数", "|ΔΔCP|≥0.10", "max|ΔΔCP|", "mean ΔCP(突变体)", "mean ΔCP(WT)", "ΣCP_GCG", "ΣCP_GCA"])
for k, m in enumerate(MUTS):
    dd = D[k]
    dcp_m = np.array([DCP[m][i] for i in range(1, N + 1)])
    ws5.append([NAME.get(m, m), N, int((np.abs(dd) >= 0.05).sum()), int((np.abs(dd) >= 0.10).sum()),
                fm(np.abs(dd).max()), fm(dcp_m.mean()), fm(WT.mean()),
                fm(dcp_m[dcp_m > 0].sum()), fm((-dcp_m[dcp_m < 0]).sum())])
ws5.append(["（WT 基线）", N, 0, 0, 0, fm(WT.mean(), 4), fm(WT.mean(), 4), "", ""])
style_header(ws5, 9, [16, 8, 20, 15, 12, 17, 15, 11, 11])
ws5.auto_filter.ref = f"A1:I{ws5.max_row}"

wb.save("results/突变体基线ΔCP_全199残基.xlsx")
print("写入 results/突变体基线ΔCP_全199残基.xlsx")

# ---------- 控制台核对 ----------
print("\n" + "=" * 100)
print("各突变体相对 WT 基线的 ΔΔCP 分布（全 199 残基）")
print("=" * 100)
print(f"{'突变体':<18}{'|ΔΔ|≥0.05':>10}{'|ΔΔ|≥0.10':>10}{'max|ΔΔ|':>10}"
      f"{'max(ΔΔ)':>10}{'min(ΔΔ)':>10}{'ΔΔ总量':>10}")
for k, m in enumerate(MUTS):
    dd = D[k]
    print(f"{NAME.get(m, m):<18}{int((np.abs(dd)>=0.05).sum()):>10}{int((np.abs(dd)>=0.10).sum()):>10}"
          f"{np.abs(dd).max():>10.3f}{dd.max():>+10.3f}{dd.min():>+10.3f}{dd.sum():>+10.3f}")

print("\n【AF3 自身噪声参考】WT 独立重跑 vs 基线：")
print(f"  mean={dif.mean():+.4f}  SD={dif.std(ddof=1):.4f}  max|差|={np.abs(dif).max():.4f}")
print(f"  → |ΔΔCP| < {np.abs(dif).max():.3f} 的残基差异不可解读")
