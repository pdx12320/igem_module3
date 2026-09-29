#!/bin/bash
# ============================================================
# 步骤0：下载 hg38 参考基因组 + GTF，并构建 STAR 索引（只需跑一次）
# 服务器工作路径：/data/ydx/zyx/
# 前置：已装 STAR、wget、gzip
# 注意：STAR 索引构建需约 30–40 GB 内存、约 1–2 小时（16 线程）
# ============================================================
set -e

BASE=/data/ydx/zyx
REF=$BASE/ref
IDX=$BASE/STAR_index_hg38
GENCODE_VER=47          # GENCODE 版本，如需更换改这里（如 46/45）

mkdir -p "$REF" "$IDX"

echo "== 1) 下载参考基因组 (GENCODE GRCh38 primary assembly) =="
wget -c -P "$REF" \
  "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_${GENCODE_VER}/GRCh38.primary_assembly.genome.fa.gz"

echo "== 2) 下载 GTF 注释 =="
wget -c -P "$REF" \
  "https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_${GENCODE_VER}/gencode.v${GENCODE_VER}.primary_assembly.annotation.gtf.gz"

echo "== 3) 解压参考基因组 fasta =="
gunzip -kf "$REF/GRCh38.primary_assembly.genome.fa.gz"

echo "== 4) 构建 STAR 索引 =="
STAR --runMode genomeGenerate \
     --genomeDir "$IDX" \
     --genomeFastaFiles "$REF/GRCh38.primary_assembly.genome.fa" \
     --sjdbGTFfile "$REF/gencode.v${GENCODE_VER}.primary_assembly.annotation.gtf.gz" \
     --sjdbOverhang 149 \
     --genomeSAindexNbases 14 \
     --runThreadN 16

echo "完成。"
echo "STAR 索引：$IDX"
echo "参考 fasta：$REF/GRCh38.primary_assembly.genome.fa"
echo "下一步运行：bash 01_download_align.sh"
