# -*- coding: utf-8 -*-
"""
阶段 50 —— 以 targeting_ratio 为适应度的监督学习预测（对标 Peng et al. 2026 Mol Cell 的 MLDE）

思路（照搬该文献的三条关键做法）：
  ① 适应度用「想要的 ÷ 不想要的」比值，而不是单项效率
  ② 评价用 NDCG / top-N 回收率，而不只是相关系数
  ③ 用留一交叉验证给出诚实的泛化估计

适应度定义：
  targeting_ratio = Σ_GCG% / Σ_nonGCG%      （等价于文献的 CC5/(GC4+unwanted)）
  同时训练 activity_retention 作为第二标签 —— 因为本数据中 ratio 与活性存在
  检测限混杂（低活性 → 脱靶测不到 → ratio 虚高），必须两个一起看。

特征：
  A. 已知突变 token 的 multi-hot（16 维）
  B. 突变的理化性质总变化（体积/疏水/电荷/极性/芳香 + 突变数）→ 可外推到训练集未见的新突变

产出：
  results/ML适应度_交叉验证.csv
  results/ML适应度_候选预测.csv
"""
import csv, sys, math, json, os, re
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
import numpy as np

# ---------------------------------------------------------------------------
# 氨基酸理化性质
# ---------------------------------------------------------------------------
VOL = {"G":60.1,"A":88.6,"S":89.0,"C":108.5,"D":111.1,"T":116.1,"N":114.1,"P":112.7,
       "E":138.4,"V":140.0,"Q":143.8,"H":153.2,"M":162.9,"I":166.7,"L":166.7,
       "K":168.6,"R":173.4,"F":189.9,"Y":193.6,"W":227.8}
KD  = {"A":1.8,"R":-4.5,"N":-3.5,"D":-3.5,"C":2.5,"Q":-3.5,"E":-3.5,"G":-0.4,"H":-3.2,
       "I":4.5,"L":3.8,"K":-3.9,"M":1.9,"F":2.8,"P":-1.6,"S":-0.8,"T":-0.7,"W":-0.9,
       "Y":-1.3,"V":4.2}
CHG = {"D":-1,"E":-1,"K":1,"R":1,"H":0.1}
POL = {"G":0.0,"A":0.0,"S":1.0,"C":0.0,"D":1.0,"T":1.0,"N":1.0,"P":0.0,"E":1.0,"V":0.0,
       "Q":1.0,"H":1.0,"M":0.0,"I":0.0,"L":0.0,"K":1.0,"R":1.0,"F":0.0,"Y":1.0,"W":0.0}
ARO = {"F":1,"Y":1,"W":1}
WT_SEQ = json.load(open("af3_submit/WT_GCG.json", encoding="utf-8"))[0]["sequences"][0]["proteinChain"]["sequence"]


def parse_variant(name):
    """兼容两种命名：
       训练集  '27T-30H-58M'      -> [(27,'T'),(30,'H'),(58,'M')]
       候选表  'G27T+K30H+Q58M'   -> [(27,'T'),(30,'H'),(58,'M')]
       'WT (PUF12-9)' / 'PUF12-9' -> []
    """
    if not name:
        return []
    s = str(name).split("→")[0]                      # 去掉 'W129Y→129W' 的箭头注释
    if "PUF12-9" in s or s.strip().upper().startswith("WT"):
        return []
    out = []
    for p in re.split(r"[+\-]", s):
        p = p.strip()
        if not p:
            continue
        m = re.match(r"^([A-Z])(\d+)([A-Z])$", p)    # K30H / M132D / G27D
        if m:
            out.append((int(m.group(2)), m.group(3))); continue
        m = re.match(r"^(\d+)([A-Z])$", p)           # 27T / 130G
        if m:
            out.append((int(m.group(1)), m.group(2))); continue
    return out


def prop_vec(muts):
    """理化性质总变化（可外推到训练集未见的突变）。"""
    dv = dk = dq = dp = 0.0; na = 0; big = 0
    for pos, new in muts:
        wt = WT_SEQ[pos - 1]
        dv += VOL[new] - VOL[wt]
        dk += KD[new] - KD[wt]
        dq += CHG.get(new, 0) - CHG.get(wt, 0)
        dp += POL[new] - POL[wt]
        na += ARO.get(new, 0) - ARO.get(wt, 0)
        if VOL[new] - VOL[wt] > 50: big += 1
    return np.array([dv, dk, dq, dp, na, len(muts), big], float)


