# -*- coding: utf-8 -*-
"""
阶段 41 —— 湿实验「完全失活」阴性对照候选表

判定口径（三层，缺一不可）：
  ① 活性保留率 ≈ 0（C388 相对亲本）
  ② 测序深度充足（med_dp ≥ 300），排除"测不到"而非"真失活"
  ③ 区分「真 0」与「检测限伪 0」：本数据集 1 条变异读长 ≈ 0.077%（深度 1300 时），
     故 0.051–0.096% 一类反复出现的数值实为「1 条读长」，按伪 0 处理并标注。

产出：results/阴性对照候选表.xlsx / .csv
"""
import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

NAVY = "1F3B66"; LIGHT = "F2F4F8"
C_REC = "E6F4EA"   # 推荐
C_MID = "FFF4CC"   # 备选
C_BAD = "FBE3E1"   # 排除

# 位点角色（来自前期结构/保守性/共进化分析）
ROLE = {
    57: "loop3 催化必需（与靶碱基成氢键；共进化 MI 最高 0.30）",
    31: "＋1 阅读器 A 侧（PSSM 家族频率 0%D/E/Y，大侧链/电荷与口袋失配）",
    58: "loop3 排 A 位（高比低保留的代表位点）",
    98: "WS 环（保守性 0.91，慎动）",
    28: "loop1-N 口袋壁（保守性 0.84）",
    132: "loop7 出口通道（保守性 0.05，可动）",
    30: "＋1 阅读器主位（最佳单点来源）",
    25: "loop1-N（与 K30 共变 MI 1.07，最高）",
    130: "loop7 探针（保守性 0.03，可动）",
}

# ---------------------------------------------------------------- 读数据
singles = list(csv.DictReader(open("results/experimental_ranking.csv", encoding="utf-8-sig")))
per = list(csv.DictReader(open("results/offtarget_per_sample.csv", encoding="utf-8-sig")))
gcg = {r["mutation"]: r for r in
       csv.DictReader(open("results/GCG_vs_off_ranking_WT.csv", encoding="utf-8-sig"))}

def pos_of(m):
    d = "".join(ch for ch in m if ch.isdigit())
    return int(d) if d else None

# ---------------------------------------------------------------- 单点
SINGLE = []
for r in singles:
    ret = float(r["retain"])
    if ret >= 0.15:
        continue
    c388 = float(r["GCG"]); dp = float(r["depth"]); p = pos_of(r["mut"])
    if c388 < 0.01:
        verdict, rec = "真失活（编辑信号 ≈ 0）", "★★ 首选"
    elif c388 < 0.03:
        verdict, rec = "真失活（仅 1–3 条读长）", "★ 可用"
    elif c388 < 0.08:
        verdict, rec = "近失活（背景水平）", "备选"
    else:
        verdict, rec = "近失活（10–15% 残余）", "不推荐作阴性对照"
    SINGLE.append(dict(mut=r["mut"], pos=p, role=ROLE.get(p, "—"),
                       retain=ret, c388=c388, dp=dp,
                       ratio=float(r["ratio"]), verdict=verdict, rec=rec))

# ---------------------------------------------------------------- 组合
combos = {}
for r in per:
    m = r["mutant"]
    if m.upper() in ("PUF12-9", "WT"):
        continue
    combos.setdefault(m, []).append(dict(rep=r["rep"], dp=float(r["med_dp"]),
                                         on=float(r["on_388"])))
