"""五个班级成绩数据：预处理 + 描述性统计 + 可视化 + 数据挖掘（聚类/异常检测）
运行：python analysis.py <xlsx路径> <输出目录>
"""
import sys, json, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from scipy import stats
warnings.filterwarnings("ignore")

SRC, OUT = sys.argv[1], sys.argv[2]
FIG = f"{OUT}/fig"

# ---------- 绘图风格（matplotlib 默认配色 + 学术排版） ----------
for f in ["/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
          "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
          "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"]:
    font_manager.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": ["Liberation Serif", "Noto Serif CJK SC"],   # 西文 Times 类字体，中文宋体
    "mathtext.fontset": "stix", "axes.unicode_minus": True,
    "font.size": 10, "axes.labelsize": 10, "xtick.labelsize": 9.5, "ytick.labelsize": 9.5,
    "legend.fontsize": 9, "legend.frameon": False, "xtick.direction": "in", "ytick.direction": "in",
    "axes.linewidth": 0.8, "savefig.dpi": 300, "figure.dpi": 100,
})
CLASSES = ["D1", "D2", "BD", "T1", "T2"]
CCOL = dict(zip(CLASSES, plt.rcParams["axes.prop_cycle"].by_key()["color"][:5]))
LEVELS = ["及格(60–70)", "中等(70–80)", "良好(80–85)", "优秀(≥85)"]

def save(fig, name):
    fig.savefig(f"{FIG}/{name}.png", bbox_inches="tight"); plt.close(fig)

# ---------- 1. 数据读取与审查 ----------
raw = pd.read_excel(SRC, sheet_name=None, dtype=str)
import openpyxl
_wb = openpyxl.load_workbook(SRC)
TEXT_CELLS = {ws.title: sum(isinstance(c.value, str) for r in ws.iter_rows(min_row=2, min_col=2) for c in r) for ws in _wb}
audit = []
frames = []
for cls, df in raw.items():
    first_col = df.columns[0]
    text_cells = TEXT_CELLS[cls]   # 以文本格式存储的数值单元格（Excel 中带绿色小三角）
    pr_fmt = "百分号文本(如 82.14%)" if df["通过率"].str.contains("%").any() else "数值型小数(单元格显示为百分比)"
    df = df.rename(columns={first_col: "ID"})
    d = df.copy()
    d["通过率"] = d["通过率"].str.rstrip("%").astype(float)
    if d["通过率"].max() > 1.5:
        d["通过率"] /= 100
    for c in d.columns[1:]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    audit.append(dict(
        班级=cls, 样本数=len(d), 首列列名=first_col, 学号示例=df.ID.iloc[0], 通过率格式=pr_fmt,
        文本型数值单元格=text_cells, 缺失值=int(d.isna().sum().sum()),
        重复学号=int(d.ID.duplicated().sum()), 重复记录=int(d.duplicated().sum()),
        学分恒等式不符=int((d["获得学分"] + d["不及格学分"] != d["总学分"]).sum()),
        通过率口径不符=int((abs(d["获得学分"] / d["总学分"] - d["通过率"]) > 0.006).sum()),
        越界值=int(((d["学分加权平均分"] < 0) | (d["学分加权平均分"] > 100) |
                    (d["平均学分绩点"] < 0) | (d["平均学分绩点"] > 5) |
                    (d["通过率"] < 0) | (d["通过率"] > 1)).sum()),
        标准总学分=int(d["总学分"].mode()[0]), 标准门数=int(d["门数"].mode()[0]),
        总学分非标准人数=int((d["总学分"] != d["总学分"].mode()[0]).sum()),
    ))
    d.insert(0, "班级", cls)
    frames.append(d)
audit = pd.DataFrame(audit)

# ---------- 2. 数据集成与变换 ----------
data = pd.concat(frames, ignore_index=True)                   # 集成：5 表纵向合并
data["课程平均分"] = data["总分"] / data["门数"]                # 消除门数不同带来的量纲差异
data["是否不及格"] = (data["不及格门次"] > 0).astype(int)
data["成绩等级"] = pd.cut(data["学分加权平均分"], [60, 70, 80, 85, 100.01],
                       labels=LEVELS, right=False)
