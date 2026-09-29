# -*- coding: utf-8 -*-
"""
56_make_dbtl.py —— 把 APOBEC 编辑模块的全部实验整理为 iGEM 的 DBTL 循环

输出到 文案数据图表整理/：
  APOBEC_DBTL_迭代整理.docx   双语 + 中英对照（与队友《Wiki PUF（简介、工程）》同格式）
  APOBEC_DBTL_迭代整理.md     同内容的 Markdown（直接贴 wiki 用）
  APOBEC_DBTL_数据支撑表.xlsx 每个 cycle 的关键数据（wiki 表格可直接引用）

用法：uv run --with python-docx --with openpyxl python 56_make_dbtl.py
"""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUTDIR = "文案数据图表整理"
DOCX = os.path.join(OUTDIR, "APOBEC_DBTL_迭代整理.docx")
MD = os.path.join(OUTDIR, "APOBEC_DBTL_迭代整理.md")
XLSX = os.path.join(OUTDIR, "APOBEC_DBTL_数据支撑表.xlsx")
import time as _t
for _n in ("DOCX", "XLSX"):
    _p = globals()[_n]
    try:
        with open(_p, "r+b"):
            pass
    except (PermissionError, FileNotFoundError):
        if os.path.exists(_p):
            _b, _e = os.path.splitext(_p)
            globals()[_n] = f"{_b}_{_t.strftime('%m%d_%H%M')}{_e}"
FIGDIRS = [os.path.join("文案数据图表整理", "scientific-figures"),
           os.path.join("文案数据图表整理", "图表"), os.path.join("results", "figs")]
os.makedirs(OUTDIR, exist_ok=True)

CN = "微软雅黑"
NAVY, BLUE, ACC, GREEN, GRAY = (0x1F, 0x3B, 0x66), (0x2E, 0x54, 0x8B), \
    (0xB4, 0x4A, 0x3C), (0x1E, 0x7A, 0x46), (0x40, 0x40, 0x40)

# ===========================================================================
# 正文内容（中英双语，与 PUF 文档同结构）
# ===========================================================================
INTRO_ZH = (
    "Orca 系统的编辑模块采用 APOBEC 家族脱氨酶（底盘为 Pro.hA1，199 aa），负责将靶点 C 脱氨为 U。"
    "在 APOE4 的编辑中，我们面对一个关键的特异性问题：靶点 c.388（GCG）与最严重的脱靶位点 c.871（GCA）"
    "共享 −1 位 G，唯一的核心差异在 +1 位（G vs A）。因此编辑模块的工程目标是「保 G 排 A」——"
    "在保留 on-target 活性的前提下，让酶优先编辑 +1=G 的 GCG 而非 +1=A 的 GCA。"
    "需要说明的是，我们优化的并不是单个位点，而是这个酶对 ±1 位基序的整体偏好。"
    "逐位点扫描整段 APOE 扩增子（951 bp、291 个 C 位点）共检出 74 个脱靶热点，"
    "其中 −1 位是 G 的占 68 个；按 +1 位细分则是 GCG 30、GCA 16、GCC 12、GCT 10——"
    "GCA 是 GCG 之外最大的一类脱靶。优先针对 GCA 除了因为它的普遍性，还因为 +1 位决定了脱靶编辑的后果："
    "以 CA 开头的密码子编辑后变成 TA 开头，其中 TAA 与 TAG 是终止子（下游 4 种碱基里有 2 种会如此）；"
    "以 CG 开头的只有 TGA 是终止子（4 种里有 1 种）；以 CT、CC 开头的则不会读出终止子"
    "（这一条依标准遗传密码推出，本项目并未直接测量终止子的获得）。"
    "这也是与靶向模块的分工：PUF 模块关心「哪一位」（388 还是 871），"
    "编辑模块关心「哪一类基序」（GCG 还是 GCA/GCN），两边的改进作用层次不同、彼此互补。"
    "设计思路来自 Wu、Xiao 与 Tang 在 Nature Biotechnology 的工作（2026;44(4):587–601）："
    "他们对脱氨酶的核酸识别热点做定向进化，得到 16 个覆盖全部 −1/+1 组合的 NCN 特异变体，"
    "其核心论点是「同时识别 −1 与 +1 位，才足以把编辑限定到单个 C」。"
    "围绕这一目标，我们对 APOBEC 编辑模块完成了六个完整的 DBTL 循环，"
    "每一次都由设计、构建、测试、学习四步闭环。"
    "五个循环贯穿的同一条主线是：这个酶究竟靠什么认出它的底物，而这种识别里有多少是可以被改造的——"
    "每一轮都由干实验提出可证伪的机制预言、湿实验给出验证并回补干实验，两者一致处成为下一轮的地基，"
    "不一致处则修正我们对这个酶的理解。"
)
INTRO_EN = (
    "The editing module of the Orca system employs an APOBEC-family deaminase (scaffold: Pro.hA1, 199 aa) "
    "that deaminates the target C to U. In APOE4 editing we face a key specificity problem: the on-target "
    "site c.388 (GCG) and the most severe off-target site c.871 (GCA) share the −1 position G, and their only "
    "core difference lies at the +1 position (G vs A). The engineering goal of the editing module is therefore "
    "\"keep G, reject A\" — to make the enzyme preferentially edit +1=G (GCG) over +1=A (GCA) while retaining "
    "on-target activity. Note that what we are optimising is not a single site but the enzyme's overall "
    "preference over the ±1 motif. Scanning every position of the whole APOE amplicon (951 bp, 291 C sites) "
    "detected 74 off-target hotspots, of which 68 have G at the −1 position; broken down by +1 they are GCG 30, "
    "GCA 16, GCC 12 and GCT 10 — GCA is the largest off-target class after GCG. GCA was prioritised not only "
    "for its prevalence but because the +1 position sets the consequence of an off-target edit: a codon "
    "beginning CA becomes TA after editing, and two of the four possible downstream bases then read as stops "
    "(TAA, TAG); one beginning CG becomes TG, where only TGA is a stop (one of four); one beginning CT or CC "
    "yields no stop codon at all (this follows from the standard genetic code; stop-codon gain was not measured "
    "directly in this project). This is also the division of labour with the targeting module: the PUF module "
    "cares about which position (388 or 871), the editing module about which motif (GCG or GCA/GCN) — "
    "improvements at different levels that complement each other. The design idea came from work by Wu, Xiao "
    "and Tang in Nature Biotechnology (2026;44(4):587–601), who evolved the nucleic-acid-recognition hotspots "
    "of a deaminase to obtain 16 NCN-specific variants covering every −1/+1 context, on the argument that "
    "recognising both the −1 and +1 positions is what confines editing to a single C. Toward this goal we have "
    "completed six full DBTL cycles on the APOBEC editing module, each closing the loop of design, build, "
    "test and learn. One "
    "thread runs through all five: what does this enzyme actually recognise in its substrate, and how much of "
    "that recognition can be engineered? Each round has the dry work state a falsifiable mechanistic prediction "
    "and the wet work test it and feed the result back to the dry work — agreement becomes the foundation of "
    "the next round, disagreement corrects our understanding of the enzyme."
)