# ---------------------------------------------------------------------------
# 数据
# ---------------------------------------------------------------------------
rows = []
for r in csv.DictReader(open("results/GCG_vs_off_ranking_WT.csv", encoding="utf-8-sig")):
    try:
        tr = float(r["targeting_ratio"])
    except Exception:
        continue
    if math.isinf(tr) or math.isnan(tr):
        continue
    if r["mutation"] in ("PUF12-9", "WT"):
        continue
    muts = parse_variant(r["mutation"])
    if not muts:
        continue
    rows.append(dict(name=r["mutation"], muts=muts, tr=tr,
                     act=float(r["activity_retention"] or 0),
                     c388=float(r["C388_pct"])))
import random
random.Random(0).shuffle(rows)          # CSV 本身按 ratio 降序，必须先打乱否则基线指标失真
print(f"可用训练样本 n = {len(rows)}（已剔除 inf/0-0 与 WT；行序已打乱）")

TOKENS = sorted({(p, a) for r in rows for p, a in r["muts"]})
TIDX = {t: i for i, t in enumerate(TOKENS)}
print(f"已知突变 token = {len(TOKENS)} 个")


def feat_multi(muts):
    v = np.zeros(len(TOKENS))
    for t in muts:
        if t in TIDX:
            v[TIDX[t]] += 1
    return v


def design(muts, mode):
    pm = feat_multi(muts)
    if mode == "multi":
        return pm
    if mode == "prop":
        return prop_vec(muts)
    return np.concatenate([pm, prop_vec(muts)])


# ---------------------------------------------------------------------------
# 指标（对标文献：NDCG、top-N 回收率、Spearman）
# ---------------------------------------------------------------------------
def pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    x = x - x.mean(); y = y - y.mean()
    d = math.sqrt((x ** 2).sum() * (y ** 2).sum())
    return float((x * y).sum() / d) if d > 0 else float("nan")


def spearman(x, y):
    def rk(v):
        s = np.argsort(np.asarray(v, float)); r = np.empty(len(v)); r[s] = np.arange(len(v))
        return r
    return pearson(rk(x), rk(y))


def ndcg_at(y_true, y_pred, k):
    """以 min-max 归一化后的真实适应度为相关度。"""
    yt = np.asarray(y_true, float)
    yt = (yt - yt.min()) / (np.ptp(yt) + 1e-12)
    order = np.argsort(-np.asarray(y_pred, float))[:k]
    ideal = np.argsort(-yt)[:k]
    disc = 1.0 / np.log2(np.arange(2, k + 2))
    dcg = float((yt[order] * disc).sum())
    idcg = float((yt[ideal] * disc).sum())
    return dcg / idcg if idcg > 0 else float("nan")


def topn_recovery(y_true, y_pred, n):
    yt = np.asarray(y_true, float)
    a = set(np.argsort(-np.asarray(y_pred, float))[:n])
    b = set(np.argsort(-yt)[:n])
    return len(a & b) / n


# ---------------------------------------------------------------------------
# 留一交叉验证
# ---------------------------------------------------------------------------
def kfold_preds(X, y, model_fn, n_splits=5, n_repeats=20, seed=0):
    """重复 K 折交叉验证，返回 (n_repeats, n) 的折外预测矩阵。

    为什么不用留一（LOO）：
      当模型被强正则化时，第 i 个样本的折外预测 pred_i 会塌缩到训练折标签的均值，
      而训练折 = 除 i 外的全部样本，故 pred_i ≈ (n·ȳ − y_i)/(n−1)，与 y_i 产生
      人为的负相关（极端情况下 corr = −1）。
      实测：LOO 的置换零分布中位 |r| 高达 0.59、10 次里有 8 次为负 —— 纯属伪影。
      K 折下每个折外预测依赖的是另外 80% 的样本，该伪影可忽略。
    """
    rng = np.random.default_rng(seed)
    out = np.zeros((n_repeats, len(y)))
    for r in range(n_repeats):
        idx = rng.permutation(len(y))
        for f in np.array_split(idx, n_splits):
            tr = np.ones(len(y), bool); tr[f] = False
            mu, sd = X[tr].mean(0), X[tr].std(0)
            sd = np.where(sd < 1e-9, 1.0, sd)
            m = model_fn()
            m.fit((X[tr] - mu) / sd, y[tr])
            out[r, f] = m.predict((X[f] - mu) / sd)
    return out