for c in ["学分加权平均分", "总分", "课程平均分"]:
    data[f"{c}_MinMax"] = (data[c] - data[c].min()) / (data[c].max() - data[c].min())
    data[f"{c}_Z"] = (data[c] - data[c].mean()) / data[c].std()
data["班内Z分数"] = data.groupby("班级")["学分加权平均分"].transform(lambda s: (s - s.mean()) / s.std())

# ---------- 3. 描述性统计 ----------
def describe(s):
    m = s.mode()
    mode = "无（各值不重复）" if (s.value_counts().max() == 1) else "、".join(f"{v:.2f}" for v in m[:3])
    q1, q3 = s.quantile(.25), s.quantile(.75)
    return dict(样本数=len(s), 均值=s.mean(), 中位数=s.median(), 众数=mode,
                标准差=s.std(), 方差=s.var(), 最小值=s.min(), 最大值=s.max(), 极差=s.max() - s.min(),
                Q1=q1, Q3=q3, IQR=q3 - q1, 变异系数=s.std() / s.mean(),
                偏度=s.skew(), 峰度=s.kurt())
g = data.groupby("班级", sort=False)
desc = pd.DataFrame({c: describe(g.get_group(c)["学分加权平均分"]) for c in CLASSES}).T
desc_all = describe(data["学分加权平均分"])

other = pd.DataFrame({
    "平均学分绩点(均值)": g["平均学分绩点"].mean(),
    "课程平均分(均值)": g["课程平均分"].mean(),
    "不及格人数": g["是否不及格"].sum(),
    "不及格率": g["是否不及格"].mean(),
    "不及格门次合计": g["不及格门次"].sum(),
    "人均不及格学分": g["不及格学分"].mean(),
    "通过率(均值)": g["通过率"].mean(),
    "标准总学分": g["总学分"].agg(lambda s: s.mode()[0]),
    "标准门数": g["门数"].agg(lambda s: s.mode()[0]),
}).loc[CLASSES]
level_ct = pd.crosstab(data["班级"], data["成绩等级"]).loc[CLASSES, LEVELS]
level_pct = level_ct.div(level_ct.sum(1), axis=0)

# ---------- 4. 差异检验 ----------
groups = [g.get_group(c)["学分加权平均分"] for c in CLASSES]
shapiro = {c: stats.shapiro(s).pvalue for c, s in zip(CLASSES, groups)}
levene = stats.levene(*groups).pvalue
anova = stats.f_oneway(*groups)
kw = stats.kruskal(*groups)
eps2 = (kw.statistic - len(groups) + 1) / (len(data) - len(groups))   # Kruskal-Wallis 效应量 ε²
pairs = []
for i in range(5):
    for j in range(i + 1, 5):
        u = stats.mannwhitneyu(groups[i], groups[j], alternative="two-sided")
        pairs.append([CLASSES[i], CLASSES[j], groups[i].median() - groups[j].median(), u.pvalue])
pairs = pd.DataFrame(pairs, columns=["班级A", "班级B", "中位数差(A-B)", "p值"]).sort_values("p值")
m = len(pairs)  # Holm 校正
adj, running = [], 0
for k, p in enumerate(pairs["p值"]):
    running = max(running, min(1, p * (m - k))); adj.append(running)
pairs["Holm校正p值"] = adj
pairs["显著(α=0.05)"] = np.where(pairs["Holm校正p值"] < .05, "是", "否")

# ---------- 5. 异常检测（箱线图 1.5×IQR 规则，班内） ----------
def iqr_flags(s):
    q1, q3 = s.quantile(.25), s.quantile(.75); r = q3 - q1
    return (s < q1 - 1.5 * r) | (s > q3 + 1.5 * r), q1 - 1.5 * r
data["箱线图异常"] = False
fences = {}
for c in CLASSES:
    idx = data["班级"] == c
    f, lo = iqr_flags(data.loc[idx, "学分加权平均分"])
    data.loc[idx, "箱线图异常"] = f; fences[c] = lo
outliers = data[data["箱线图异常"]][["班级", "ID", "学分加权平均分", "平均学分绩点", "不及格门次", "不及格学分", "通过率", "班内Z分数"]]

