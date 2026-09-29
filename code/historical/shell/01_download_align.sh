#!/bin/bash
# ============================================================
# 步骤1：下载 CU-REWIRE5.1 (Pro.hA1) EGFP-GC 三个重复的 RNA-seq 并比对到 hg38
# 前置：已装 SRA Toolkit(prefetch/fasterq-dump)、STAR、samtools；已跑完 00_setup_reference.sh
# 服务器工作路径：/data/ydx/zyx/
# ============================================================
set -e

BASE=/data/ydx/zyx
STAR_INDEX=$BASE/STAR_index_hg38
REF_FA=$BASE/ref/GRCh38.primary_assembly.genome.fa

# 三个重复的 SRR（已由 SAMN 解析得到）
SRR=(SRR27885774 SRR27885775 SRR27885777)

mkdir -p "$BASE/fastq" "$BASE/bam"

# ---- 1) 下载 ----
for s in "${SRR[@]}"; do
  echo "下载 $s ..."
  prefetch "$s" -O "$BASE/fastq/"
  fasterq-dump --split-3 -O "$BASE/fastq/" "$BASE/fastq/$s/$s.sra"
  rm -rf "$BASE/fastq/$s"   # 删除中间 .sra，节省空间
done

# ---- 2) 比对到 hg38 ----
for s in "${SRR[@]}"; do
  echo "比对 $s ..."
  STAR --genomeDir "$STAR_INDEX" \
       --readFilesIn "$BASE/fastq/${s}_1.fastq" "$BASE/fastq/${s}_2.fastq" \
       --outSAMtype BAM SortedByCoordinate \
       --outFileNamePrefix "$BASE/bam/${s}_" \
       --outSAMunmapped Within --outSAMattributes NH HI AS NM MD \
       --runThreadN 16 --limitBAMsortRAM 30000000000
  samtools index "$BASE/bam/${s}_Aligned.sortedByCoord.out.bam"
done

echo "完成。BAM 文件："
ls "$BASE"/bam/*.bam
echo "下一步运行："
echo "python 02_find_CU_offtarget.py --bam $BASE/bam/SRR27885774_Aligned.sortedByCoord.out.bam $BASE/bam/SRR27885775_Aligned.sortedByCoord.out.bam $BASE/bam/SRR27885777_Aligned.sortedByCoord.out.bam --ref $REF_FA --min-depth 10 --min-rep 2 --top 30"