def cv_metrics(X, y, model_fn, **kw):
    """对每次重复分别算指标再取平均（避免把不同重复的折外预测混在一起）。"""
    P = kfold_preds(X, y, model_fn, **kw)
    return dict(pearson=float(np.mean([pearson(y, p) for p in P])),
                spearman=float(np.mean([spearman(y, p) for p in P])),
                ndcg10=float(np.mean([ndcg_at(y, p, 10) for p in P])),
                top5=float(np.mean([topn_recovery(y, p, 5) for p in P])),
                top10=float(np.mean([topn_recovery(y, p, 10) for p in P])))


def loo_cv(X, y, model_fn):        # 仅保留用于对照展示其伪影，不用于结论
    pred = np.zeros(len(y))
    for i in range(len(y)):
        tr = np.ones(len(y), bool); tr[i] = False
        mu, sd = X[tr].mean(0), X[tr].std(0)
        sd = np.where(sd < 1e-9, 1.0, sd)
        m = model_fn()
        m.fit((X[tr] - mu) / sd, y[tr])
        pred[i] = m.predict(((X[i] - mu) / sd)[None, :])[0]
    return pred


print("\n" + "=" * 104)
print("重复 5 折交叉验证（20 次重复；不用 LOO，理由见 kfold_preds 注释）")
print("=" * 104)
try:
    from sklearn.linear_model import RidgeCV
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    HAVE = True
except ImportError:
    HAVE = False

MODELS = {}
if HAVE:
    MODELS = {
        "Ridge（线性/加性）": lambda: RidgeCV(alphas=np.logspace(-1, 3, 20)),
        "随机森林": lambda: RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                                  random_state=0),
        "梯度提升": lambda: GradientBoostingRegressor(n_estimators=200, max_depth=2,
                                                      learning_rate=0.05, random_state=0),
    }

mode = "multi+prop"
X = np.array([design(r["muts"], mode) for r in rows])
y = np.array([r["tr"] for r in rows])
ya = np.array([r["act"] for r in rows])
rng = np.random.default_rng(0)

# 随机排序基线：把标签打乱后算指标，即为「无信号」的期望水平
def random_baseline(yy, n=200):
    out = {k: [] for k in ("pearson", "spearman", "ndcg10", "top5", "top10")}
    for _ in range(n):
        p = rng.permutation(yy)
        out["pearson"].append(pearson(yy, p)); out["spearman"].append(spearman(yy, p))
        out["ndcg10"].append(ndcg_at(yy, p, 10))
        out["top5"].append(topn_recovery(yy, p, 5)); out["top10"].append(topn_recovery(yy, p, 10))
    return {k: float(np.mean(v)) for k, v in out.items()}

HDR = f"{'模型':<22}{'Pearson':>9}{'Spearman':>10}{'NDCG@10':>9}{'top5回收':>10}{'top10回收':>11}"
CV, CVa = {}, {}
for lab, yy, store in [("targeting_ratio", y, CV), ("activity_retention", ya, CVa)]:
    print(f"\n---- 标签 = {lab} ----")
    print(f"特征模式 = {mode}，维度 = {X.shape[1]}，样本 = {X.shape[0]}")
    print(HDR)
    rb = random_baseline(yy)
    print(f"{'随机排序基线':<22}{rb['pearson']:>9.3f}{rb['spearman']:>10.3f}"
          f"{rb['ndcg10']:>9.3f}{rb['top5']:>10.2f}{rb['top10']:>11.2f}")
    for name, fn in MODELS.items():
        m = cv_metrics(X, yy, fn)
        store[name] = m
        print(f"{name:<22}{m['pearson']:>9.3f}{m['spearman']:>10.3f}"
              f"{m['ndcg10']:>9.3f}{m['top5']:>10.2f}{m['top10']:>11.2f}")

print("\n" + "-" * 104)
print("置换检验（200 次打乱标签，Ridge，重复 5 折）—— 实测相关是否只是偶然")
PERM = {}
for lab, yy in [("targeting_ratio", y), ("activity_retention", ya)]:
    obs = cv_metrics(X, yy, lambda: RidgeCV(alphas=np.logspace(-1, 3, 20)))["pearson"]
    null = []
    for _ in range(200):
        yp = rng.permutation(yy)
        null.append(cv_metrics(X, yp, lambda: RidgeCV(alphas=np.logspace(-1, 3, 20)))["pearson"])
    null = np.array(null)
    pv = (1 + int((np.abs(null) >= abs(obs)).sum())) / (1 + len(null))
    PERM[lab] = pv
    print(f"  {lab:<20} 实测 r = {obs:+.3f}　置换零分布 |r| 中位 = {np.median(np.abs(null)):.3f}，"
          f"95 分位 = {np.percentile(np.abs(null), 95):.3f}　→ p = {pv:.3f}")