# ---------- 6. 相关分析（冗余检测） ----------
num_cols = ["学分加权平均分", "平均学分绩点", "课程平均分", "总分", "获得学分", "不及格学分", "不及格门次", "通过率"]
corr = data[num_cols].corr()

# ---------- 7. 数据挖掘：PCA 降维 + K-means 聚类 ----------
feat = ["学分加权平均分", "平均学分绩点", "课程平均分", "不及格门次", "不及格学分", "通过率"]
X = data[feat].values
Xz = (X - X.mean(0)) / X.std(0, ddof=0)
evals, evecs = np.linalg.eigh(np.cov(Xz, rowvar=False))
order = evals.argsort()[::-1]; evals, evecs = evals[order], evecs[:, order]
if evecs[0, 0] < 0: evecs[:, 0] *= -1
if evecs[3, 1] < 0: evecs[:, 1] *= -1
pcs = Xz @ evecs[:, :2]
expl = evals / evals.sum()
loadings = pd.DataFrame(evecs[:, :2], index=feat, columns=["PC1", "PC2"])

def kmeans(Z, k, seeds=500):
    best = None
    for sd in range(seeds):
        rng = np.random.default_rng(sd)
        if sd % 2:   # 奇数次重启使用 k-means++ 初始化
            C = Z[[rng.integers(len(Z))]]
            while len(C) < k:
                d2 = ((Z[:, None] - C) ** 2).sum(-1).min(1)
                C = np.vstack([C, Z[rng.choice(len(Z), p=d2 / d2.sum())]])
        else:
            C = Z[rng.choice(len(Z), k, replace=False)]
        for _ in range(300):
            lab = ((Z[:, None] - C) ** 2).sum(-1).argmin(1)
            newC = np.array([Z[lab == j].mean(0) if (lab == j).any() else C[j] for j in range(k)])
            if np.allclose(newC, C): break
            C = newC
        sse = ((Z - C[lab]) ** 2).sum()
        if best is None or sse < best[0]: best = (sse, lab, C)
    return best
def silhouette(Z, lab):
    D = np.sqrt(((Z[:, None] - Z[None]) ** 2).sum(-1)); s = []
    for i in range(len(Z)):
        same = lab == lab[i]; a = D[i, same & (np.arange(len(Z)) != i)].mean() if same.sum() > 1 else 0
        b = min(D[i, lab == j].mean() for j in set(lab) if j != lab[i]); s.append((b - a) / max(a, b))
    return float(np.mean(s))
kscan = []
for k in range(2, 7):
    sse, lab, _ = kmeans(Xz, k); kscan.append(dict(k=k, SSE=sse, 轮廓系数=silhouette(Xz, lab)))
kscan = pd.DataFrame(kscan)
K = 3
_, lab, _ = kmeans(Xz, K)
# 按加权平均分高低给簇命名
rank = pd.Series(lab).map(data.groupby(lab)["学分加权平均分"].mean().rank(ascending=False).astype(int))
names = {1: "A 学业优良组", 2: "B 中等组", 3: "C 学业预警组"}
data["聚类"] = rank.map(names).values
cl_profile = data.groupby("聚类")[["学分加权平均分", "平均学分绩点", "不及格门次", "不及格学分", "通过率"]].mean()
cl_profile.insert(0, "人数", data.groupby("聚类").size())
cl_cross = pd.crosstab(data["班级"], data["聚类"]).loc[CLASSES]
warn_list = data[data["聚类"] == names[3]][["班级", "ID", "学分加权平均分", "平均学分绩点", "不及格门次", "不及格学分", "通过率"]].sort_values("学分加权平均分")

# =================== 图表 ===================
# 图宽按 Word 中的插入宽度设定（通栏 16 cm = 6.3 in，单栏 13.5 cm = 5.3 in），插入时不再缩放，图内字号与正文一致
W1, W2 = 6.3, 5.3
x = np.arange(5)
LV = ["优秀(≥85)", "良好(80–85)", "中等(70–80)", "及格(60–70)"]
MINUS = lambda t: t.replace("-", "−")
from decimal import Decimal, ROUND_HALF_UP
def hu(v, nd=0):   # 四舍五入（与正文口径一致）
    return str(Decimal(f"{v:.8f}").quantize(Decimal(1).scaleb(-nd), ROUND_HALF_UP))