CYCLES = [
    dict(
        num=1,
        title_zh="迭代 1：+1 位有没有可被改造的读取元件——单点饱和",
        title_en="Iteration 1: Is there a modifiable reader at the +1 position? — single-site saturation",
        overview_zh=(
            "问题：在这个界面上，究竟有没有一个残基在「读取」+1 位碱基，而不只是贴近它？"
            "做法：用三组只差一个碱基的 RNA 底物建模，把每个残基与 +1 位碱基的接触拆成侧链/主链 × 碱基/糖磷酸，"
            "据此设计并测试 102 个单点突变体。"
            "结果：在我们这套建模中，K30 是唯一用侧链读 +1 的残基，改造它得到 1.71（保留 84%），"
            "也是 102 个里为数不多的有效单点；在保留活性者中没有任何单点达到 2.0。"
            "结论不是「位点没选对」，而是这一层根本没有可改造的读取元件——单点路线由此关闭。"
        ),
        overview_en=(
            "Question: is there any residue at this interface that actually reads the +1 base, rather than "
            "merely sitting near it? What we did: modelled three RNA substrates differing by a single base and "
            "decomposed each residue's contact with the +1 base into sidechain/mainchain × base/sugar-phosphate, "
            "then designed and tested 102 single mutants on that basis. Result: in our modelling, K30 is the "
            "only residue that reads +1 through its sidechain, and engineering it gave 1.71 (84% retention) — "
            "one of the few effective substitutions among the 102; no mutant that retained activity reached 2.0. The conclusion is not "
            "that we picked the wrong positions, but that this layer has no modifiable reader at all, which "
            "closed the single-mutation route."
        ),
        design_zh=(
            "我们首先把问题限定成一个可证伪的生物学问题：在这个界面上，究竟有没有残基在「读取」+1 位碱基，"
            "而不只是贴近它？一个残基完全可能因为主链走向而紧贴 +1 位，却对它是 G 还是 A 毫无分辨能力——"
            "改造这样的残基只会改变底物被酶结合的松紧，不会产生选择性。"
            "为把「+1 位效应」与「侧翼序列效应」解耦，我们设计了三个 AlphaFold3 复合物模型："
            "GUGCGCG（靶点）、GUGCACG（仅 +1 位换成 A）、AUGCAGC（完整脱靶序列）。"
            "在此基础上做接触类型分解（侧链/主链 × 碱基/糖磷酸）：以侧链–碱基接触作为「真正在读碱基」的判据，"
            "结构性接触的残基则以主链为主。这份分解在动手前就划掉了几个候选——最典型的是 Q58，"
            "它在两种底物中与 +1 位碱基的侧链接触频率都是 0.00，不可能是在读 +1。"
            "最后用 3504 条同源序列的保守性与 PSSM 突变方向分析判断哪些位点可动、能朝哪些氨基酸变，"
            "据此设计第一批单点突变引物。"
        ),
        design_en=(
            "We first reduced the problem to a falsifiable biological question: is there any residue at this "
            "interface that actually reads the +1 base, rather than merely sitting near it? A residue can sit "
            "right against the +1 base because of its mainchain geometry while being unable to tell G from A at "
            "all — engineering it would only change how tightly the enzyme binds the substrate, not produce selectivity. "
            "To decouple the \"+1 effect\" from the \"flanking-sequence effect\", we designed three AlphaFold3 "
            "complex models: GUGCGCG (on-target), GUGCACG (+1 swapped only), and AUGCAGC (full off-target "
            "sequence). On these we performed contact-type decomposition (sidechain/mainchain × base/"
            "sugar-phosphate): we took sidechain–base contact as the criterion for a residue genuinely reading "
            "the base, whereas a structural contact runs mainly through the mainchain. That decomposition "
            "removed several candidates before any "
            "experiment — most clearly Q58, whose sidechain–base contact frequency with the +1 base is 0.00 in "
            "both substrates, so it cannot be reading +1. Finally, conservation and PSSM analyses over 3,504 "
            "homologous sequences were used to decide which positions are mutable and toward which amino acids, "
            "and the first batch of single-mutation primers was designed from that."
        ),
        build_zh=(
            "候选表分三步筛出。"
            "① 位点范围由结构分析划定（阅读器区 29–31、loop1 25–28、loop3 57–60、WS 环 98、loop7 出口 129–133），"
            "再用 3504 条同源序列的保守性剔除催化活性相关的禁区：H70（0.97）、E72（0.95）、C102（1.00）、C105（1.00）"
            "为锌配位/质子供体，W99（0.74）为保守 Trp；N57（0.67）虽非绝对保守，"
            "但与催化核心的共进化 MI 为全蛋白最高（0.30），不做单独突变。"
            "② 替换方向由 PSSM 决定（家族频率 ≥1% 为允许方向，<1% 为禁止方向），"
            "每位点挑 1–4 个有生化依据的替换而非做 20 AA 饱和 → 16 个位点、102 个替换，"
            "各位点的替换数从 1 个（A59）到 16 个（I26）不等。"
            "③ 侧链对 +1 位贡献仅 5%（94% 走主链）的 H29 被降级为机制探针，未构建任何单点，"
            "仅出现在组合 29N-98A 中。"
            "按与 PUF 模块相同的方法构建：PCR 获取线性化载体，同源重组自环化引入点突变，"
            "得到 102 个单点突变体，每个做 2 次独立转染（含亲本共 205 个样本行）。"
        ),
        build_en=(
            "The candidate table was filtered in three steps. (i) The site range came from the structural "
            "analysis (reader region 29–31, loop1 25–28, loop3 57–60, WS ring 98, loop7 exit 129–133), after "
            "which conservation across 3,504 homologues removed the positions critical for catalytic activity: H70 (0.97), "
            "E72 (0.95), C102 (1.00) and C105 (1.00) are the zinc-coordinating/proton-donating residues and "
            "W99 (0.74) a conserved tryptophan; N57 (0.67) is less absolutely conserved but has the highest "
            "coevolutionary MI with the catalytic core in the protein (0.30) and was excluded from single "
            "substitution. (ii) The direction of each substitution came from a PSSM (family frequency ≥1% = "
            "allowed, <1% = disallowed), choosing 1–4 justified substitutions per site rather than a 20-AA "
            "saturation — giving 16 sites and 102 substitutions, from 1 substitution (A59) to 16 (I26). "
            "(iii) H29, whose sidechain contributes only 5% of the contact with +1 (94% runs through the "
            "mainchain), was demoted to a mechanistic probe and has no single mutant at all; it appears only "
            "inside the combination 29N-98A. Building followed the same method as the PUF module: PCR for a "
            "linearised vector, then homologous recombination to self-circularise with the point mutation, "
            "giving 102 single mutants each transfected in two independent replicates (205 sample rows "
            "including the parent)."
        ),
        test_zh=(
            "将各突变体转染至表达 APOE4 的细胞中，通过扩增子深度测序（APOE 951 bp，291 个 C 位点）"
            "读取 c.388（GCG）、c.871（GCA）、c.295（ACA）三个位点的编辑效率，计算 +1 比（GCG/GCA）与活性保留率。"
            "同时逐突变核对 PSSM 排除规则：102 个突变体中判对 53 个、判错 49 个（准确率 0.52），"
            "「判为禁止方向 → 失活」的精确率仅 0.38（38 个被判禁止的替换仍然保留活性）。"
        ),
        test_en=(
            "Each mutant was transfected into APOE4-expressing cells, and amplicon deep sequencing "
            "(APOE 951 bp, 291 C sites) was used to read editing efficiency at c.388 (GCG), c.871 (GCA) and "
            "c.295 (ACA), from which the +1 ratio (GCG/GCA) and activity retention were calculated. The PSSM "
            "exclusion rule was checked substitution by substitution: 53 of 102 called correctly and 49 "
            "incorrectly (accuracy 0.52), with a precision of only 0.38 for \"disallowed direction implies "
            "inactive\" — 38 substitutions the rule called disallowed retained activity."
        ),
        learn_zh=(
            "102 个单点突变体中 40 个保留活性。原始比值超过 2.0 的有 3 个（130G 3.00、60Q 2.55、31G 2.22），但保留率分别只有 0.32、0.17、0.13；在保留率 ≥70% 的突变体中，+1 比最高的是 K30H 的 1.71，也就是说 2.0 这条线并没有在可接受的活性代价下被跨过。"
            "湿实验对干实验的回补验证分成正反两部分结论。"
            "成立的部分：K30 是唯一用侧链读 +1 的残基，而且读 G 强于读 A（侧链–碱基接触频率 0.81 vs 0.64），"
            "改造它确实产生了效果，也是全部 102 个单点中为数不多的有效改造。"
            "被证伪的一半：「结构接触 = 功能驱动力」被直接证伪——T31 在 A 型复合物中侧链–碱基接触频率为 1.00、"
            "G 型中为 0.00，但切除它的 T31A 实测三个位点读数（GCG 0.501 / GCA 0.379 / ACA 0.239）"
            "与亲本（0.514 / 0.375 / 0.294）几乎重合，+1 比 1.32 甚至略低于亲本的 1.37。"
            "生物学结论：+1 位在野生型中可能不存在 GCG 特异的侧链读取元件——接触最强的 H29 有 94% 的接触走主链，"
            "作用是把碱基按在位点上而不是分辨它，且H29的单点突变对选择性的结果并不理想。"
            "这并不意外：APOBEC 家族的底物偏好由 −1 位决定，"
            "+1 位是被容忍而非被读取的。因此单点路线关闭，特异性必须转向「作用于不同识别层的多位点组合」。"
            "\n\n"
            "此后补测的一批数据对上述结论做了回补验证。位点 29 的替换此前完全未测，本次补齐了 18 个；"
            "按测序深度过滤（DP < 500 时该位点的编辑效率不可信）后，只有 29N（+1 比 1.59、保留 0.75）、"
            "29R（1.45、0.68）、29S（1.36、0.63）、29A（1.20、0.51）四者同时达到活性下限，"
            "其 ROF 分别为 1.21、1.10、1.03、0.91，均未超过 K30H；原始比值最高的 29Y（1.71）"
            "其 on-target 仅剩亲本的 34%，属于低活性导致的比值虚高。位点 29 的饱和扫描因此没有给出"
            "比 K30 更好的读取器。需要一并记录的是，同批中 K30H 的 +1 比为 1.35（ROF 1.02），"
            "与既有单点批的 1.71（ROF 1.25）不一致——这一差异提示单点天花板的数值宜按批次重新确认，"
            "而不宜当作一个固定常数。"
        ),
        learn_en=(
            "Of the 102 single mutants, 40 retained activity. Three exceeded the 2.0 target in raw ratio "
            "(130G 3.00, 60Q 2.55, 31G 2.22) but retained only 0.32, 0.17 and 0.13 respectively; among mutants "
            "retaining at least 70% activity the highest ratio was 1.71 (K30H). The 2.0 line was therefore not "
            "crossed at an acceptable activity cost. "
            "The feedback from the wet lab back to the dry prediction "
            "falls into two parts, positive and negative. "
            "What held: K30 is the only residue that reads +1 through its sidechain, and it reads G better than A "
            "(sidechain–base contact frequency 0.81 vs 0.64), so engineering it did work — one of the few "
            "effective substitutions among the 102. What failed: \"structural contact = functional driving force\" "
            "was directly refuted — T31 shows a sidechain–base contact frequency of 1.00 in the A-type complex and "
            "0.00 in the G-type, yet removing it (T31A) left the three read-outs (GCG 0.501 / GCA 0.379 / ACA "
            "0.239) almost superimposed on the parent (0.514 / 0.375 / 0.294), with a +1 ratio of 1.32, slightly "
            "below the parent's 1.37. Biological conclusion: the wild type may contain no GCG-specific sidechain "
            "reader at +1 — H29, the most contacting residue, makes 94% of its contact through the mainchain, "
            "holding the base in place rather than identifying it, and single substitutions at H29 did not give "
            "a satisfactory result for selectivity. This is unsurprising: APOBEC substrate "
            "preference is set by −1, and +1 is tolerated rather than read. The single-mutation route is therefore "
            "closed, and specificity has to come from combinations acting on different recognition layers."
            "\n\n"
            "A later sequencing batch provided a check on this conclusion. The substitutions at position 29 had "
            "not been tested at all; eighteen are now available. Filtering by sequencing depth (below 500 reads "
            "the editing estimate at that position is not reliable), only four of them — 29N (+1 ratio 1.59, "
            "retention 0.75), 29R (1.45, 0.68), 29S (1.36, 0.63) and 29A (1.20, 0.51) — also reach the activity "
            "floor, with ROF values of 1.21, 1.10, 1.03 and 0.91, none of which exceeds K30H. The highest raw "
            "ratio, 29Y (1.71), retains only 34% of the parent's on-target activity, i.e. its ratio is inflated "
            "by low activity. The position-29 saturation therefore did not yield a better reader than K30. One "
            "further observation belongs in the record: in the same batch K30H measures 1.35 (ROF 1.02) against "
            "1.71 (ROF 1.25) in the earlier single-mutant batch, which suggests the single-point ceiling should "
            "be re-confirmed per batch rather than treated as a fixed number."
        ),
        figs=[("wiki_fig2_Cycle1_单点天花板.png", "图 1-1　单点突变全景：+1 比 vs 活性保留", "Fig. 1-1  Landscape of single mutants: +1 ratio vs activity retention")],
        data=[
            ["单点突变体数", "102（+ 亲本 PUF12-9）"],
            ["样本数 / 重复", "205 / n=2"],
            ["保留活性者", "40 / 102"],
            ["+1 比天花板（保留活性者）", "1.71（K30H，保留 84%）；原始比值最高为 130G 3.00，但保留仅 0.32"],
            ["原始比值 ≥2.0 者", "3（130G 3.00 / 60Q 2.55 / 31G 2.22，保留率 0.32 / 0.17 / 0.13）"],
            ["亲本基线", "GCG 0.5145 / GCA 0.3754 / +1 比 1.371"],
            ["K30 读取方向", "侧链–碱基接触频率 0.81（+1=G）vs 0.64（+1=A）→ 目前识别到的保 G 读取器"],
            ["位点 29 饱和扫描（后补）", "18 个替换；DP ≥500 过滤后仅 29N/29R/29S/29A 达活性下限（ROF 1.21/1.10/1.03/0.91），均未超过 K30H"],
            ["跨批一致性", "K30H：后补批 1.35（ROF 1.02）vs 既有单点批 1.71（ROF 1.25），宜按批次复核"],
            ["被证伪的假说", "T31 = 排 A 靶点（T31A 实测 +1 比 1.32、GCG 0.501 / GCA 0.379 / ACA 0.239，与亲本几乎重合）"],
        ],
    ),
    dict(
        num=2,
        title_zh="迭代 2：跨识别层组合——−1 位锚点与 +1 位读取器",
        title_en="Iteration 2: Cross-layer combinations — the −1 anchor and the +1 reader",
        overview_zh=(
            "问题：既然 +1 层没有读取器，特异性能否由作用于其他识别层的位点补上？"
            "做法：回到单点数据，发现虽然靶点不同，对−1 层的改造的效果远比对+1 层改造的效果好"
            "（G27D 把 ACA 类底物压低 36 倍、同时保留 88% 活性），"
            "据此按「跨层」原则设计组合，构建并测试 50 个双点与三点构建体。"
            "结果：27T-30H-58M 达到 +1 比 2.16、保留 77%，是全批唯一同时越过 2.0 且保留接近 70% 线的组合，"
            "其三个成分恰好分别作用于 −1 层、+1 层与活性补偿。"
            "但比值与活性的取舍并未消失，而 M132D 暴露出远端残基的长程耦合——这个结构域可能不是模块化的。"
        ),
        overview_en=(
            "Question: if the +1 layer has no reader, can specificity be supplied by positions acting on other "
            "recognition layers? What we did: went back to the single-mutation data and found that, although the "
            "target sites differ, engineering the −1 layer is considerably more effective than engineering the "
            "+1 layer (G27D suppresses ACA-class substrate 36-fold while "
            "retaining 88% activity), then designed cross-layer combinations on that basis and built and tested "
            "50 double and triple constructs. Result: 27T-30H-58M reached a +1 ratio of 2.16 at 77% retention — "
            "the only construct in the batch to clear 2.0 while staying near the 70% line, with its three "
            "components acting on the −1 layer, the +1 layer and activity compensation respectively. But the "
            "ratio–activity trade-off did not disappear, and M132D exposed long-range coupling from a distal "
            "residue: this domain may not be modular."
        ),
        design_zh=(
            "既然单点上限为 1.71（距目标 2.0 仅差 0.29），我们假设把机制不同的位点叠加可以突破这一上限。"
            "但在设计组合之前，我们回头重看了一遍单点数据，发现了一条比 1.71 本身更值得注意的线索："
            "G27D 把 ACA 类底物（c.295）的编辑率压到亲本的 1/36（0.008，亲本 0.294），同时保留 88% 活性、"
            "GCG 几乎不受影响（0.451，亲本 0.514）；G27T 类似（ACA 0.042，保留 98%）。"
            "27 位是 loop1 上的 −1 位主锚残基，也就是说，它作用的是这个酶真正进化出来读的那个位置。"
            "由此形成一个与迭代 1 互补的假设：+1 层的改造上限很低（那一层没有承重结构），"
            "而 −1 层被进化打磨过，改动它可能以很低的活性代价换取显著的选择性——"
            "组合的意义不只是「把效应加起来」，而是同时作用于两个识别层。"
            "组合遵循三条规则：① 至少含一个能提升 +1 比的突变；② 优先跨区域组合，避免同区域冗余；"
            "③ 含高活性代价突变（如 K60Q、W130G）的组合只作机制探针，不作候选。"
            "骨架取自迭代 1 中已证实的锚点：K30H（目前唯一的 +1 层读取器改造）、G27D/T（−1 层）、"
            "Q58M（活性代价最低者之一，真实作用待定）、M132D/E（出口通道，距 +1 位 15–20 Å、接触频率 0，"
            "作为显式的远端对照）。"
        ),
        design_en=(
            "Since the single-site ceiling was 1.71 — only 0.29 short of the 2.0 target — we hypothesized that "
            "stacking positions with different mechanisms could break it. Before designing combinations, though, "
            "we re-read the single-mutation data and found a line more interesting than the 1.71 itself: G27D "
            "suppressed ACA-class substrate (c.295) to 1/36 of the parent (0.008 vs 0.294) while retaining 88% "
            "activity and leaving GCG almost untouched (0.451 vs 0.514); G27T behaved similarly (ACA 0.042, "
            "retention 0.98). Position 27 is the primary −1 anchor in loop1 — it acts on the position this enzyme "
            "actually evolved to read. That suggested a hypothesis complementary to Iteration 1: the +1 layer has "
            "a low ceiling because it carries no load-bearing structure, whereas the −1 layer has been shaped by "
            "evolution and may buy substantial selectivity at little activity cost. Combining is therefore not "
            "just \"adding effects up\" but acting on two recognition layers at once. Three rules governed the "
            "combinations: (i) each combination must contain at least one mutation that raises the +1 ratio; "
            "(ii) cross-region combinations were preferred to avoid redundancy within a region; (iii) "
            "combinations containing high-activity-cost mutations (e.g. K60Q, W130G) served only as mechanistic "
            "probes, not candidates. The scaffolds were the anchors validated in Iteration 1: K30H (the only "
            "engineering of the +1 layer's reader), G27D/T (the −1 layer), Q58M (among the lowest activity costs, "
            "true role still open) and M132D/E (the exit channel, 15–20 Å from +1 with zero contact frequency, as "
            "an explicit distal control)."
        ),
        build_zh=(
            "候选表由两条线交叉后筛选而成。"
            "第一条线：位点对按证据强度分层。对全部候选位点两两配对，每对同时用三路证据打分——"
            "① 共进化（3504 条同源序列的互信息 MI）；② 结构耦合（复合物中两残基的最小原子距离）；"
            "③ 实验可行性（该位点单点保留率 ≥0.6 且 +1 比最高者）。三路证据都不支持的位点对淘汰，"
            "催化活性相关的禁区（H70/E72/W99/C102/C105）与催化必需的 N57 全程排除。"
            "得到 16 个位点对并分四档：Tier 1「高比+高活性」2 对（27+32、32+132）、"
            "Tier 2「高比+中活性」5 对、Tier 3「中比+高活性」5 对、Tier 4 4 对。"
            "这一层排序完全是先验的，它与实测 +1 比是否相关正是本轮要检验的内容。"
            "第二条线：生成式组合库。把 24 个有生化依据的替换（覆盖 13 个位点）枚举全部双点与三点组合，"
            "施加三条合理性筛选——排除预估去稳定能之和 >2.0 kcal/mol 者、排除不含任何「排 A」突变者"
            "（原理上无法提升特异性）、同位点不重复；按预估 +1 比乘积降序保留前 1000 组，作为假设清单。"
            "收敛：最终构建的 50 个组合以 Tier 1–3 位点对为骨架——44 个规范位点组合中 35 个可对应到上述 16 对，"
            "其中 18 个直接出现在 top-1000 生成式清单中（排名 2–867）；另有 4 个含非规范位点"
            "（34R、62P、63P、140H），属探索性配对。"
            "按同样流程构建后 50 个构建体全部完成转染与测序：44 组 n=2、4 组 n=1、2 组 n=4，共 100 个样本行。"
            "其中 6 个含 W130G 的构建体是「活性开关」探针（130G 单点比 3.00 但保留仅 32%），"
            "12 个含 M132D 的构建体是远端残基的显式对照臂——这两组均非候选。"
        ),
        build_en=(
            "The candidate table came from crossing two lines and filtering. Line one: site pairs tiered by "
            "evidence strength. Every candidate pair was scored on three independent sources at once — "
            "(i) coevolution (mutual information from 3,504 homologues); (ii) structural coupling (minimum "
            "inter-residue atom distance in the complex); (iii) experimental feasibility (the substitution at "
            "that site with retention ≥0.6 and the highest +1 ratio). Pairs unsupported by any of the three "
            "were dropped, and the positions critical for catalytic activity (H70/E72/W99/C102/C105) plus the "
            "catalytically essential N57 were excluded throughout. This yielded 16 site pairs in four tiers: Tier 1 \"high "
            "ratio + high activity\", 2 pairs (27+32, 32+132); Tier 2 \"high ratio + medium activity\", 5; "
            "Tier 3 \"medium ratio + high activity\", 5; Tier 4, 4. This ranking is entirely a priori, and "
            "whether it correlates with the measured +1 ratio is one of the things this cycle set out to test. "
            "Line two: a generative combination library. Every double and triple combination of 24 "
            "biochemically justified substitutions (spanning 13 positions) was enumerated and passed through "
            "three sanity filters — drop combinations whose summed predicted destabilisation exceeds "
            "2.0 kcal/mol, drop those containing no \"reject-A\" substitution (incapable in principle of "
            "raising specificity), and never repeat a position — keeping the top 1,000 by the product of "
            "predicted +1 ratios as a hypothesis list. Convergence: the 50 constructs built take the Tier 1–3 "
            "pairs as their backbone — of the 44 canonical position combinations, 35 map onto one of the 16 "
            "pairs and 18 appear directly in the top-1,000 generative list (ranks 2–867); four further "
            "constructs contain non-canonical positions (34R, 62P, 63P, 140H) and are exploratory. Built by "
            "the same workflow, all 50 constructs completed transfection and sequencing: 44 in duplicate, "
            "4 in singlicate and 2 in quadruplicate, giving 100 sample rows. Six constructs containing W130G "
            "are \"activity switch\" probes (130G alone gives ratio 3.00 at only 32% retention) and twelve "
            "containing M132D are the explicit control arm for a distal residue — neither group is a candidate."
        ),
        test_zh=(
            "同批转染并测序，读取 c.388 / c.871 / c.295，计算 +1 比与相对亲本的活性保留率；"
            "同时做逐位点边际效应分析，判断每个位点对 +1 比与活性的独立贡献。"
        ),
        test_en=(
            "The variants were transfected and sequenced in the same batch, reading c.388 / c.871 / c.295 to "
            "compute the +1 ratio and activity retention relative to the parent; per-position marginal effects "
            "were also analysed to determine each position's independent contribution to ratio and activity."
        ),
        learn_zh=(
            "组合成功突破了单点天花板：G27T-K30H-Q58M 达到 +1 比 2.16、活性保留 77%，"
            "是唯一同时满足「比 ≥2.0」与「保留接近 70% 线」的构建体。它的三个成分恰好对应三个不同的角色："
            "27T 作用于 −1 层、30H 是唯一的 +1 层读取器、58M 负责维持活性。"
            "由此得到两条生物学结论。"
            "① 识别层的可改造性可能并不对等，而且两层作用在不同的底物轴上：−1 层（27 位）用 12% 的活性代价，"
            "把 ACA 类底物的编辑压低 36 倍（0.294 → 0.008）而 GCG 保留 88%——做的是「干净地切掉一整类非 G 底物」；"
            "+1 层（30 位）用 16% 的活性代价，把 GCG/GCA 比值从亲本的 1.37 抬到 1.71——"
            "只能在两个共享 −1=G 的位点之间做有限度的偏置。"
            "本轮唯一达标的组合 27T-30H-58M 恰好同时含有这两层的改造，58M 负责补偿活性；"
            "这成为候选表里的一条设计原则：组合骨架应当跨层。"
            "② 这个结构域不是模块化的：M132D 单点保留 89%，但含它的 12 组组合 C388 中位数仅 0.178、"
            "无一超过 0.30；132 位距 +1 位 15–20 Å、接触频率为 0，从界面角度看它「不在场」，"
            "却在组合突变中对构建体的活性产生了巨大影响。所以我们认为突变效应不能由各自的单点表现加和，"
            "因为它们通过同一张长程耦合网络起作用。M132D 因此被列为硬性排除项，只作为显式对照组。"
            "方法学上，本循环还发现两套实验使用了不同的亲本基数（单点批 C388=0.5145 vs 组合批 0.673），"
            "原始 +1 比不可跨批比较，因此定义了 ROF（相对同批亲本的 +1 比倍数）并在下一轮改为同批设计。"
        ),
        learn_en=(
            "The combinations broke the single-site ceiling: G27T-K30H-Q58M reached a +1 ratio of 2.16 with 77% "
            "activity retention — the only construct satisfying both \"ratio ≥2.0\" and \"retention near the 70% "
            "line\". Its three components map onto three distinct roles: 27T acts on the −1 layer, 30H is the "
            "+1-layer reader we identified, and 58M maintains activity. Two biological conclusions follow. (i) The recognition "
            "layers may not be equally engineerable, and the two act on different substrate axes: the −1 layer "
            "(position 27) spent a 12% activity cost to suppress ACA-class editing 36-fold (0.294 → 0.008) while "
            "keeping 88% of GCG — it cleanly removes an entire class of non-G substrates — whereas the +1 layer "
            "(position 30) spent a 16% activity cost to lift the GCG/GCA ratio from the parent's 1.37 to 1.71, "
            "biasing only the choice between two sites that share −1=G. The one combination that cleared the "
            "target, 27T-30H-58M, happens to contain engineering of both layers, with 58M compensating activity; "
            "this became a design principle in the candidate table: scaffolds should be cross-layer. (ii) The domain "
            "is not modular: M132D retained 89% as a single mutant, yet the twelve combinations containing it had "
            "a median C388 of only 0.178, none above 0.30. Position 132 sits 15–20 Å from +1 with zero contact "
            "frequency — from the interface's point of view it is simply \"not there\" — yet in combinations it "
            "has a large effect on construct activity. We therefore consider that mutation effects cannot be "
            "summed from individual behaviour, because they act through one shared long-range coupling network, "
            "so M132D is a hard exclusion, appearing only as an explicit control group. Methodologically, this cycle also found "
            "that the two experiments used different parental baselines (single batch C388=0.5145 vs combination "
            "batch 0.673), making raw +1 ratios incomparable across batches; we therefore defined ROF (ratio over "
            "fold, relative to the same-batch parent) and switched to same-batch designs in the next cycle."
        ),
        figs=[("wiki_fig3_Cycle2_组合突破.png", "图 2-1　组合突变「+1 比–活性保留」Pareto 前沿", "Fig. 2-1  Pareto front of combinations: +1 ratio vs activity retention")],
        data=[
            ["组合构建体数", "50（双点 + 三点）"],
            ["样本行 / 重复", "100（44 组 n=2、4 组 n=1、2 组 n=4）；分析主表收录 49 个（27D-32F 无可用数据）"],
            ["候选表来源", "16 个证据分层位点对（Tier 1–3 为骨架）× top-1000 生成式组合库（18 个并入）"],
            ["最优组合", "G27T-K30H-Q58M：+1 比 2.16 / 保留 0.77（−1 层 + +1 层 + 活性补偿）"],
            ["−1 层改造（27 位）", "G27D：ACA 0.008（亲本 0.294，36 倍压制）/ 保留 0.88；G27T：ACA 0.042 / 保留 0.98"],
            ["+1 层改造（30 位）", "K30H：+1 比 1.71 / 保留 0.84（单点天花板）"],
            ["跨层 vs 同层", "唯一同时越过 +1 比 2.0 且保留接近 70% 线的组合是跨层的 27T-30H-58M"],
            ["+1 比 >2.5 的组合", "保留率全部 <40%"],
            ["M132D 单点 vs 组合", "单点保留 0.89；含它的 12 组组合 C388 中位 0.178（远端残基的长程耦合）"],
            ["跨批校正指标", "ROF = 自身 +1 比 ÷ 同批亲本 +1 比"],
        ],
    ),
    dict(
        num=3,
        title_zh="迭代 3：放大到整段转录本——酶究竟靠什么挑位点",
        title_en="Iteration 3: Widening to the whole transcript — what actually governs site choice",
        overview_zh=(
            "问题：如果酶真的只读 +1 位，那么全部 GCG 位点都应当被同等编辑——这个预言可以直接检验。"
            "做法：把观察窗口从两个位点放大到整段 APOE 扩增子（951 bp、291 个 C 位点），"
            "对 57 个构建体共 117 个样本逐位点扫描，并同时检验改造结合域这条替代路线。"
            "结果：预言不成立。47 个 GCG 位点共享同一个 −1/+1 上下文，编辑率却从 67.3% 一路铺到检出线下；"
            "全扩增子编辑最强的前两个热点之一是 GCG（c.390）；靶点编辑与脱靶编辑高度正相关（r = +0.760），"
            "脱靶不是可以单独进行筛选的模块。由此得到本项目的核心结论：底物选择性至少分布在三层上。"
        ),
        overview_en=(
            "Question: if the enzyme really reads only the +1 position, then every GCG site should be edited "
            "equally — a prediction we can test directly. What we did: widened the observation window from two "
            "sites to the whole APOE amplicon (951 bp, 291 C sites), scanning every position across 117 samples "
            "from 57 constructs, and tested the alternative route of engineering the binding domain. Result: the "
            "prediction fails. The 47 GCG sites share an identical −1/+1 context, yet editing spans 67.3% down "
            "to below detection; one of the two most heavily edited hotspots in the whole amplicon is itself a "
            "GCG (c.390); and on-target and off-target editing are strongly correlated (r = +0.760), so "
            "off-targets are not a module that can be screened independently. This gave the project its central "
            "conclusion: substrate selectivity is distributed over at least three layers."
        ),
        design_zh=(
            "前两个循环只用 c.388 与 c.871 两个位点评价特异性，但这个定义背后藏着一个很强的生物学断言："
            "酶读的是 +1 位。如果这个断言成立，扩增子里全部 47 个 GCG 位点（−1 = G、+1 = G）应当被同等编辑——"
            "它们在这个位置上完全一样；如果它们的编辑率差异很大，那么 +1 位就只是决定位点选择的众多因素之一。"
            "这个预言可以直接检验。"
            "因此我们把观察窗口换成整个 APOE 扩增子（951 bp，291 个 C 位点）："
            "把全部 GCG 基序位点（47 个）视为「靶向集」，其余 244 个 C 位点视为「非靶向集」，"
            "定义靶向比 targeting_ratio = Σ(GCG 编辑率) ÷ Σ(非 GCG 编辑率)，"
            "并逐位点记录编辑率、脱靶位点数、脱靶负荷与新增脱靶位点。"
        ),
        design_en=(
            "The first two cycles assessed specificity using only c.388 and c.871, but that definition carries a "
            "strong biological claim: the enzyme reads the +1 position. If it holds, all 47 GCG sites in the "
            "amplicon (−1 = G, +1 = G) should be edited equally — they are identical at that position. If their "
            "editing efficiencies differ substantially, then +1 is only one of several determinants of site "
            "choice. The prediction is directly testable. We therefore switched the observation window to the "
            "whole APOE amplicon (951 bp, 291 C sites): all 47 GCG-motif C sites were treated as the \"target "
            "set\" and the remaining 244 C sites as the \"non-target set\", defining the targeting ratio "
            "targeting_ratio = Σ(GCG editing) ÷ Σ(non-GCG editing), with per-site editing efficiency, off-target "
            "site counts, off-target load and newly emerged off-target sites recorded alongside."
        ),
        build_zh=(
            "对全部 57 个构建体做 APOE 扩增子深度测序，共 117 个样本（含 a/b 重复）；"
            "另外引入一组 P 域（核酸结合域）重设计变体（P4–P8）以检验结合域改造是否可提升特异性。"
            "同时重分析公共 CU5.1 转录组数据（3 处理 + 3 对照）以独立确认 +1 位脱靶的存在。"
        ),
        build_en=(
            "All 57 constructs were subjected to APOE amplicon deep sequencing, giving 117 samples (including "
            "a/b replicates). A set of P-domain (nucleic-acid-binding domain) redesign variants (P4–P8) was "
            "introduced to test whether engineering the binding domain could improve specificity. Public CU5.1 "
            "transcriptome data (3 treated + 3 control) were re-analysed to independently confirm the existence "
            "of +1-position off-targets."
        ),
        test_zh=(
            "逐位点统计编辑率、脱靶位点数、脱靶负荷与新增脱靶位点，并与亲本 PUF12-9 比较。"
            "关键检验是「+1 位相同则编辑率应当相同」这条预言：亲本在 47 个 GCG 位点中有 26 个高于 5% 检出下限，"
            "编辑率从 c.388 = 67.3%、c.390 = 61.7%（几乎与靶点持平）、c.874 = 50.2% 一路铺到检出线下，中位数 13.8%——"
            "这些位点的 −1 与 +1 完全相同，因此这些差异不能归因于 +1 位。"
            "此外，全部 74 个检出脱靶位点中平均编辑率最高的正是 c.390（GCG，0.251），高于经典脱靶 c.871（GCA，0.198）。"
        ),
        test_en=(
            "Per-site editing efficiency, off-target site counts, off-target load and newly emerged off-target "
            "sites were tabulated and compared with the parent PUF12-9. The key test is the prediction that "
            "identical +1 means identical editing: 26 of the 47 GCG sites were edited above the 5% detection floor "
            "in the parent, spanning c.388 = 67.3%, c.390 = 61.7% (essentially tied with the on-target), c.874 = "
            "50.2% and down to below detection, median 13.8% — these sites are identical at both −1 and +1, so the "
            "differences cannot be attributed to +1. Separately, the highest mean editing among all 74 detected "
            "off-target sites belongs to c.390 (GCG, 0.251), above the classic off-target c.871 (GCA, 0.198)."
        ),
        learn_zh=(
            "本轮最重要的结果是生物学层面的：预言不成立，+1 位相同而编辑率相差一个数量级。"
            "全部 47 个 GCG 位点共享同一个 −1/+1 上下文，因此它们之间的差异只能来自 ±1 之外——"
            "更远的侧翼序列与 RNA 可及性。+1 位是必要但不充分的条件。"
            "更直接的一条：全部 74 个检出脱靶中编辑最强的是 c.390（GCG），它和靶点 c.388 在 +1 位上完全一样，"
            "却被编辑得几乎一样多——GCG 基序本身并不等于安全。"
            "由此我们得到一个关于这个酶如何挑底物的图景：底物选择性至少分布在三层上——"
            "RNA 结合与可及性、−1 位识别、+1 位容忍。本轮的结果分别落在这三层上："
            "① 脱靶清除可行但代价是活性：7 组组合两次重复中 c.871 均检出为 0，保留率却全部低于 22%；"
            "②  贯穿全局的定量事实是 on-target 效率与脱靶总量高度正相关（Pearson r = +0.760）："
            "在本轮的突变谱里，靶点编辑与脱靶编辑共享同一个决定因素，脱靶不是可以单独拆下来的模块。"
            "方法学上，本轮新定义的靶向比被 5% 检测下限污染（低活性层中位 2.53 vs 高活性层 1.20；"
            "Spearman ρ(靶向比, Σ非GCG) = −0.557，Pearson r = −0.390，n = 41；50 行中 9 行比值为 ∞），"
            "若直接按它排序，榜首会是活性 0.000 的死构建体。补做回补检验后：加下限使 ∞ 由 9 降至 0、"
            "原始 top-10 与新 top-10 重叠为 0，但偏倚只是减弱而非消除（r 从 +0.760 降至 +0.598，"
            "ρ 从 −0.557 变为 −0.650）。由此重新定义规则：解读脱靶设 on-target ≥0.30 下限，比值型指标不单独使用；"
            "61 条候选以 +1 比与机制论证挑选，未受该偏倚影响。"
        ),
        learn_en=(
            "The most important outcome of this cycle is biological: the prediction failed, and identical +1 "
            "yields editing that differs by an order of magnitude. All 47 GCG sites share the same −1/+1 "
            "context, so the differences between them can only come from outside the ±1 window — more distal "
            "flanking sequence and RNA accessibility. The +1 position is necessary but not sufficient. Even more "
            "directly: the most heavily edited of all 74 detected off-targets is c.390 (GCG), which is identical "
            "to the on-target c.388 at +1 yet edited almost as much — a GCG motif is not by itself safe. This "
            "gives a picture of how the enzyme picks its substrate: selectivity is distributed over at least three "
            "layers — RNA binding and accessibility, −1 recognition, and +1 tolerance — and the results of "
            "this cycle land on them respectively. (i) Off-target clearance is achievable but costs activity: "
            "seven combinations showed no detectable c.871 editing in either replicate, all with retention below "
            "22%. (ii) Running through everything: on-target efficiency and total off-target editing "
            "are strongly positively correlated (Pearson r = +0.760) — across this mutational spectrum the two "
            "share a common determinant, so off-targets are not a module that can be detached. Methodologically, the "
            "targeting ratio defined in this cycle is confounded by the 5% detection floor (median 2.53 in the "
            "low-activity stratum vs 1.20 in the high-activity stratum; Spearman ρ(targeting ratio, Σ non-GCG) = "
            "−0.557, Pearson r = −0.390, n = 41; 9 of 50 rows undefined), and ranking by it directly would have "
            "put a construct with activity 0.000 at the top. Back-testing showed the activity floor removes the "
            "extreme artefact (undefined 9 → 0) and that the floored top-10 shares no members with the original, "
            "but the bias is only weakened, not removed (r +0.760 → +0.598; ρ −0.557 → −0.650). We therefore "
            "redefined the rules: apply an "
            "on-target ≥0.30 floor when interpreting off-targets, and never use a ratio-type metric on its own; "
            "the 61 candidates were selected on +1 ratio and mechanistic reasoning and were unaffected."
        ),
        figs=[("wiki_fig4_Cycle3_指标偏倚.png", "图 3-1　靶向比的系统性偏倚：随活性下降而虚高", "Fig. 3-1  Systematic bias of the targeting ratio"),
              ("fig3_总体脱靶负荷.png", "图 3-2　各构建体的总体脱靶负荷", "Fig. 3-2  Global off-target load of each construct"),
              ("cycle3b-rerank/cycle3b@2x.png", "图 3-3　活性下限的回补检验与重新排序",
               "Fig. 3-3  Back-testing the activity floor and re-ranking")],
        data=[
            ["观察窗口", "APOE 扩增子 951 bp，291 个 C 位点"],
            ["样本 / 构建体", "117 个样本 / 57 个构建体"],
            ["靶向集 / 非靶向集", "47 个 GCG 位点 / 244 个其他 C 位点"],
            ["核心检验：+1 相同 ≠ 编辑相同", "亲本 26/47 个 GCG 位点高于检出线：388 = 67.3%、390 = 61.7%、874 = 50.2%，中位数 13.8%"],
            ["编辑最强的脱靶", "c.390（GCG，均值 0.251）—— 高于经典脱靶 c.871（GCA，0.198），与靶点共享 +1"],
            ["检出脱靶热点", "74 个"],
            ["脱靶清除组（检出为 0）", "7 组（C871 两次重复均未检出），但保留率全部 <22%"],
            ["活性–脱靶耦合", "Pearson r(C388%, Σ非GCG%) = +0.760 —— 靶点与脱靶编辑共享同一决定因素"],
            ["P 域变体新增脱靶", "19 个（占全部新增脱靶的 68%），on-target 活性仍保持 0.61–0.77 → 方向放弃"],
            ["指标偏倚", "Spearman ρ(靶向比,Σ非GCG)=−0.557（Pearson r=−0.390, n=41）"],
            ["回补检验·加下限后", "n=17；∞ 由 9→0；Spearman ρ 变为 −0.650，r(C388%,Σ非GCG%) 降至 +0.598"],
            ["回补检验·重新排序", "原始 top-10 全部低于活性下限（10/10）；加下限后与原 top-10 重叠 0/10"],
            ["六种口径一致性", "除原始口径外，其余五种 top-10 互相重叠 7–10/10"],
            ["稳健候选（8 个）", "25E-32F、27T-32F、32F-132E、25E-132E、25E-27D、30H-58M、27T-30H-58M、27T-32F-132E"],
            ["对最终决策的影响", "61 条候选以 +1 比与机制论证挑选，未使用靶向比排序；偏倚未传导"],
            ["活性下限", "on-target ≥0.30（否则 32 个样本产生「零脱靶」假象）"],
        ],
    ),
    dict(
        num=4,
        title_zh="迭代 4：结构复核——我们改的到底是不是「界面」",
        title_en="Iteration 4: Structural re-examination — did we actually change the interface?",
        overview_zh=(
            "问题：我们在 loop 上做的这些保守替换，究竟有没有改变蛋白–RNA 界面？"
            "做法：引入一组答案已知的对照——已知完全失活的构建体、催化核心对照，"
            "以及最关键的「只换底物、蛋白一字未改」的 WT-GCA；同时提交不含 RNA 的纯蛋白建模任务。"
            "结果：按机制必然失活的催化敲除 E72A 结构偏离全场最低，而只换底物的 WT-GCA 反而高过真正失活的 T31D。"
            "三条证据指向同一结论：决定接触模式的是喂进去哪条 RNA，我们的替换只做了能量层面的微调、并未重塑界面"
            "——这正是迭代 1 那面墙的结构解释。"
        ),
        overview_en=(
            "Question: did the conservative loop substitutions we made actually change the protein–RNA "
            "interface? What we did: introduced a set of controls whose answers we already knew — constructs "
            "confirmed inactive and catalytic-core controls, plus the crucial wild-type protein with only the "
            "substrate swapped (WT-GCA) — and submitted RNA-free, protein-only modelling jobs alongside. Result: "
            "E72A, an obligatory-dead catalytic knockout, has the lowest structural deviation in the set, while "
            "substrate-swapped WT-GCA exceeds the genuinely inactive T31D. Three lines of evidence converge: the "
            "contact pattern is set by which RNA is fed in, and our substitutions only tuned the interface "
            "energetically without remodelling it — the structural explanation for the wall in Iteration 1."
        ),
        design_zh=(
            "前面三个循环中，我们一直在用 AlphaFold3 的接触概率（CP）来判断突变体的结构变化，"
            "而它背后是一个关于这个蛋白的生物学假设，且从未被明说："
            "「突变导致功能丧失，是因为它改变了蛋白–RNA 界面的接触模式，因此结构偏离应当与功能丧失同步」。"
            "这个假设可以直接检验——只要引入一组我们确知答案的构建体。"
            "我们从既有单点与组合数据中回溯挑选已知完全失活的构建体（T31D、N57W、G27D-M130G），"
            "加上同位点活性对照 T31A、催化核心对照 N57A 与 E72A；"
            "而最关键的对照是 WT 只更换底物（蛋白序列完全不变，RNA 由 GCGCG 换成 GCACG）——"
            "如果 CP 反映的是「蛋白被改成了什么」，它应当几乎不偏离。"
            "此外，为区分「突变效应」与「RNA 结合效应」，我们另外提交了不含 RNA 的纯蛋白 AF3 建模任务。"
        ),
        design_en=(
            "Across the first three cycles we had been using AlphaFold3 contact probabilities (CP) to judge "
            "structural change in mutants, resting on a biological assumption about this protein that was never "
            "stated explicitly: \"a mutation causes loss of function because it changes the contact pattern of "
            "the protein–RNA interface, so structural deviation and loss of function should track each other.\" "
            "That assumption is directly testable — all it takes is a set of constructs whose answer we already "
            "know. Constructs known to be completely inactive were retrospectively selected from the existing "
            "single and combinatorial data (T31D, N57W, G27D-M130G), together with the same-position active "
            "control T31A and the catalytic-core controls N57A and E72A. The most important control of all was "
            "wild-type protein with only the RNA swapped from GCGCG to GCACG — if CP reflects \"what the protein "
            "was changed to\", this control should barely deviate. To separate mutation effects from RNA-binding "
            "effects, we additionally submitted RNA-free (protein-only) AlphaFold3 jobs."
        ),
        build_zh=(
            "对上述 7 个构建体分别构建 GCG 与 GCA 两种底物的复合物模型，并额外提交 60 个不含 RNA 的纯蛋白任务"
            "（WT 20 个 seed + 10 个构建体各 4 个 seed）。"
        ),
        build_en=(
            "Complex models were built for the seven constructs against both GCG and GCA substrates, and 60 "
            "additional RNA-free (protein-only) jobs were submitted (20 seeds for WT plus 4 seeds for each of "
            "10 constructs)."
        ),
        test_zh=(
            "以仅由 WT 自身 20 个 seed 定义的白化基计算马氏距离 D_M（避免基底被纳入的构建体污染），"
            "并用 WT seed 留一法建立零假设（95 分位 = 1.57）。同时比较复合物与纯蛋白两种条件下的偏离。"
        ),
        test_en=(
            "Mahalanobis distances D_M were computed on a whitening basis defined solely by WT's own 20 seeds "
            "(avoiding contamination of the basis by whichever constructs are included), with a null "
            "distribution from leave-one-out WT seeds (95th percentile = 1.57). Deviation was compared between "
            "complex and protein-only conditions."
        ),
        learn_zh=(
            "结果推翻了这条假设，并给出一个关于这个界面的生物学结论：我们做的替换并没有重塑界面。"
            "① 按机制必然失活的催化敲除 E72A 的 D_M = 0.903，是全部 28 个构建体中最低的——拆掉催化中心，界面本身几乎纹丝不动，"
            "提示结合与催化在这个酶里可能是解耦的：一个「结合得好」的构建体完全可能是一个死酶；"
            "② 只换底物、蛋白一个字都没改的 WT-GCA，D_M = 5.605，超过了完全失活的 T31D（5.498）——"
            "决定接触模式的是「喂进去哪条 RNA」，而不是「蛋白被改成了什么」；"
            "③ 纯蛋白对照给出机制解释：T31D 的 78% 偏离在去掉 RNA 后消失，而 E72A 是唯一一个"
            "「去掉 RNA 后偏离反而变大」的构建体（0.903 → 1.656），RNA 结合掩盖了它的蛋白缺陷。"
            "序列同一性超过 99% 的突变体骨架几乎重合，而界面接触模式完全随底物而变——"
            "也就是说，我们在 loop 上做的保守替换只是在既有界面上做能量层面的微调，没有重塑它。"
            "这为迭代 1 的那面墙提供了一个结构层面的解释：如果 +1 层连可被重塑的结构差异都不存在，"
            "「找到读取残基并优化它」从一开始就没有着力点——两轮从完全不同的方向得到了同一个结论。"
            "由此推出：+1 的区分只能来自能量与动力学层面的细微差别（氢键强度、侧链构象分布、界面水），"
            "这落在 AF3 接触概率的分辨率之下，也解释了为何基于结合强度的预测工具会系统性失效。"
            "方法学上，CP 类特征的方差被 RNA 主导（蛋白信号仍占 22%–72%，N57W 这类剧烈扰动可被检出，D_M = 8.889 全批最高），"
            "因此 CP / PCA / 马氏距离不能作为功能预测依据；马氏距离基底只能用 WT 自身 seed 定义。"
        ),
        learn_en=(
            "The results were not consistent with the assumption, and point to a biological conclusion about this interface: our "
            "substitutions did not remodel it. (i) The catalytic knockout E72A — dead by mechanism — had D_M = 0.903, "
            "the lowest of all 28 constructs — removing the catalytic centre leaves the interface essentially "
            "untouched, suggesting that binding and catalysis may be decoupled in this enzyme: a construct that binds "
            "well can perfectly well be a dead enzyme. (ii) WT-GCA, with the protein sequence entirely unchanged "
            "and only the substrate swapped, had D_M = 5.605, exceeding the completely inactive T31D (5.498) — "
            "what determines the contact pattern is which RNA was fed in, not what the protein was changed to. "
            "(iii) Protein-only controls supplied the mechanism: 78% of T31D's deviation disappeared when RNA was "
            "removed, while E72A was the only construct whose deviation increased upon RNA removal (0.903 → "
            "1.656) — RNA binding masks its protein defect. Mutants with over 99% sequence identity have "
            "essentially superimposable backbones while the interface follows the substrate, so the conservative "
            "loop substitutions we made only tuned the existing interface energetically; they did not remodel it. "
            "This offers a structural explanation for the wall in Iteration 1: if the +1 layer does not even present "
            "a structural difference that could be remodelled, \"find the reading residue and optimise it\" had no "
            "point of application — two cycles approaching from opposite directions reached the same conclusion. "
            "It follows that discrimination at +1 can only arise from fine differences in energy and dynamics "
            "(hydrogen-bond strength, sidechain conformational distributions, interfacial water), below the "
            "resolution of AF3 contact probabilities — which is why predictors built on binding strength fail "
            "systematically here. Methodologically, CP-type variance is dominated by RNA (protein signal still "
            "accounts for 22–72%; a severe perturbation like N57W is detectable at D_M = 8.889, the highest in the "
            "set), so CP / PCA / Mahalanobis cannot be used to predict function, and the Mahalanobis basis must be "
            "defined by wild type alone."
        ),
        figs=[("wiki_fig5_Cycle4_阴性对照.png", "图 4-1　阴性对照 D_M 排序：偏离大 ≠ 失活", "Fig. 4-1  D_M ranking of negative controls"),
              ("fig15_纯蛋白_vs_复合物.png", "图 4-2　纯蛋白（无 RNA）与复合物偏离对比", "Fig. 4-2  Deviation in protein-only vs complex conditions")],
        data=[
            ["阴性对照构建体", "7 个（T31D、N57W、G27D-M130G、T31A、N57A、E72A + WT-GCA）"],
            ["判读统计量", "D_M = WT 自身 seed 基底的z分数均方根；零假设 95 分位 = 1.57"],
            ["E72A（必然失活）", "D_M = 0.903 —— 28 个构建体中最低（催化敲除不改变界面）"],
            ["WT 只换底物", "D_M = 5.605 > T31D（完全失活）5.498（界面由 RNA 决定）"],
            ["纯蛋白对照", "T31D 5.498 → 1.202（78% 偏离来自 RNA）；E72A 0.903 → 1.656（唯一反向）"],
            ["蛋白信号仍存在", "N57W（剧烈扰动催化核心）D_M = 8.889，全批最高"],
            ["生物学结论", "我们的替换只做能量微调、不重塑界面 —— +1 特异性不可能来自结构上看得见的读取器"],
            ["方法学结论", "CP 类特征主要编码「结合了哪条 RNA」，不能用于功能判别"],
        ],
    ),
    dict(
        num=5,
        title_zh="迭代 5：计算路线回溯、下一轮设计与该批实测结果",
        title_en="Iteration 5: Auditing the computational routes, designing the next round, and the results of that batch",
        overview_zh=(
            "问题：所有计算路线都没能预测 +1 特异性——这是数据不够，还是天然序列分布本就不围绕 +1 区分组织？"
            "做法：三项彼此独立的检验——逆折叠采样的偏好方向、AiCE 结构约束过滤器的回溯应用、"
            "以及监督学习分别预测活性保留与特异性。"
            "结果：三条证据一致。MPNN 采样频率与 +1 比负相关（ρ = −0.499），实测最佳的 K30H 在采样中频率为 0.000；"
            "监督学习能预测活性保留（r = 0.613，p = 0.005）却不能预测特异性（p = 0.164）。"
            "+1 区分不是这个家族进化出来的性状，从天然分布采样的方法在这里会系统性失效"
            "——下一轮因此改为「跨层高约束设计 + 小规模湿实验验证」。"
        ),
        overview_en=(
            "Question: no computational route predicted +1 specificity — is that a matter of insufficient data, "
            "or is the natural sequence distribution simply not organised around +1 discrimination? What we did: "
            "three mutually independent tests — the direction of inverse-folding preference, a retrospective "
            "application of AiCE's structural-constraint filter, and supervised learning to predict activity "
            "retention and specificity separately. Result: all three agree. MPNN sampling frequency correlates "
            "negatively with the +1 ratio (ρ = −0.499), and K30H — our best measured variant — has a sampling "
            "frequency of 0.000; supervised learning predicts activity retention (r = 0.613, p = 0.005) but not "
            "specificity (p = 0.164). +1 discrimination is not a trait this family evolved, and methods that "
            "sample the natural distribution fail systematically here — so the next round switched to "
            "cross-layer, high-constraint design with small-scale wet-lab validation."
        ),
        design_zh=(
            "前四个循环中我们尝试过多条计算预测路线（分子设计工具 mCSM-NA / PremPRI、加性先验模型、"
            "逆折叠模型 ProteinMPNN、接触概率 CP），但都未能预测 +1 特异性。"
            "这些失败有两种完全不同的解读：一种是技术性的（样本不够、采样参数不对，扩大投入就能解决），"
            "另一种是生物学的——如果 +1 位读取器是自然界从未建造过的东西，"
            "那么任何从天然序列分布中采样的方法在原理上都不可能把它采样出来。"
            "迭代 1 的结构分析与迭代 4 的阴性对照都指向后者，但它们都来自我们自己的建模，"
            "因此需要独立于建模的证据来源。"
            "三项检验因此被设计出来，它们的共同点是都直接问：天然序列分布是否围绕 +1 区分组织？"
            "① 用 top-5 / top-10 回收率而非相关性重新评价全部方法；"
            "② 用现有样本做监督学习，分别预测活性保留与靶向比；"
            "③ 检验 2025 年 Cell 发表的 AiCE 方法（其核心论点正是「裸逆折叠偏好不够，需叠加结构约束」）"
            "能否救回逆折叠路线——回溯地把它的 β/γ 二级结构约束过滤器应用到我们已有的 ProteinMPNN 采样输出上。"
        ),
        design_en=(
            "In the first four cycles we tried several computational prediction routes (molecular design tools "
            "mCSM-NA / PremPRI, an additive prior model, the inverse-folding model ProteinMPNN, and contact "
            "probabilities), none of which predicted +1 specificity. That failure admits two entirely different "
            "readings: a technical one (not enough samples, wrong sampling parameters — more investment would fix "
            "it) and a biological one — if the +1 reader is something nature never built, no method that samples "
            "the natural sequence distribution can ever sample it. Iteration 1's structural analysis and "
            "Iteration 4's negative controls both point to the second reading, but both come from our own "
            "modelling, so evidence independent of it is needed. Three tests were therefore designed around one "
            "shared question: is the natural sequence distribution organised around +1 discrimination at all? "
            "(i) Re-evaluating all methods by top-5 / top-10 recovery instead of correlation; (ii) supervised "
            "learning on the existing samples to predict activity retention and targeting ratio separately; "
            "(iii) testing whether AiCE (Cell 2025), whose central claim is precisely that \"raw inverse-folding "
            "preference is insufficient without structural constraints\", can rescue the inverse-folding route — "
            "by retrospectively applying its β/γ secondary-structure constraint filter to our existing "
            "ProteinMPNN sampling output."
        ),
        build_zh=(
            "回溯分析已有的 ProteinMPNN 采样输出（48 条 T=0.3 序列），"
            "用纯 Python DSSP 实现（pydssp）计算二级结构，按 AiCE 官方代码的规则"
            "（结构化区 β = 0.8、无规卷曲区 γ = 0.5）重新过滤，并与 102 个单点的湿实验结果对照。"
            "\n\n本轮的另一半是湿实验构建：按候选表构建并转染了 **37 个突变组**（另含 PUF10、PUF12 两个参照），共 77 个样本行，覆盖 A 复验、B 新单点、C 新组合、D 控制变量与 E 异常配对／放宽口径五组。其中 D 组是为「M132D 破坏活性」这一争议设置的同背景配对（132D 与 132E 各一条）。"
        ),
        build_en=(
            "Existing ProteinMPNN sampling output (48 sequences at T=0.3) was re-analysed; secondary structure "
            "was computed with a pure-Python DSSP implementation (pydssp) and re-filtered using the rules from "
            "AiCE's official code (β = 0.8 in structured regions, γ = 0.5 in coil regions), then compared against "
            "the 102 single-mutant wet-lab results."
            "\n\nThe other half of this cycle was wet-lab construction: **37 mutant groups** were built and transfected according to the candidate table (plus two references, PUF10 and PUF12), giving 77 sample rows and covering all five groups — A replication, B new single substitutions, C new combinations, D control variants, and E anomalous pairings plus relaxed-criterion pairings. Group D is the same-background pairing designed to settle the M132D question, with one 132D and one 132E construct."
        ),
        test_zh=(
            "计算三种过滤口径（不过滤 / 频率 ≥0.50 / AiCE β/γ）下的精确率与召回率；"
            "计算 MPNN 采样频率与活性保留、+1 比的 Spearman 相关；"
            "并检验被点名的「强偏好」替换能否被 β/γ 过滤器剔除。"
            "\n\n湿实验侧读取 c.388（GCG）与 c.871（GCA）的编辑效率，并以同批亲本 PUF12（比值 1.070）计算 ROF 作跨批可比量。c.295 本批仅有 32% 的样本具备可信深度记录，因此不产出任何 ACA 类结论。所有有深度记录且可用的样本 DP 均 ≥ 500。"
        ),
        test_en=(
            "Precision and recall were computed under three filtering regimes (no filter / frequency ≥0.50 / "
            "AiCE β/γ); Spearman correlations were computed between MPNN sampling frequency and both activity "
            "retention and +1 ratio; and we tested whether the named \"strongly preferred\" substitutions could "
            "be removed by the β/γ filter."
            "\n\nOn the wet-lab side, editing efficiency was read at c.388 (GCG) and c.871 (GCA), and ROF was computed against the same-batch parent PUF12 (ratio 1.070) as the cross-batch comparable quantity. Only 32% of samples carried a reliable depth record at c.295, so no ACA-class conclusion is drawn from this batch. Every usable sample had DP ≥ 500."
        ),
        learn_zh=(
            "三条彼此独立的证据指向同一个结论：天然的序列–结构空间不是围绕 +1 位区分组织的。"
            "① 逆折叠模型的偏好方向与我们要的方向相反：MPNN 采样频率与活性保留无相关（ρ = +0.060），"
            "与 +1 比负相关（ρ = −0.499）——模型越倾向于在某位点采样，实测的 +1 特异性越差；"
            "实测最佳的 K30H 在 48 条采样序列中频率为 0.000，根本不在模型给出的分布里，"
            "活性前 14 名单点无一被提名。"
            "② 结构约束层救不回这条路线：AiCE 的 β/γ 过滤器没能剔除任何一个争议替换"
            "（H29P 0.771 / K30T 0.562 / N57D 0.875 / A59P 0.896 均远高于阈值）——"
            "原因是定义层面的：APOBEC 的底物结合界面本身就是 loop，18 个候选位点中 16 个二级结构为无规卷曲，"
            "全部适用宽松阈值 γ = 0.5，约束层恰好放过了我们最关心的界面。"
            "③ 监督学习能预测活性保留（r = 0.613，p = 0.005），但不能预测特异性（p = 0.164）——"
            "这是一个重要的生物学分界：活性与特异性由不同的结构决定因素编码，特异性不是结合强度的单调函数。"
            "三条证据从三个方向印证了迭代 1 的结构结论：+1 区分不是这个家族进化出来的性状，"
            "而是要被发明出来的性状。这也解释了为什么目前唯一有效的 +1 层改造（K30H）来自定点替换而非生成式设计。"
            "由此我们确立了下一轮的路线：放弃「用机器学习预测特异性」，改为「高约束设计 + 小规模湿实验验证」。"
            "方法层面需注明：top-5 / top-10 回收率检验中全部方法均未通过显著性（p ≥ 0.685），"
            "但可比样本仅 6–13 个、此类指标在小样本下方差极大，只能作为旁证。"
            "\n\n**本批湿实验结果给出四组结论。**① **D 组配对达成设计目的**：同一骨架上仅把 132 位由 D 换成 E，活性保留率就从 0.34 升到 0.75（2.2 倍），M132D 的活性压制作用由此从组合层面的统计观察变成直接测量，「132 位该用哪个」的争议就此关闭——**E 可用，D 不可用**。② **此前的最佳组合 `27T-30H-58M` 被复现**：含其全部三个突变的 `27T-30H-58M-132E` 本批给出 C388 0.533 / C871 0.256 / 比值 2.08 / 保留 0.67（ROF 1.95），而该骨架在组合批为 0.520 / 0.241 / 2.156 / 0.77——绝对编辑率仅相差 +2.5% / +6.1% / −3.4%，而此时两批亲本基数相差 18%。**该骨架因此是经过两次独立测量确认的最优组合**；132E 接近表现中性（保留率口径 −0.10、ROF 口径 +0.14，两个口径方向相反），是可选附加项而非必要条件。③ **`27T-30H-58M` 自身所在孔（C13）判为测量失败并剔除，不作为负结果**：该孔 C388 仅 0.063、c.871 两次重复均未检出。判定依据来自本批内部——真正失活的构建体不会因为增加一个残基就把保留率恢复到 0.67（8 倍回升），而本项目没有任何位点表现出这种量级的补偿；同样的三个替换在 D03 中测得 0.533，即为例证。这里只主张「该孔剔除」（数据可用性判断），不主张「原因是操作失误」（原因判断，需那次转染的湿实验记录支持）。④ **两条探索性路线被否证**：含 R28A 的两个组合 ROF 均低于亲本（0.99、0.88）；「异常配对」组除 `130G-32F` 外全部无增益，含 130G 或 131R 者活性一律 ≤0.48。作为对照，A 组两个单点（M132D、I26N）的 ROF 与既有批次几乎完全一致（1.04 → 1.07、1.04 → 1.04），而它们的绝对比值在本批是 1.15 / 1.12、在既有批是 1.42——这验证了 ROF 归一化有效、绝对比值不可跨批比较（亲本比值三批为 1.371 → 1.191 → 1.070）。**需要更正的一点**：本稿初版曾据 C13 提出「组合比单点对批次敏感」，并把多批重复列为与剂量梯度并列的缺口；既然 C13 判为孔失败，该对比不成立——剔除该孔后，每一个被测量两次的构建体都复现了，目前没有证据表明构建体本身不稳定。"
        ),
        learn_en=(
            "Three lines of evidence independent of one another point to one conclusion: the natural "
            "sequence–structure space is not organised around +1 discrimination. (i) The inverse-folding model's "
            "preference points the opposite way from our goal — MPNN sampling frequency shows no correlation with "
            "activity retention (ρ = +0.060) and a negative correlation with the +1 ratio (ρ = −0.499): the more "
            "the model favours sampling at a position, the worse the measured +1 specificity there. K30H, our best "
            "measured variant, has a frequency of 0.000 in the 48 sampled sequences — it is not in the distribution "
            "the model proposes at all — and not one of the top fourteen single mutants by activity retention "
            "would have been nominated. (ii) The structural-constraint layer cannot rescue the route either: "
            "AiCE's β/γ filter failed to remove a single contested substitution (H29P 0.771 / K30T 0.562 / N57D "
            "0.875 / A59P 0.896 all far above threshold), for a definitional reason — the APOBEC substrate-binding "
            "interface is itself a loop, and sixteen of the eighteen candidate positions are coil by secondary "
            "structure, so all fall under the permissive γ = 0.5; the constraint layer passes over the "
            "interface we care about most. (iii) Supervised learning can predict activity retention (r = 0.613, "
            "p = 0.005) but not specificity (p = 0.164) — an important biological boundary: activity and "
            "specificity are encoded by different structural determinants, and specificity is not a monotone "
            "function of binding strength. Together the three corroborate Iteration 1's structural conclusion from "
            "three directions: +1 discrimination is not a trait this family evolved but one that has to be "
            "invented, which is also why the only effective +1 engineering so far (K30H) came from site-directed "
            "substitution rather than generative design. We therefore set the next round's strategy: abandon "
            "\"using machine learning to predict specificity\" in favour of \"high-constraint design + small-scale "
            "wet-lab validation\". Noted for the record: in the top-5 / top-10 recovery test no method passed "
            "significance (p ≥ 0.685), but only 6–13 comparable samples exist and such metrics have enormous "
            "variance at that size, so it serves as corroboration only."
            "\n\n**The wet-lab half of this cycle produced four sets of conclusions.** (i) **The Group D pairing achieved its design purpose**: on an identical scaffold, changing position 132 from D to E alone raised activity retention from 0.34 to 0.75 (2.2-fold). The activity suppression caused by M132D is thereby promoted from a statistical observation at the combination level to a direct measurement, and the question of which residue belongs at position 132 is closed — **E is usable, D is not**. (ii) **The previous best combination, `27T-30H-58M`, was reproduced**: `27T-30H-58M-132E`, which carries all three of its substitutions, measured C388 0.533 / C871 0.256 / ratio 2.08 / retention 0.67 (ROF 1.95) here, against 0.520 / 0.241 / 2.156 / 0.77 for the scaffold in the combinatorial batch — absolute editing differing by only +2.5% / +6.1% / −3.4% while the two batches' parental baselines differed by 18%. **The scaffold is therefore the best combination confirmed by two independent measurements.** M132E is close to performance-neutral (the retention normalisation puts it 0.10 lower and ROF puts it 0.14 higher), an optional addition rather than a requirement. (iii) **The `27T-30H-58M` well itself (C13) is excluded as a failed measurement, not read as a negative result**: it returned C388 0.063 with c.871 undetected in both replicates. The reason is internal to the batch — a construct that had genuinely lost activity would not recover to 0.67 retention (an eight-fold recovery) on the addition of a single residue, and no position in this project has shown compensation of that magnitude; the same three substitutions measured 0.533 in D03. Only the exclusion is claimed here (a judgement about data usability), not the cause (a judgement about cause, which would require that transfection's wet-lab records). (iv) **Two exploratory routes were refuted**: both R28A-containing combinations gave an ROF below the parent (0.99 and 0.88), and in the anomalous-pairing group nothing beyond `130G-32F` produced any gain, with every 130G- or 131R-containing construct retaining ≤0.48 activity. By contrast, the two Group A single substitutions (M132D, I26N) reproduced their ROF almost exactly (1.04 → 1.07 and 1.04 → 1.04), while their absolute ratios were 1.15 and 1.12 here against 1.42 in the earlier batch — validating ROF normalisation and confirming that absolute ratios are not comparable across batches (the parental ratio runs 1.371 → 1.191 → 1.070 across the three batches). **One correction to the first draft of this document**: it inferred from C13 that combinations are more batch-sensitive than single substitutions, and listed repeated measurement as a gap on a par with the dose gradient. With C13 attributed to a failed well, that contrast does not hold — once the well is excluded, every construct measured twice reproduced, so there is currently no evidence that the constructs themselves are unstable. "
        ),
        figs=[("wiki_fig6_Cycle5_方法回溯.png", "图 5-1　AiCE β/γ 回溯检验", "Fig. 5-1  Retrospective test of the AiCE β/γ filter"),
              ("fig5_D组控制变量布局.png", "图 5-2　下一轮 D 组控制变量设计", "Fig. 5-2  Design of the control (Group D) variants"),
              ("fig6_候选总览.png", "图 5-3　下一轮候选总览", "Fig. 5-3  Overview of next-round candidates")],
        data=[
            ["逆折叠偏好方向", "MPNN 频率 vs +1 比 ρ = −0.499（负相关）；vs 活性保留 ρ = +0.060（无相关）"],
            ["致命假阴性", "活性前 14 名单点无一被提名；K30H 频率 0.000，模型会提名 K30T"],
            ["AiCE β/γ 过滤", "争议替换（H29P 0.771 / K30T 0.562 / N57D 0.875 / A59P 0.896）全部通过；18 个候选位点中 16 个为卷曲区"],
            ["监督学习", "可预测活性保留（r=0.613, p=0.005）；不可预测特异性（p=0.164）→ 两者由不同决定因素编码"],
            ["方法重评价（旁证）", "全部方法 top-5/top-10 回收率 p ≥ 0.685（可比样本仅 6–13，方差极大）"],
            ["记录核查", "四个「被 MPNN 强偏好但被功能数据否定」的替换在整理后的单点数据中均不存在，已改用本循环的计算回溯检验"],
            ["下一轮交付", "61 条候选（A 复验 18 / B 新单点 6 / C 新组合 12 / D 控制 5 / E 异常配对 20）"],
            ["待补对照", "本批全部为单一剂量；在等 on-target 效率下比较 +1 比的剂量梯度实验（0.25×–4×，n=3）未执行"],
            ["本批湿实验规模", "37 个突变组 + 2 个参照（PUF10/PUF12），77 个样本行；DP 可用记录均 ≥500"],
            ["D 组配对（132D vs 132E）", "同背景：25E-30H-58M-132D 保留 0.34（比 2.58）→ 25E-30H-58M-132E 保留 0.75（比 1.66）——M132D 破坏活性被直接测量证实"],
            ["最优组合（两批互证）", "27T-30H-58M 骨架：组合批 比 2.16 / 保留 0.77；本批 27T-30H-58M-132E 比 2.08 / 保留 0.67（ROF 1.95）——绝对 C388 0.520 → 0.533、C871 0.241 → 0.256，两批亲本基数相差 18% 的情况下复现"],
            ["孔剔除（非负结果）", "27T-30H-58M 本批所在孔 C388 0.063、C871 两次重复均未检出：判为测量失败予以剔除。理由是含其全部三个突变的 D03 测得 C388 0.533，失活构建体不会因增加一个残基而 8 倍回升"],
            ["被否证方向", "含 R28A 的组合 ROF 0.99 / 0.88，均低于亲本；异常配对组除 130G-32F 外全部无增益"],
            ["ROF 归一化验证", "M132D 1.04→1.07、I26N 1.04→1.04（绝对比 1.42 → 1.15 / 1.12）；亲本比值三批 1.371 → 1.191 → 1.070，绝对比值不可跨批"],
            ["本批亲本基线", "PUF12：C388 0.792 / C871 0.740 / 比 1.070（三批亲本比 1.371 → 1.191 → 1.070）"],
        ],
    ),

    dict(
        num=6,
        title_zh="迭代 6：换一个建库背景，三元组仍然浮到面板顶部——以及 27 位饱和",
        title_en="Iteration 6: In a different library background the triple still rises to the top — and position 27 saturated",
        overview_zh=(
            "问题：迭代 5 推出的最优骨架 27T-30H-58M 能否在独立批次中复现？−1 轴的 27 位还有多少空间？"
            "做法：在与前几批不同的建库背景下构建并测序 64 个样本（29 个组）——27 位饱和 10 个替换、"
            "六个位点的单点、4 个组合，以及 4 个靶向模块参照。"
            "结果：建库背景不同使**跨批的比值横比无效**，因此本轮只做批内比较（秩与帕累托结构不受背景影响）。"
            "在这个基础上三元组复现了：它在 25 个突变体中 ROF 排第 3（1.218），而且是唯一的帕累托枢纽点——"
            "保留率 ≥0.95 者中 ROF 最高、ROF ≥1.20 者中保留率最高（0.980）。"
            "同时 −1 层在批内复现：27 位 10 个替换中 7 个把 ACA 类底物压到检测线下，G27D 保留 0.990 活性。"
        ),
        overview_en=(
            "Question: does the leading scaffold from Iteration 5, 27T-30H-58M, replicate in an independent "
            "batch? And how much room is left at position 27 on the −1 axis? What we did: built and sequenced "
            "64 samples in 29 groups under a library background different from the earlier batches — a "
            "position-27 saturation of 10 substitutions, single substitutions at six positions, four "
            "combinations, and four targeting-module references. Result: the different library background makes "
            "**lateral comparison of ratio values across batches invalid**, so this round compares only within "
            "the batch, where ranks and Pareto structure are unaffected by the background. On that basis the "
            "triple replicated: it ranks third of 25 mutants by ROF (1.218) and is the panel's only pivotal "
            "Pareto point — the highest ROF among constructs retaining ≥0.95 activity and the highest retention "
            "among those reaching ROF ≥1.20 (0.980). The −1 layer also replicated within the batch: seven of "
            "the ten position-27 substitutions drive ACA-class editing below the detection floor, with G27D "
            "retaining 0.990 activity."
        ),
        design_zh=(
            "迭代 5 的结论全部建立在单次测量之上，而三元组 27T-30H-58M 的数字尤其如此：它在组合批给出 "
            "2.16 / 保留 0.77，其 132E 版本在补充批给出 2.08 / 保留 0.67。因此本轮的目的一是把这个构建体"
            "放进一个新批次里，看它相对面板的位置是否稳定。"
            "目的二是对 27 位做饱和：迭代 2–5 反复显示 −1 层是本项目最可靠的改造层，而它从未被饱和过"
            "（手里只有 G27D 与 G27T 两个点）。"
            "目的三是补上三个此前只能间接推断的量：M132E 与 M132D 的单点表现，以及靶向模块本身能否"
            "提供基序区分（用 PUF10、PUF12、PUF12-129Y、PUF12-129Y-132T 四个参照检验）。"
        ),
        design_en=(
            "Iteration 5's conclusions rested on single measurements, and none more so than the triple "
            "27T-30H-58M: 2.16 at 0.77 retention in the combinatorial batch, 2.08 at 0.67 retention for its "
            "132E version in the supplementary batch. The first aim of this round was therefore to place that "
            "construct in a fresh batch and see whether its position relative to the panel is stable. The "
            "second was to saturate position 27: Iterations 2–5 repeatedly showed the −1 layer to be the "
            "project's most reliable engineering handle, and it had never been saturated (we held only G27D "
            "and G27T). The third was to measure three quantities that had only been inferred indirectly — the "
            "single-substitution behaviour of M132E and M132D, and whether the targeting module itself can "
            "supply motif discrimination, tested with four PUF references."
        ),
        build_zh=(
            "**64 个样本、29 个同名组**：27 位饱和 10 个替换（D/E/I/L/M/P/Q/T/V/W），"
            "另加 25/26/29/30/132 五个位点的 11 个单点；4 个组合（25E-30H、27D-30H、30H-58M、27T-30H-58M）；"
            "以及 4 个参照组（PUF12 n=2、PUF10 n=6、PUF12-129Y、PUF12-129Y-132T）。"
            "分组规模为 27 组 n=2、1 组 n=4、1 组 n=6。"
            "测序深度全部可用：c.388 最小 1055、c.871 最小 1060、c.295 有记录者最小 1038，"
            "**无一条低于 DP 500**。c.295 在 29 个组中全部有记录，其中 32 个样本为「低于检测线」"
            "（源表记为 0）而非缺失值。"
            "**关键前提：本批的建库背景与前几批不同**，这是本轮只做批内比较的原因。"
        ),
        build_en=(
            "**64 samples in 29 groups**: a ten-substitution saturation at position 27 (D/E/I/L/M/P/Q/T/V/W), "
            "eleven further single substitutions at positions 25, 26, 29, 30 and 132, four combinations "
            "(25E-30H, 27D-30H, 30H-58M, 27T-30H-58M), and four reference groups (PUF12 n=2, PUF10 n=6, "
            "PUF12-129Y, PUF12-129Y-132T). Group sizes were 27 at n=2, one at n=4 and one at n=6. Read depth "
            "was usable throughout: minimum 1055 at c.388, 1060 at c.871 and 1038 at c.295, with **no record "
            "below DP 500**. All 29 groups carried c.295 records, 32 samples returning a below-detection "
            "reading (recorded as 0 in the source table) rather than a missing one. "
            "**Key premise: this batch was built in a different library background from the earlier ones**, "
            "which is why this round compares only within the batch."
        ),
        test_zh=(
            "**① 为什么不能横比。** 本批选择性最高的构建体比值也只有 1.33，而更早的面板产出过 1.71 的单点"
            "与 2.1 的组合——整个批次的选择性被压缩，这正是背景不同的直接表现。把本批的 1.278 与"
            "组合批的 2.156 或补充批的 2.083 相比，是在比较两套不同的构建体系，差异无法归因。"
            "**因此本稿不据此判定「复现失败」，也不做这种横比。**"
            "\n\n**② 批内秩与帕累托结构（本批唯一可承载结论的比较）。** 25 个突变体按 ROF 排序："
            "27I（1.267 / 保留 0.745）、27D-30H（1.227 / 0.783）、"
            "**27T-30H-58M（1.218 / 0.980）**、25E-30H（1.217 / 0.619）、27V（1.162 / 0.795）、"
            "30H-58M（1.146 / 1.005）、27E（1.140 / 0.794），其余 ROF ≤ 1.080。"
            "帕累托前沿（ROF 与保留率同时最大化）只有 6 个构建体，而三元组是其中的**枢纽点**："
            "**保留率 ≥0.95 者中它的 ROF 最高**（1.218，第二名 30H-58M 为 1.146，相差 6.3%）；"
            "**ROF ≥1.20 者中它的保留率最高**（0.980，其余三个为 0.745 / 0.783 / 0.619）。"
            "名义上排前两位的构建体，活性代价都远大于它。"
            "\n\n**③ 组分分解在本背景下同样成立。** 30H-58M 为 ROF 1.146 / 保留 1.005，"
            "加上 −1 层的 G27T 后变为 1.218 / 0.980——**用 2.5% 的活性换来 6.3% 的 ROF**，"
            "第三个替换不冗余，且两层各自独立起作用。"
            "\n\n**④ −1 层在批内复现。** 亲本 c.295 = 0.309；27 位 10 个替换中 7 个压到检测线下"
            "（27D/27E/27T/27V/27Q/27P/27W），G27D 保留 0.990 活性；四个组合也全部压到检测线下。"
            "\n\n**⑤ 27 位在 +1 轴上已饱和。** 7/10 的 ROF ≤ 1.06；有增益的 27I（1.267）、27V（1.162）、"
            "27E（1.140）都要付 20–25% 的活性代价。"
            "\n\n**⑥ 补上的直接测量。** M132E 单点保留 1.018（中性）、M132D 单点 0.915——"
            "而 M132D 在组合中把活性压到 0.34。靶向模块四个参照比值 1.049 / 0.952 / 1.036 / 0.997，"
            "全部 ≈1；PUF12-129Y-132T 把绝对活性提高 16% 而比值不动。"
            "\n\n**⑦ 一处需要留意的限定。** K30H 在本批没有保住名次：30H 的 ROF 为 1.050，"
            "在 25 个突变体中列第 14、21 个单点中列第 10。本批对比集合被 27 位饱和主导，"
            "因此这是提示性的——但不应把 K30H 作为 +1 层可读手柄的地位视为理所当然。"
        ),
        test_en=(
            "**① Why lateral comparison is not valid.** This batch's most selective construct reaches a ratio "
            "of only 1.33, where earlier panels produced single substitutions at 1.71 and combinations at 2.1 — "
            "the whole batch's selectivity is compressed, which is the direct signature of a different "
            "background. Comparing this batch's 1.278 with the combinatorial batch's 2.156 or the supplementary "
            "batch's 2.083 means comparing two different construct systems, and any difference is "
            "unattributable. **This document therefore does not read the round as a failure to reproduce, and "
            "does not make that comparison.** "
            "**② Within-batch rank and Pareto structure — the only comparison that can carry a conclusion "
            "here.** The 25 mutants by ROF: 27I (1.267 / 0.745 retention), 27D-30H (1.227 / 0.783), "
            "**27T-30H-58M (1.218 / 0.980)**, 25E-30H (1.217 / 0.619), 27V (1.162 / 0.795), 30H-58M "
            "(1.146 / 1.005), 27E (1.140 / 0.794), and the rest at ROF ≤ 1.080. Only six constructs lie on the "
            "Pareto front of ROF against retention, and the triple is its **pivotal point**: **the highest ROF "
            "among constructs retaining ≥0.95 activity** (1.218, against 1.146 for the next best, 30H-58M) and "
            "**the highest retention among those reaching ROF ≥1.20** (0.980 against 0.745 / 0.783 / 0.619). "
            "The two constructs nominally ranked above it pay far more activity for their rank. "
            "**③ The composition decomposition holds in this background too.** 30H-58M gives ROF 1.146 at "
            "1.005 retention; adding the −1-layer G27T moves it to 1.218 / 0.980 — **2.5% of activity for "
            "6.3% of ROF** — so the third substitution is not redundant and the two layers act independently. "
            "**④ The −1 layer replicated within the batch.** Parent c.295 = 0.309; seven of ten position-27 "
            "substitutions below the detection floor (27D/27E/27T/27V/27Q/27P/27W) with G27D retaining 0.990 "
            "activity; all four combinations likewise. "
            "**⑤ Position 27 is saturated on the +1 axis.** Seven of ten at ROF ≤ 1.06; the three that gain — "
            "27I (1.267), 27V (1.162), 27E (1.140) — all cost 20–25% activity. "
            "**⑥ Direct measurements added.** M132E retains 1.018 (neutral) and M132D 0.915 as single "
            "substitutions, while M132D in combination collapses activity to 0.34. The four targeting-module "
            "references give ratios 1.049 / 0.952 / 1.036 / 0.997, all ≈1; PUF12-129Y-132T raises absolute "
            "activity by 16% without moving the ratio. "
            "**⑦ One qualification.** K30H did not hold its rank: 30H gives ROF 1.050, fourteenth of 25 and "
            "tenth of the 21 single substitutions. The comparison set here is dominated by the position-27 "
            "saturation, so this is suggestive rather than conclusive — but K30H's standing as the +1 layer's "
            "readable handle should not be taken for granted."
        ),
        learn_zh=(
            "**本轮的价值在于把「哪些结论可以跨批、哪些只能批内」这条界线划清楚了。**"
            "\n\n**可以跨批的是秩，不是数值。** 建库背景一变，比值整体被压缩（本批最高 1.33），"
            "因此 2.16 / 2.08 / 1.278 这三个数只在各自的批次内有效。但**秩与帕累托结构不受背景影响**——"
            "而在这个尺度上，三元组复现了：它在换了一个建库背景的面板上仍然是枢纽点，"
            "保留率 ≥0.95 者中 ROF 最高、ROF ≥1.20 者中保留率最高。"
            "**一个在背景 A 里做出的设计决策，在背景 B 构建的面板上仍落在最前面，这是对设计决策的实质支持。**"
            "\n\n**组分分解在本批也成立**：加入 G27T 用 2.5% 的活性换 6.3% 的 ROF，"
            "说明第三个位点不冗余、且 −1 与 +1 两层各自独立起作用——这是分层模型的一次干净验证。"
            "\n\n**−1 层仍然是最可靠的成果**：G27D 等 7 个 27 位替换把 ACA 压到检测线下、"
            "G27D 保留 0.990 活性，且这是批内比较，不受背景影响。"
            "\n\n**27 位在 +1 轴上已饱和**：7/10 等于亲本，有增益的三个都付 20–25% 活性。"
            "同一个位点能决定性地改变 ACA 类编辑、却几乎不改变 GCG/GCA 编辑，"
            "这是分层模型最直接的一次验证。"
            "\n\n**两条需要继续跟进的限定**：① K30H 在本批落到中游，"
            "它在 +1 层的地位需要再确认；② 剂量梯度实验仍未执行，且今后应当与**同一背景下**的多批重复"
            "一起做，每批内含内部对照——否则无法把背景效应与剂量效应分开。"
        ),
        learn_en=(
            "**What this round contributes is a clearer line between the conclusions that travel across "
            "batches and those that cannot.** "
            "**What travels is the rank, not the value.** Change the library background and the whole batch's "
            "selectivity compresses (this batch peaks at 1.33), so 2.16, 2.08 and 1.278 are each valid only "
            "inside their own batch. But **ranks and Pareto structure are unaffected by the background**, and "
            "on that scale the triple replicated: in a panel built in a different background it is still the "
            "pivotal point, the highest ROF among constructs retaining ≥0.95 activity and the highest "
            "retention among those reaching ROF ≥1.20. **A design decision made in background A still lands "
            "at the top of a panel built in background B, which is substantive support for the decision.** "
            "**The composition decomposition holds here too**: adding G27T trades 2.5% of activity for 6.3% of "
            "ROF, so the third substitution is not redundant and the −1 and +1 layers act independently — a "
            "clean corroboration of the layered model. "
            "**The −1 layer remains the most reliable result**: seven of the ten position-27 substitutions "
            "drive ACA-class editing below the detection floor with G27D retaining 0.990 activity, and this "
            "is a within-batch comparison unaffected by the background. "
            "**Position 27 is saturated on the +1 axis**: seven of ten equal the parent, and the three that "
            "gain all cost 20–25% activity. The same position decisively changes ACA-class editing while "
            "barely moving GCG/GCA editing — the most direct corroboration of the layered model in the "
            "project. "
            "**Two qualifications to carry forward**: (i) K30H fell to mid-pack in this batch, so its "
            "standing on the +1 layer needs re-confirming; (ii) the dose-gradient experiment remains "
            "outstanding and should from now on be run together with multi-batch replication **within one "
            "background**, each batch containing an internal control — otherwise the background effect and "
            "the dose effect cannot be separated."
        ),
        figs=[("figure_16_replication_saturation.png",
               "图 6-1　本批面板内的秩与帕累托结构，以及 27 位饱和",
               "Fig. 6-1  Within-batch rank and Pareto structure, and the position-27 saturation")],
        data=[
            ["本批规模", "64 个样本 / 29 个同名组（27 组 n=2、1 组 n=4、1 组 n=6）；DP 全部 >1000"],
            ["关键前提", "本批建库背景与前几批不同 → 比值不可跨批横比；本批只做批内比较"],
            ["选择性压缩的证据", "本批最高比值 1.33（27I），而更早面板有 1.71 的单点与 2.1 的组合"],
            ["三元组的批内位置", "25 个突变体中 ROF 第 3（1.218）；帕累托前沿 6 个构建体中的枢纽点"],
            ["枢纽点判据", "保留率 ≥0.95 者中 ROF 最高（1.218 对 1.146，+6.3%）；ROF ≥1.20 者中保留率最高（0.980 对 0.745/0.783/0.619）"],
            ["组分分解（本批）", "30H-58M 1.146/1.005 → 加 G27T 后 1.218/0.980：用 2.5% 活性换 6.3% ROF"],
            ["−1 层（批内复现）", "亲本 c.295 = 0.309；27 位 10 个替换中 7 个压到检测线下；G27D 保留 0.990 活性"],
            ["27 位饱和（+1 轴）", "7/10 的 ROF ≤ 1.06；有增益者 27I 1.267 / 27V 1.162 / 27E 1.140，保留率均 0.745–0.795"],
            ["M132E 单点（首次）", "保留 1.018、ROF 1.062——中性；M132D 单点保留 0.915，而组合中含 M132D 者活性 0.34"],
            ["靶向模块参照", "PUF12 1.049 / PUF10 0.952 / PUF12-129Y 1.036 / PUF12-129Y-132T 0.997——全部 ≈1"],
            ["需继续跟进 ①", "K30H 本批 ROF 1.050，25 个突变体中列第 14（21 个单点中第 10），名次未复现"],
            ["需继续跟进 ②", "剂量梯度实验未执行；今后应与同一背景下的多批重复一起做，每批含内部对照"],
        ],
    ),
]

