# -*- coding: utf-8 -*-
"""
步骤2：从三个重复的 BAM 中找 C→U（C→T）编辑事件，排序找出「脱靶编辑最强」的位点及其 motif。

原理：C→U 编辑在 RNA-seq 反转录后表现为相对参考基因组的 C→T 错配。
对每个参考 C 位点统计 T/(C+T) 即编辑率；跨 3 个重复取平均；按编辑率降序输出前 N 个，
并给出 ±context 的 motif。

用法：
  python 02_find_CU_offtarget.py --bam bam/SRR27885774_...bam bam/SRR27885775_...bam bam/SRR27885777_...bam \
                                 --ref /path/to/hg38.fa \
                                 --min-depth 10 --min-rep 2 --top 20
依赖：pysam
"""
import argparse
import sys
from collections import defaultdict

import pysam


def detect(bam_path, ref_fa, min_depth):
    bam = pysam.AlignmentFile(bam_path, "rb")
    ref = pysam.FastaFile(ref_fa)
    events = {}  # (contig, pos1based) -> (rate, c_count, t_count, depth)
    for contig in bam.references:
        seq = ref.fetch(contig).upper()
        for pos0 in range(len(seq)):
            if seq[pos0] != "C":
                continue
            c_cnt = t_cnt = 0
            for col in bam.pileup(contig, pos0, pos0 + 1, truncate=True,
                                  min_base_quality=20):
                for rd in col.pileups:
                    if rd.is_del or rd.is_refskip:
                        continue
                    b = rd.alignment.query_sequence[rd.query_position].upper()
                    if b == "C":
                        c_cnt += 1
                    elif b == "T":
                        t_cnt += 1
            tot = c_cnt + t_cnt
            if tot < min_depth:
                continue
            rate = t_cnt / tot
            events[(contig, pos0 + 1)] = (rate, c_cnt, t_cnt, tot)
    bam.close()
    return events


def context(ref_fa, contig, pos1, half=5):
    ref = pysam.FastaFile(ref_fa)
    start = max(0, pos1 - 1 - half)
    seq = ref.fetch(contig, start, pos1 + half).upper()
    rel = pos1 - 1 - start  # 目标 C 在 seq 中的位置
    return seq, rel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bam", nargs="+", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--min-depth", type=int, default=10)
    ap.add_argument("--min-rep", type=int, default=2, help="至少几个重复检出")
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()

    all_events = defaultdict(list)
    for bam in args.bam:
        ev = detect(bam, args.ref, args.min_depth)
        for k, v in ev.items():
            all_events[k].append(v)

    # 合并：要求至少 min_rep 个重复检出，取平均编辑率
    merged = {}
    for k, vs in all_events.items():
        if len(vs) < args.min_rep:
            continue
        rate = sum(v[0] for v in vs) / len(vs)
        depth = sum(v[3] for v in vs)
        merged[k] = (rate, len(vs), depth)

    ranked = sorted(merged.items(), key=lambda x: -x[1][0])

    print(f"共检出 {len(merged)} 个 C→T 位点（≥{args.min_rep} 重复、深度≥{args.min_depth}）")
    print(f"\n== 脱靶编辑最强的 Top {args.top} 位点 ==")
    print(f"{'chr':<8} {'pos':>10} {'编辑率':>8} {'重复数':>6} {'深度':>8}  上下文(±5, C 为目标)")
    for (contig, pos1), (rate, nrep, depth) in ranked[:args.top]:
        seq, rel = context(args.ref, contig, pos1)
        left = seq[max(0, rel - 5):rel]
        right = seq[rel + 1:rel + 6]
        motif = f"{left}[C]{right}"
        print(f"{contig:<8} {pos1:>10} {rate*100:>7.1f}% {nrep:>6} {depth:>8}  {motif}")

    # 保存完整结果
    out = "CU_offtarget_all.txt"
    with open(out, "w") as f:
        f.write("chrom\tpos\tedit_rate\tn_rep\tdepth\tmotif\n")
        for (contig, pos1), (rate, nrep, depth) in ranked:
            seq, rel = context(args.ref, contig, pos1)
            motif = f"{seq[max(0,rel-5):rel]}[C]{seq[rel+1:rel+6]}"
            f.write(f"{contig}\t{pos1}\t{rate:.4f}\t{nrep}\t{depth}\t{motif}\n")
    print(f"\n完整结果已保存到 {out}")


if __name__ == "__main__":
    main()