COMBO = []
for m, reps in combos.items():
    act = float(gcg[m]["activity_retention"]) if m in gcg else None
    if act is None or act >= 0.15:
        continue
    good = [x for x in reps if x["dp"] >= 300]
    if not good:
        verdict, rec = "✗ 全部重复测序失败（深度 0），不可用", "排除"
    else:
        ok = [x for x in good if x["on"] == 0.0]
        if len(ok) >= 2:
            verdict, rec = f"真失活（{len(ok)}/{len(good)} 个可用重复为 0，深度充足）", "★★ 首选"
        elif len(ok) == 1:
            verdict, rec = f"真失活（1/{len(good)} 个可用重复为 0）", "★ 可用"
        else:
            verdict, rec = "近失活（残余为 1 条读长的检测限水平）", "备选"
    dp_txt = " / ".join(f"{x['dp']:.0f}" for x in reps)
    on_txt = " / ".join(f"{x['on']:.3f}" for x in reps)
    COMBO.append(dict(mut=m, act=act, on=on_txt, dp=dp_txt,
                      n_ok=len(good), verdict=verdict, rec=rec))

# ---------------------------------------------------------------- 建议新增
NEW = [
    ("E72A", "催化碱（general base）失活——APOBEC 领域标准阴性对照",
     "催化谷氨酸，位于活性口袋底部、面向溶剂，突变不破坏锌指与整体折叠，只废除催化",
     "保守性 >90%（不可动）；结构上靶 C 的 C4/N4 距 E72 仅 2.88 Å（WT GCG）"),
    ("E72Q", "同上，侧链长度保留但失去羧基负电（更温和的失活）",
     "与 E72A 配对使用，可区分「移除负电」与「移除整个侧链」两种失活机制",
     "同 E72A"),
    ("N57A", "移除催化必需氢键供体——比 N57W 更干净的失活对照",
     "已测的 N57W/M/R 都引入了大侧链，可能同时扰动折叠；N57A 只去掉酰胺基，体积最小",
     "保守性 0.67；与催化核心共进化 MI 最高（0.30）"),
    ("K30A（对照臂）", "最佳单点 K30H 的「非极性同义替换」对照",
     "用于证明 K30H 的效应来自组氨酸侧链本身，而非「改动 30 位」这一行为；"
     "若 K30A 也失活则说明该位点不容任何改动",
     "保守性 0.36（可动）；mCSM swap +2.89"),
]
NEW_NOTE = [
    ("H70A / C102A / C105A", "锌配位残基",
     "也能彻底失活，但它们同时破坏锌指折叠，蛋白可能不折叠/不表达——",
     "作为「催化失活但仍折叠」的对照不如 E72A 干净，仅在需要时使用"),
]

# ---------------------------------------------------------------- 控制台
print("=" * 108)
print("阴性对照候选 —— 单点（活性保留 < 0.15）")
print("=" * 108)
print(f"{'突变':<8}{'位点':>5}{'活性保留':>9}{'C388':>9}{'深度':>8}  {'判定':<28}{'推荐':<10}")
for r in sorted(SINGLE, key=lambda x: x["c388"]):
    print(f"{r['mut']:<8}{r['pos']:>5}{r['retain']:>9.3f}{r['c388']:>9.3f}{r['dp']:>8.0f}"
          f"  {r['verdict']:<28}{r['rec']:<10}")

print("\n" + "=" * 108)
print("阴性对照候选 —— 组合（activity_retention < 0.15）")
print("=" * 108)
print(f"{'组合':<18}{'活性保留':>9}{'C388(各重复)':>18}{'深度(各重复)':>18}  {'判定':<40}{'推荐'}")
for r in sorted(COMBO, key=lambda x: x["act"]):
    print(f"{r['mut']:<18}{r['act']:>9.3f}{r['on']:>18}{r['dp']:>18}  {r['verdict']:<40}{r['rec']}")