OUTRO_ZH = (
    "六个循环连起来，回答的是同一个问题：这个脱氨酶靠什么认出它的底物，而这种识别里有多少是可以被改造的。"
    "每一轮都是干实验提出关于机制的、可证伪的预言，湿实验给出裁决："
    "一致的地方成为下一轮的地基，不一致的地方修正我们对这个酶的理解。"
    "六轮下来得到的图景是：底物选择性至少分布在三层上——RNA 结合与可及性（改它会改变脱靶谱，"
    "却不改变靶点效率）、−1 位识别（家族进化出的锚，也是唯一能被廉价改造的一层）、"
    "以及 +1 位容忍（本项目最初的目标，也是最不承重的一层）。"
    "+1 位的区分不是这个家族进化出来的性状：接触分解显示这一层没有读取元件，"
    "阴性对照显示我们的替换并不重塑界面，逆折叠与结构约束模型显示天然序列分布也不是围绕它组织的——"
    "三条彼此独立的路线指向同一个结论。"
    "工程上的产出，第六个循环让我们能把它讲准确：**在一个建库背景里做出的跨层设计决策，"
    "在另一个背景里构建的面板上仍然落在最前面**——组合 27T-30H-58M 在换背景的复测中仍是其批次的"
    "帕累托枢纽点（保留率 ≥0.95 者中 ROF 最高、ROF ≥1.20 者中保留率最高），"
    "其组分分解也成立（加入 27T 用 2.5% 活性换 6.3% ROF）。"
    "−1 层的 G27D 在两个批次中都把 ACA 类底物压到检测线下、活性代价可忽略，是本项目最可靠的改造。"
    "与此同时，27 位饱和显示 +1 轴已用尽：10 个替换中 7 个等于亲本，有增益的三个都要付 20–25% 活性。"
    "**关于可比性需要说清楚一条方法论**：建库背景不同的批次之间不能横比比值，"
    "因此 2.16 / 2.08 / 1.278 各自只在批内有效；可以跨批传递的是**秩**，而秩层面的结论已经稳定。"
    "尚存的缺口：剂量梯度实验仍未执行，K30H 在 +1 层的地位需要再确认——"
    "而今后这两件事都应当在**同一建库背景**下、每批含内部对照地去做。"
)