# ---------------------------------------------------------------------------
# 预测候选表
# ---------------------------------------------------------------------------
print("\n" + "=" * 104)
print("预测「下一步实验突变候选表 61 组」")
print("=" * 104)
CAND = []
try:
    from openpyxl import load_workbook
    wb = load_workbook("results/下一步实验突变候选表_61组.xlsx")
    for r in list(wb.worksheets[0].iter_rows(values_only=True))[1:]:
        CAND.append(dict(no=r[0], grp=r[1], mut=r[2], site=r[3]))
except Exception as e:
    print("读不到候选表:", e)

known = set(TOKENS)
n_unseen = 0
for c in CAND:
    muts = parse_variant(c["mut"])
    c["muts"] = muts
    unseen = [f"{p}{a}" for p, a in muts if (p, a) not in known]
    c["unseen"] = unseen
    if unseen:
        n_unseen += 1
print(f"候选 {len(CAND)} 组；其中 {n_unseen} 组含训练集未见过的突变（外推）")

if CAND and HAVE:
    # 用全部数据训练最终模型
    mu, sd = X.mean(0), np.where(X.std(0) < 1e-9, 1.0, X.std(0))
    Xs = (X - mu) / sd
    Xc = np.array([design(c["muts"], mode) for c in CAND])
    Xcs = (Xc - mu) / sd
    mtr = RandomForestRegressor(n_estimators=500, min_samples_leaf=2, random_state=0).fit(Xs, y)
    mact = RandomForestRegressor(n_estimators=500, min_samples_leaf=2, random_state=0).fit(Xs, ya)
    # 用重复 5 折的折外预测估计预测不确定度（残差 SD）
    pk = kfold_preds(X, y, lambda: RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                                         random_state=0))
    pka = kfold_preds(X, ya, lambda: RandomForestRegressor(n_estimators=400, min_samples_leaf=2,
                                                           random_state=0))
    sdc = float(np.mean([math.sqrt(((y - p) ** 2).mean()) for p in pk]))
    sda = float(np.mean([math.sqrt(((ya - p) ** 2).mean()) for p in pka]))
    for c, x in zip(CAND, Xcs):
        c["pred_tr"] = float(mtr.predict(x[None, :])[0])
        c["pred_act"] = float(mact.predict(x[None, :])[0])
    print(f"  折外残差 SD：targeting_ratio = {sdc:.2f}，活性 = {sda:.2f}")
    print(f"\n{'编号':<6}{'分组':<16}{'突变':<22}{'预测ratio':>10}{'预测活性':>10}  训练集未见")
    for c in sorted(CAND, key=lambda z: -z["pred_tr"]):
        print(f"{c['no']:<6}{c['grp'][:14]:<16}{c['mut']:<22}{c['pred_tr']:>10.2f}"
              f"{c['pred_act']:>10.2f}  {'/'.join(c['unseen']) if c['unseen'] else '—'}")

# 导出
with open("results/ML适应度_交叉验证.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["label", "model", "pearson", "spearman", "ndcg@10", "top5_recovery",
                "top10_recovery", "perm_p"])
    for lab, store, yy in [("targeting_ratio", CV, y), ("activity_retention", CVa, ya)]:
        rb = random_baseline(yy)
        w.writerow([lab, "随机排序基线"] + [round(rb[k], 4) for k in
                   ("pearson", "spearman", "ndcg10", "top5", "top10")] + [""])
        for n, m in store.items():
            w.writerow([lab, n] + [round(m[k], 4) for k in
                       ("pearson", "spearman", "ndcg10", "top5", "top10")] + [round(PERM[lab], 4)])

if CAND and HAVE:
    with open("results/ML适应度_候选预测.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["编号", "分组", "突变", "预测_targeting_ratio", "预测_activity_retention",
                    "训练集未见的突变", "n_mut"])
        for c in sorted(CAND, key=lambda z: -z["pred_tr"]):
            w.writerow([c["no"], c["grp"], c["mut"], round(c["pred_tr"], 3),
                        round(c["pred_act"], 3), "/".join(c["unseen"]), len(c["muts"])])
print("\n写入 results/ML适应度_交叉验证.csv、results/ML适应度_候选预测.csv")
