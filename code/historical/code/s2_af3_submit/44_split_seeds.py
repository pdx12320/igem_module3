# -*- coding: utf-8 -*-
"""
阶段 44 —— 把多 seed 的 AF3 提交文件拆成「一个 JSON 一个 seed」

背景：AF3 server 每个 JSON 只接受一个 seed，故 39 / 42 生成的
      protein_only（6 文件 × 10 seed）与 negctrl（12 文件 × 5 seed）必须拆开。

做法：
  · 每个 seed 输出一个独立 JSON，文件名与 job name 均带 seed 号（便于下载后区分目录）；
  · 原始多 seed 文件移入 <目录>/_原始多seed/（保留，不删除）；
  · 已是单 seed 的文件原样跳过（可重复运行）；
  · 每个目录另出 _提交清单.csv，含构建体 / RNA / seed 数 / 优先级，便于逐条勾选上传。

用法：uv run python 44_split_seeds.py
"""
import json, glob, os, re, sys, shutil, csv
sys.stdout.reconfigure(encoding="utf-8")

FOLDERS = ["af3_submit_negctrl"]   # 纯蛋白线已取消
ARCHIVE = "_原始多seed"

# 面板说明（用于清单）
NOTE = {
    "WT_pure": ("WT（纯蛋白，无 RNA）", "P0"),
    "M132D_pure": ("M132D（纯蛋白）", "P0"),
    "M132E_pure": ("M132E（纯蛋白）", "P0"),
    "K30H_pure": ("K30H（纯蛋白）", "P0"),
    "G27TK30HQ58M_pure": ("G27T-K30H-Q58M（纯蛋白）", "P0"),
    "T31D": ("T31D 完全失活（活性 0.000）", "P0"),
    "N57W": ("N57W 完全失活（活性 0.000）", "P0"),
    "G27DM130G": ("G27D-M130G 完全失活组合（活性 0.000）", "P0"),
    "T31A": ("★ T31A 同位点活性对照（活性 0.970）", "P0"),
    "N57A": ("N57A 新失活对照（未测）", "P1"),
    "E72A": ("E72A 新失活对照（未测）", "P1"),
}


def base_of(fname):
    """WT_pure_seed01-10.json -> WT_pure ; T31D_GCG.json -> T31D_GCG"""
    b = os.path.splitext(os.path.basename(fname))[0]
    return re.split(r"_seed\d", b)[0].rstrip("_-")


total_files = 0
manifest = []
for folder in FOLDERS:
    if not os.path.isdir(folder):
        print(f"跳过（不存在）：{folder}")
        continue
    files = sorted(glob.glob(os.path.join(folder, "*.json")))
    multi, single = [], []
    for f in files:
        try:
            n = len(json.load(open(f, encoding="utf-8"))[0].get("modelSeeds", []))
        except Exception:
            continue
        (multi if n > 1 else single).append((f, n))

    print(f"\n{'='*90}\n{folder}\n{'='*90}")
    print(f"  单 seed（原样保留）: {len(single)} 个")
    print(f"  多 seed（待拆分）  : {len(multi)} 个")

    if multi:
        arch = os.path.join(folder, ARCHIVE)
        os.makedirs(arch, exist_ok=True)
        for f, n in multi:
            job = json.load(open(f, encoding="utf-8"))[0]
            seeds = job["modelSeeds"]
            base = base_of(f)
            for s in seeds:
                new = dict(job)
                new["modelSeeds"] = [str(s)]
                new["name"] = f"{base}_s{int(s):02d}"
                out = os.path.join(folder, f"{base}_s{int(s):02d}.json")
                with open(out, "w", encoding="utf-8") as fh:
                    json.dump([new], fh, indent=1, ensure_ascii=False)
            shutil.move(f, os.path.join(arch, os.path.basename(f)))
            lo, hi = min(int(x) for x in seeds), max(int(x) for x in seeds)
            print(f"    {os.path.basename(f):<42} {n} seed -> 拆为 {n} 个文件（{base}_s{lo:02d}..s{hi:02d}）")

    # 清单
    for f in sorted(glob.glob(os.path.join(folder, "*.json"))):
        j = json.load(open(f, encoding="utf-8"))[0]
        nm = os.path.splitext(os.path.basename(f))[0]
        stem = re.sub(r"_s\d+$", "", nm)
        stem_key = re.sub(r"_(GCG|GCA)$", "", stem)
        construct, pri = NOTE.get(stem_key, (stem, "—"))
        rna = "无 RNA" if len(j["sequences"]) < 2 else j["sequences"][1]["rnaSequence"]["sequence"]
        manifest.append([folder, os.path.basename(f), j["name"], construct, rna,
                         len(j["modelSeeds"]), pri])
        total_files += 1

with open("提交清单_AF3.csv", "w", newline="", encoding="utf-8-sig") as fh:
    w = csv.writer(fh)
    w.writerow(["目录", "文件名", "job name", "构建体", "RNA", "seed 数", "优先级"])
    for row in sorted(manifest, key=lambda r: (r[0], r[6], r[1])):
        w.writerow(row)

print(f"\n{'='*90}")
print(f"拆分完成：共 {total_files} 个待提交文件（每个仅 1 个 seed）")
print(f"清单已写入 提交清单_AF3.csv")
print(f"原始多 seed 文件保留在各目录的 {ARCHIVE}/ 下")