CLN = sorted(names.values())
CLCOL = {CLN[0]: "tab:green", CLN[1]: "tab:blue", CLN[2]: "tab:red"}   # 与等级图一致：绿=优良，红=风险
CLMK = {CLN[0]: "o", CLN[1]: "s", CLN[2]: "^"}

# 各班均值及 95% 置信区间（误差条图）
means = desc["均值"].astype(float); sd = desc["标准差"].astype(float); n = desc["样本数"].astype(int)
ci = stats.t.ppf(.975, n - 1) * sd / np.sqrt(n)
fig, ax = plt.subplots(figsize=(W2, 3.0))
ax.errorbar(x, means, yerr=ci, fmt="o", color="black", ms=5, capsize=4, elinewidth=0.8, capthick=0.8)
for i, c in enumerate(CLASSES): ax.text(i + 0.1, means[c], hu(means[c], 2), ha="left", va="center", fontsize=9)
ax.axhline(desc_all["均值"], color="0.5", ls="--", lw=0.8)
ax.set_xticks(x); ax.set_xticklabels(CLASSES); ax.set_xlim(-0.5, 4.7); ax.set_ylim(70, 92); ax.set_yticks(range(70, 95, 5))
ax.set_xlabel("班级"); ax.set_ylabel("学分加权平均分")
save(fig, "fig1_mean_bar")

# 直方图（2×3 分面，第 6 格放图例）
bins = np.arange(60, 95.1, 2.5)
fig, axes = plt.subplots(2, 3, figsize=(W1, 3.9), sharex=True, sharey=True)
for ax, c in zip(axes.flat, CLASSES):
    s = g.get_group(c)["学分加权平均分"]
    ax.hist(s, bins=bins, color="0.75", edgecolor="black", linewidth=0.5)
    l1 = ax.axvline(s.mean(), color="black", lw=1.2, ls="-")
    l2 = ax.axvline(s.median(), color="black", lw=1.0, ls=(0, (3, 2)))
    ax.text(0.04, 0.92, c, transform=ax.transAxes, va="top", fontsize=10)
    ax.set_xticks([60, 70, 80, 90]); ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
axes[1, 2].axis("off"); axes[1, 2].legend([l1, l2], ["均值", "中位数"], loc="center")
fig.supxlabel("学分加权平均分", fontsize=10); fig.supylabel("人数", fontsize=10)
fig.tight_layout(); save(fig, "fig2_hist")

# 成绩等级构成（百分比堆积条形图，配色沿用课堂范例：优秀绿、良好蓝、中等黄、及格红）
lp = level_pct[LV[::-1]] * 100
lp.columns = ["及格[60,70)", "中等[70,80)", "良好[80,85)", "优秀[85,100]"]
ax = lp.plot(kind="barh", stacked=True, figsize=(W1, 3.0), width=0.6, edgecolor="black", linewidth=0.5,
             color=["tab:red", "gold", "tab:blue", "tab:green"])
fig = ax.get_figure()
ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("比例（%）"); ax.set_ylabel("班级"); ax.tick_params(axis="y", length=0)
ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0))
for cont in ax.containers:
    ax.bar_label(cont, labels=[hu(w) if w >= 7 else "" for w in cont.datavalues], label_type="center", fontsize=8.5)
save(fig, "fig3_levels")

# 箱线图
fig, ax = plt.subplots(figsize=(W2, 3.4))
ax.boxplot(groups, tick_labels=CLASSES, widths=0.5, medianprops=dict(color="black", lw=1.5),
           flierprops=dict(marker="o", markerfacecolor="none", markersize=5))
for i, c in enumerate(CLASSES):
    d = data[(data["班级"] == c) & data["箱线图异常"]].sort_values("学分加权平均分")
    for k, (_, r) in enumerate(d.iterrows()):
        ax.annotate(r.ID, (i + 1, r.学分加权平均分), xytext=(6, -6 if k == 0 and len(d) > 1 else 0), textcoords="offset points",
                    fontsize=8.5, va="center")
ax.set_xlabel("班级"); ax.set_ylabel("学分加权平均分")
save(fig, "fig4_box")