OUTRO_EN = (
    "All six cycles answer one question: what does this deaminase actually recognise in its substrate, and "
    "how much of that recognition can be engineered? Each round has the dry work state a falsifiable "
    "mechanistic prediction and the wet work deliver the verdict — agreement becomes the foundation of the "
    "next round, disagreement corrects our understanding of the enzyme. The picture that emerges is this: "
    "substrate selectivity is distributed over at least three layers — RNA binding and accessibility "
    "(changing it rewrites the off-target spectrum without changing on-target efficiency), −1 recognition "
    "(the anchor the family evolved, and the only layer that can be engineered cheaply), and +1 tolerance "
    "(this project's original target, and the least load-bearing of the three). Discrimination at +1 is not "
    "a trait this family evolved: contact decomposition shows the layer has no reader, the negative controls "
    "show our substitutions do not remodel the interface, and the inverse-folding and structural-constraint "
    "models show the natural sequence distribution is not organised around it either — three mutually "
    "independent routes, one conclusion. "
    "The sixth cycle lets us state the engineering outcome precisely: **a cross-layer design decision made "
    "in one library background still lands at the top of a panel built in another** — the combination "
    "27T-30H-58M remains its batch's pivotal Pareto point (the highest ROF among constructs retaining ≥0.95 "
    "activity, and the highest retention among those reaching ROF ≥1.20), and its composition decomposition "
    "holds (adding 27T trades 2.5% of activity for 6.3% of ROF). The −1 layer's G27D drives ACA-class "
    "editing below the detection floor at negligible activity cost in two batches, the project's most "
    "reliable engineering result. At the same time the position-27 saturation shows the +1 axis is used up: "
    "seven of ten substitutions equal the parent, and the three that gain all cost 20–25% activity. "
    "**One methodological point about comparability needs stating**: ratiometric values cannot be compared "
    "laterally between batches built in different library backgrounds, so 2.16, 2.08 and 1.278 are each "
    "valid only within their own batch; what does travel across batches is the **rank**, and the rank-based "
    "conclusion is stable. Remaining gaps: the dose-gradient experiment has not been run, and K30H's "
    "standing on the +1 layer needs re-confirming — and both should from now on be addressed **within a "
    "single library background**, with internal controls in every batch."
)