# ---------------------------------------------------------------- 输出
wb = Workbook()
thin = Side(style="thin", color="BBBBBB"); bd = Border(left=thin, right=thin, top=thin, bottom=thin)
def style(ws, widths, fills=None):
    for j in range(1, ws.max_column + 1):
        c = ws.cell(row=1, column=j)
        c.font = Font(bold=True, color="FFFFFF", size=10)
        c.fill = PatternFill("solid", fgColor=NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = bd
    for i in range(2, ws.max_row + 1):
        for j in range(1, ws.max_column + 1):
            c = ws.cell(row=i, column=j)
            c.font = Font(size=9); c.alignment = Alignment(vertical="top", wrap_text=True); c.border = bd
            if i % 2 == 0: c.fill = PatternFill("solid", fgColor=LIGHT)
    for col, w in zip("ABCDEFGH", widths):
        ws.column_dimensions[col].width = w
    if fills:
        for i, col in fills:
            ws.cell(row=i, column=col).fill = PatternFill("solid", fgColor=C_REC)

ws = wb.active; ws.title = "1_单点阴性对照"
ws.append(["突变", "位点", "位点角色", "活性保留率", "C388(G) 编辑率", "测序深度", "+1 偏好比", "判定与推荐"])
rl = []
for r in sorted(SINGLE, key=lambda x: x["c388"]):
    ws.append([r["mut"], r["pos"], r["role"], round(r["retain"], 3), round(r["c388"], 4),
               int(r["dp"]), round(r["ratio"], 2), f"{r['verdict']}　→　{r['rec']}"])
    rl.append(r["rec"])
style(ws, [9, 6, 42, 11, 14, 10, 10, 34],
      fills=[(i + 2, 8) for i, v in enumerate(rl) if v.startswith("★★")])

ws2 = wb.create_sheet("2_组合阴性对照")
ws2.append(["组合", "活性保留率", "C388 各重复", "测序深度 各重复", "可用重复数", "判定与推荐"])
for r in sorted(COMBO, key=lambda x: x["act"]):
    ws2.append([r["mut"], round(r["act"], 3), r["on"], r["dp"], r["n_ok"],
                f"{r['verdict']}　→　{r['rec']}"])
style(ws2, [18, 11, 18, 18, 11, 46],
      fills=[(i + 2, 6) for i, r in enumerate(sorted(COMBO, key=lambda x: x["act"]))
             if r["rec"].startswith("★★")])

ws3 = wb.create_sheet("3_建议新增的经典失活对照")
ws3.append(["突变", "失活机制", "为何是干净的阴性对照", "结构/进化依据"])
for n in NEW:
    ws3.append(list(n))
ws3.append([])
ws3.append(["—— 以下不推荐作为首选 ——", "", "", ""])
for n in NEW_NOTE:
    ws3.append(list(n))
style(ws3, [18, 46, 52, 46])

ws4 = wb.create_sheet("4_口径与排除说明")
for line in [
    ["判定三层口径", "", ""],
    ["① 活性保留率", "C388_sample / C388_parent；亲本单点批 0.5145、组合批 0.6768", ""],
    ["② 测序深度", "med_dp ≥ 300 才计入；本数据中 med_dp = 0 的样本为测序失败", ""],
    ["③ 检测限伪 0", "1 条变异读长 ≈ 0.077%（深度约 1300）。数据中反复出现的 0.051–0.096% "
                     "实为 1 条读长，按伪 0 处理，不能与真 0 等同", ""],
    ["", "", ""],
    ["被排除的样本", "原因", ""],
    ["30H-32F-132D (rep a)", "med_dp = 0，测序失败；rep b 深度 2701 且为 0，可用", ""],
    ["25-30 (rep a)", "med_dp = 0，测序失败；rep b 深度 1156 且为 0，可用", ""],
    ["27T-98A", "两个重复 med_dp 均为 0，全部失败；表中 activity=0 不可采信", ""],
    ["H70A / C102A / C105A", "可彻底失活，但破坏锌指折叠，非「折叠正常但催化死」的干净对照", ""],
    ["", "", ""],
    ["重要局限", "本实验的「活性」= C388 编辑率，同时受表达量、稳定性与催化活性影响。"
                 "阴性对照若要严格成立，建议补做 western blot 或体外纯化活性，"
                 "确认失活来自催化而非不表达", ""],
]:
    ws4.append(line)
style(ws4, [26, 62, 20])

wb.save("results/阴性对照候选表.xlsx")
print("\n写入 results/阴性对照候选表.xlsx")