# 各班不及格率
fig, ax = plt.subplots(figsize=(W2, 2.9))
fr = other["不及格率"] * 100
bars = ax.bar(CLASSES, fr, width=0.55, color="0.75", edgecolor="black", linewidth=0.6)
ax.bar_label(bars, labels=[f"{hu(v, 1)}\n({int(other.loc[c, '不及格人数'])}/{int(n[c])})" for c, v in zip(CLASSES, fr)], padding=2, fontsize=8.5)
ax.set_ylim(0, 50); ax.set_xlabel("班级"); ax.set_ylabel("不及格率（%）")
save(fig, "fig5_fail")

# 相关系数矩阵
fig, ax = plt.subplots(figsize=(W2, 4.3))
im = ax.imshow(corr.values, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(num_cols))); ax.set_xticklabels(num_cols, rotation=45, ha="right")
ax.set_yticks(range(len(num_cols))); ax.set_yticklabels(num_cols); ax.tick_params(length=0)
for i in range(len(num_cols)):
    for j in range(len(num_cols)):
        v = corr.values[i, j]
        ax.text(j, i, MINUS(hu(v, 2)), ha="center", va="center", fontsize=8, color="white" if abs(v) > 0.6 else "black")
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04); cb.ax.tick_params(direction="out")
save(fig, "fig6_corr")

# Q-Q 图
PAIRS = [("D1", "D2"), ("T1", "T2"), ("T1", "BD")]
fig, axes = plt.subplots(1, 3, figsize=(W1, 2.55))
for k, (ax, (a, b)) in enumerate(zip(axes, PAIRS)):
    qs = np.linspace(.02, .98, 25)
    qa = np.quantile(g.get_group(a)["学分加权平均分"], qs); qb = np.quantile(g.get_group(b)["学分加权平均分"], qs)
    ax.plot([60, 93], [60, 93], "k--", lw=0.8)
    ax.plot(qa, qb, "o", color="black", markersize=3.5, markerfacecolor="none", markeredgewidth=0.7)
    ax.set_xlim(60, 93); ax.set_ylim(60, 93); ax.set_aspect("equal"); ax.set_xticks([60, 70, 80, 90]); ax.set_yticks([60, 70, 80, 90])
    ax.set_xlabel(f"{a}班分位数"); ax.set_ylabel(f"{b}班分位数"); ax.set_title(f"({'abc'[k]}) {a}与{b}", fontsize=10)
fig.tight_layout(); save(fig, "fig7_qq")

# 平行坐标图：每条折线为一名学生，按班级分面板（Min-Max 归一化，全体样本口径）
pc_cols = ["学分加权平均分", "平均学分绩点", "课程平均分", "通过率", "不及格门次"]
pcl = ["加权平均分", "绩点", "课程平均分", "通过率", "不及格门次"]
mm = (data[pc_cols] - data[pc_cols].min()) / (data[pc_cols].max() - data[pc_cols].min())
fig, axes = plt.subplots(1, 5, figsize=(W1, 2.7), sharey=True)
for ax, c in zip(axes, CLASSES):
    sub = mm[data["班级"] == c]
    for _, row in sub.iterrows(): ax.plot(range(len(pc_cols)), row.values, color=CCOL[c], lw=0.6, alpha=0.6)
    for v in range(len(pc_cols)): ax.axvline(v, color="black", lw=0.6)
    ax.set_xticks(range(len(pc_cols))); ax.set_xticklabels(pcl, rotation=90, fontsize=8.5); ax.tick_params(axis="x", length=0)
    ax.set_title(c, fontsize=10); ax.set_xlim(-0.2, len(pc_cols) - 0.8); ax.set_ylim(-0.03, 1.03)
axes[0].set_ylabel("归一化值")
fig.tight_layout(w_pad=0.6); save(fig, "fig8_parallel")