# ===========================================================================
# 五个循环一览（每个循环一句话）
# ===========================================================================
GLANCE = [
    ("1", "+1 位有没有可改造的读取元件？",
     "102 个单点突变体；三组只差一个碱基的 RNA 底物 + 接触类型分解",
     "没有。这一层没有读取器，可改造性为零"),
    ("2", "特异性能否由作用于其他识别层的位点补上？",
     "50 个跨层双点/三点组合，含显式对照臂",
     "能部分补上（2.16 / 保留 77%），但比值与活性始终互相交换；结构域不是模块化的"),
    ("3", "酶靠什么挑位点？我们的评价标准对吗？",
     "57 个构建体、117 个样本；整段扩增子扫描",
     "选择性分布在三层；靶向比被检测下限污染，指标本身需要先被检验"),
    ("4", "我们改的到底是不是「界面」？",
     "7 个答案已知的对照 + 65 个纯蛋白建模任务",
     "不是。我们的替换不重塑界面；接触概率衡量的是「结合了哪条 RNA」"),
    ("5", "失败的计算路线，是数据不够还是方法不适用？",
     "三项彼此独立的回溯检验 + 37 个突变组的实测",
     "方法不适用。天然序列分布不围绕 +1 组织；实测确认最优骨架可复现"),
]
GLANCE_MD = "\n### 五个循环一览\n\n| 循环 | 提出的问题 | 关键做法 | 确立的结论 |\n|---|---|---|---|\n" + \
    "\n".join(f"| **{a}** | {b} | {c} | **{d}** |" for a, b, c, d in GLANCE) + \
    "\n\n五个循环共用同一个结构：干实验提出关于机制的、可证伪的预言，湿实验给出裁决；" \
    "一致的地方成为下一轮的地基，不一致的地方修正我们对这个酶的理解。\n"

# ===========================================================================
# 生成 DOCX
# ===========================================================================
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
st = doc.styles["Normal"]; st.font.name = CN; st.font.size = Pt(10.5)
st._element.rPr.rFonts.set(qn("w:eastAsia"), CN)


def _cn(run, size=None, bold=None, color=None):
    run.font.name = CN
    run._element.rPr.rFonts.set(qn("w:eastAsia"), CN)
    if size is not None: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if color is not None: run.font.color.rgb = RGBColor(*color)


def P(t, size=10.5, bold=False, color=(0x40, 0x40, 0x40), after=6):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.4
    r = p.add_run(t); _cn(r, size, bold, color); return p


def TBL(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""
        pp = c.paragraphs[0]; pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = pp.add_run(h); _cn(r, 9, True, (0xFF, 0xFF, 0xFF))
        from docx.oxml import OxmlElement
        sh = OxmlElement("w:shd"); sh.set(qn("w:fill"), "1F3B66")
        c._tc.get_or_add_tcPr().append(sh)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            pp = cells[i].paragraphs[0]
            r = pp.add_run(str(v)); _cn(r, 9, False, (0x40, 0x40, 0x40))
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


# 封面
doc.add_paragraph()
P("Orca 系统 · APOBEC 编辑模块", 22, True, NAVY, after=8)
P("DBTL 工程循环整理（Design – Build – Test – Learn）", 15, True, BLUE, after=10)
P("iGEM Wiki · Engineering Success 素材", 11, False, ACC, after=24)

# 简介
doc.add_heading("简介", 1)
P("中", 11, True, BLUE, after=4)
P(INTRO_ZH)
P("英", 11, True, BLUE, after=4)
P(INTRO_EN)

# 迭代
for c in CYCLES:
    doc.add_page_break()
    doc.add_heading(c["title_zh"], 1)
    doc.add_heading("概述 / Overview", 2)
    P(c["overview_zh"], color=BLUE); P(c["overview_en"], color=(0x60, 0x60, 0x60))
    doc.add_heading("设计 / Design", 2); P(c["design_zh"]); P(c["design_en"], color=(0x60, 0x60, 0x60))
    doc.add_heading("构建 / Build", 2); P(c["build_zh"]); P(c["build_en"], color=(0x60, 0x60, 0x60))
    doc.add_heading("测试 / Test", 2); P(c["test_zh"]); P(c["test_en"], color=(0x60, 0x60, 0x60))
    doc.add_heading("学习 / Learn", 2); P(c["learn_zh"]); P(c["learn_en"], color=(0x60, 0x60, 0x60))
    doc.add_heading("关键数据 / Key data", 2)
    TBL(["项目", "数值"], c["data"], widths=[6.4, 10.0])
    for fn, cap_zh, cap_en in c["figs"]:
        fp = next((os.path.join(d, fn) for d in FIGDIRS if os.path.exists(os.path.join(d, fn))), None)
        if fp:
            doc.add_picture(fp, width=Cm(15.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            P(cap_zh, 9, False, (0x80, 0x80, 0x80), after=2)
            P(cap_en, 8.5, False, (0xA0, 0xA0, 0xA0), after=10)

doc.add_page_break()
doc.add_heading("五个循环一览 / The five cycles at a glance", 1)
P("五个循环共用同一个结构：干实验提出关于机制的、可证伪的预言，湿实验给出裁决；一致的地方成为下一轮的地基，不一致的地方修正我们对这个酶的理解。", 10, False, (0x40, 0x40, 0x40))
_gt = doc.add_table(rows=1, cols=4)
_gt.style = "Light Grid Accent 1"
for _i, _h in enumerate(["循环", "提出的问题", "关键做法", "确立的结论"]):
    _gt.rows[0].cells[_i].text = _h
for _a, _b, _c, _d in GLANCE:
    _r = _gt.add_row().cells
    _r[0].text, _r[1].text, _r[2].text, _r[3].text = _a, _b, _c, _d
doc.add_page_break()
doc.add_heading("五个循环的整体收获 / Overall takeaway", 1)
P(OUTRO_ZH); P(OUTRO_EN, color=(0x60, 0x60, 0x60))

doc.save(DOCX)
print(f"写入 {DOCX}")

# ===========================================================================
# 生成 Markdown
# ===========================================================================
L = []
L.append("# Orca 系统 · APOBEC 编辑模块 —— DBTL 工程循环整理\n")
L.append("> iGEM Wiki · Engineering Success 素材（Design – Build – Test – Learn）\n")
L.append("## 简介\n\n**中**\n\n" + INTRO_ZH + "\n\n**英**\n\n" + INTRO_EN + "\n")
for c in CYCLES:
    L.append(f"\n---\n\n## {c['title_zh']}\n\n### 概述 / Overview\n\n{c['overview_zh']}\n\n{c['overview_en']}\n")
    L.append(f"### 设计 / Design\n\n{c['design_zh']}\n\n{c['design_en']}\n")
    L.append(f"### 构建 / Build\n\n{c['build_zh']}\n\n{c['build_en']}\n")
    L.append(f"### 测试 / Test\n\n{c['test_zh']}\n\n{c['test_en']}\n")
    L.append(f"### 学习 / Learn\n\n{c['learn_zh']}\n\n{c['learn_en']}\n")
    L.append("**关键数据 / Key data**\n")
    L.append("| 项目 | 数值 |\n|---|---|")
    for k, v in c["data"]:
        L.append(f"| {k} | {v} |")
    L.append("")
    for fn, cz, ce in c["figs"]:
        L.append(f"![{cz}](results/figs/{fn})\n\n*{cz} / {ce}*\n")
L.append(GLANCE_MD)
L.append("\n---\n\n## 五个循环的整体收获 / Overall takeaway\n\n" + OUTRO_ZH + "\n\n" + OUTRO_EN + "\n")
open(MD, "w", encoding="utf-8").write("\n".join(L))
print(f"写入 {MD}")

# ===========================================================================
# 生成 XLSX
# ===========================================================================
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    wb = Workbook(); ws = wb.active; ws.title = "DBTL各循环关键数据"
    ws.append(["Cycle", "阶段", "项目", "数值"])
    for c in CYCLES:
        for stage, zn, en in [("Design", c["title_zh"].split("：")[0], ""),
                              ("", c["title_zh"].split("：")[-1], "")]:
            pass
        ws.append([f"Cycle {c['num']}", c["title_zh"].split("：")[-1], "", ""])
        for k, v in c["data"]:
            ws.append(["", "", k, v])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F3B66")
        cell.alignment = Alignment(horizontal="center")
    for col, w in zip("ABCD", [10, 34, 26, 62]):
        ws.column_dimensions[col].width = w

    ws2 = wb.create_sheet("实验规模总览")
    ws2.append(["DBTL 循环", "干实验（计算）", "湿实验（构建/测试）", "湿实验规模"])
    for row in [
        ["Cycle 1", "生物学问题：+1 位有没有读取元件？AF3 三底物复合物建模；接触类型分解（侧链/主链 × 碱基/糖磷酸）；保守性/PSSM",
         "单点突变质粒构建 + 转染 + 扩增子深度测序", "102 个单点 / 205 样本（n=2）"],
        ["Cycle 2", "生物学问题：识别分层的可改造性是否对等？跨层组合设计；−1 层与 +1 层效应对比",
         "组合突变质粒构建 + 同批转染与测序", "50 个组合 / 100 样本行"],
        ["Cycle 3", "生物学问题：酶究竟靠什么挑位点？全扩增子逐位点编辑谱；47 个 GCG 位点同上下文检验",
         "57 个构建体扩增子深度测序；P 域变体；转录组重分析", "117 个样本 / 951 bp 扩增子"],
        ["Cycle 4", "生物学问题：我们的替换有没有重塑界面？D_M 马氏距离；WT-only 白化基；纯蛋白 AF3 对照",
         "阴性对照构建体回溯挑选 + AF3 建模", "7 个对照构建体"],
        ["Cycle 5", "生物学问题：天然序列分布是否围绕 +1 组织？逆折叠偏好方向；监督学习；AiCE β/γ 回溯检验",
         "（下一轮）61 条候选 + 剂量梯度实验设计", "61 条候选（设计完成）"],
    ]:
        ws2.append(row)
    for cell in ws2[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F3B66")
        cell.alignment = Alignment(horizontal="center", wrap_text=True)
    for col, w in zip("ABCD", [12, 52, 46, 30]):
        ws2.column_dimensions[col].width = w
    for r in ws2.iter_rows(min_row=2):
        for c in r:
            c.alignment = Alignment(wrap_text=True, vertical="top")

    wb.save(XLSX)
    print(f"写入 {XLSX}")
except ImportError:
    print("(未安装 openpyxl，跳过 XLSX)")