# K 值选择
fig, (a1, a2) = plt.subplots(1, 2, figsize=(W1, 2.4))
a1.plot(kscan.k, kscan.SSE, "o-", color="black", markersize=4, lw=1); a1.set_ylabel("SSE"); a1.set_title("(a) 肘部法", fontsize=10)
a2.plot(kscan.k, kscan["轮廓系数"], "o-", color="black", markersize=4, lw=1); a2.set_ylabel("轮廓系数"); a2.set_title("(b) 轮廓系数", fontsize=10)
for a in (a1, a2):
    a.set_xticks(range(2, 7)); a.set_xlabel("聚类数"); a.xaxis.label.set_text("聚类数 k"); a.axvline(3, color="0.5", ls="--", lw=0.8)
fig.tight_layout(); save(fig, "fig9_kscan")

# 各班聚类构成（百分比，条内数字为人数）
cp_ = cl_cross[CLN].div(cl_cross[CLN].sum(1), axis=0) * 100
ax = cp_.plot(kind="barh", stacked=True, figsize=(W1, 2.9), width=0.6, edgecolor="black", linewidth=0.5, color=[CLCOL[k] for k in CLN])
fig = ax.get_figure()
ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel("比例（%）"); ax.set_ylabel("班级"); ax.tick_params(axis="y", length=0)
ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.0))
for cont, k in zip(ax.containers, CLN):
    cnt = cl_cross.loc[CLASSES, k].values
    ax.bar_label(cont, labels=[f"{int(v)}" if v >= 2 else "" for v in cnt], label_type="center", fontsize=8.5)
save(fig, "fig11_cluster_by_class")

# 不及格门次与加权平均分散点图
fig, ax = plt.subplots(figsize=(W2, 3.2))
jit = np.random.default_rng(0).uniform(-0.1, 0.1, len(data))
for nm in CLN:
    idx = (data["聚类"] == nm).values
    ax.scatter(data["不及格门次"][idx] + jit[idx], data["学分加权平均分"][idx], s=14, marker=CLMK[nm],
               facecolors="none", edgecolors=CLCOL[nm], linewidths=0.8, label=nm)
ax.set_xticks(range(5)); ax.set_xlabel("不及格门次"); ax.set_ylabel("学分加权平均分")
ax.legend(loc="upper right")
save(fig, "fig12_scatter")

# =================== 导出 ===================
with pd.ExcelWriter(f"{OUT}/成绩数据_清洗后及分析结果.xlsx") as w:
    data.to_excel(w, sheet_name="清洗集成后数据", index=False)
    audit.to_excel(w, sheet_name="数据质量审查", index=False)
    desc.to_excel(w, sheet_name="描述统计_加权平均分")
    other.to_excel(w, sheet_name="其他指标")
    level_ct.to_excel(w, sheet_name="成绩等级人数")
    outliers.to_excel(w, sheet_name="异常点", index=False)
    corr.to_excel(w, sheet_name="相关系数")
    cl_profile.to_excel(w, sheet_name="聚类画像")
    cl_cross.to_excel(w, sheet_name="聚类×班级")
    warn_list.to_excel(w, sheet_name="学业预警名单", index=False)

res = dict(
    audit=audit.to_dict("records"), desc=desc.astype(object).to_dict("index"), desc_all=desc_all,
    other=other.to_dict("index"), level_ct=level_ct.to_dict("index"), level_pct=level_pct.to_dict("index"),
    shapiro=shapiro, levene=levene, anova=[anova.statistic, anova.pvalue], kw=[kw.statistic, kw.pvalue], eps2=eps2,
    pairs=pairs.to_dict("records"), outliers=outliers.to_dict("records"), fences=fences,
    corr=corr.round(3).to_dict(), expl=expl.tolist(), loadings=loadings.to_dict("index"),
    kscan=kscan.to_dict("records"), cl_profile=cl_profile.to_dict("index"), cl_cross=cl_cross.to_dict("index"),
    warn_list=warn_list.to_dict("records"), N=len(data),
    nonstd=data[(data["门数"] != data.groupby("班级")["门数"].transform(lambda s: s.mode()[0]))][["班级", "ID", "总学分", "门数", "总分", "课程平均分"]].to_dict("records"),
    rank_total_vs_wavg=dict(spearman=data["总分"].corr(data["学分加权平均分"], method="spearman"),
                            avg=data["课程平均分"].corr(data["学分加权平均分"])),
)
json.dump(res, open(f"{OUT}/results.json", "w"), ensure_ascii=False, indent=1, default=float)
print("done")
