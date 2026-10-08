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

# ---------- 绘图风格 ----------
font_manager.fontManager.addfont("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc")
plt.rcParams.update({
    "font.family": "WenQuanYi Zen Hei", "axes.unicode_minus": False,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.edgecolor": "#b8b7b2", "axes.labelcolor": "#52514e",
    "xtick.color": "#52514e", "ytick.color": "#52514e",
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6,
    "axes.axisbelow": True, "figure.facecolor": "white", "savefig.dpi": 200,
    "legend.frameon": False,
})
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
CLASSES = ["D1", "D2", "BD", "T1", "T2"]
CCOL = dict(zip(CLASSES, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
LEVELS = ["及格(60–70)", "中等(70–80)", "良好(80–85)", "优秀(≥85)"]
LCOL = ["#86b6ef", "#3987e5", "#256abf", "#104281"]   # 有序单色蓝阶
KCOL = ["#2a78d6", "#eb6834", "#1baf7a"]

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
    pr_fmt = "百分号文本(如 82.14%)" if df["通过率"].str.contains("%").any() else "小数文本(如 0.8)"
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
data["是否挂科"] = (data["不及格门次"] > 0).astype(int)
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
    "挂科人数": g["是否挂科"].sum(),
    "挂科率": g["是否挂科"].mean(),
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

def kmeans(Z, k, seeds=50):
    best = None
    for sd in range(seeds):
        rng = np.random.default_rng(sd)
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
names = {1: "A 学业优良组", 2: "B 稳定中等组", 3: "C 学业预警组"}
data["聚类"] = rank.map(names).values
cl_profile = data.groupby("聚类")[["学分加权平均分", "平均学分绩点", "不及格门次", "不及格学分", "通过率"]].mean()
cl_profile.insert(0, "人数", data.groupby("聚类").size())
cl_cross = pd.crosstab(data["班级"], data["聚类"]).loc[CLASSES]
warn_list = data[data["聚类"] == names[3]][["班级", "ID", "学分加权平均分", "平均学分绩点", "不及格门次", "不及格学分", "通过率"]].sort_values("学分加权平均分")

# =================== 图表 ===================
x = np.arange(5)
# 图1 各班加权平均分均值 + 95%CI
means = desc["均值"].astype(float); sd = desc["标准差"].astype(float); n = desc["样本数"].astype(int)
ci = stats.t.ppf(.975, n - 1) * sd / np.sqrt(n)
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.bar(x, means - 60, bottom=60, width=.56, color=[CCOL[c] for c in CLASSES], edgecolor="white", linewidth=2)
ax.errorbar(x, means, yerr=ci, fmt="none", ecolor=INK2, elinewidth=1.2, capsize=5)
for i, c in enumerate(CLASSES):
    ax.text(i, means[c] + ci[c] + .4, f"{means[c]:.2f}", ha="center", va="bottom", color=INK, fontsize=10, fontweight="bold")
ax.axhline(desc_all["均值"], color=MUTED, ls="--", lw=1)
ax.set_xlim(-.5, 5.15)
ax.text(4.35, desc_all["均值"], f"全体均值\n{desc_all['均值']:.2f}", ha="left", va="center", color=INK2, fontsize=9)
ax.set_xticks(x, [f"{c}\n(n={n[c]})" for c in CLASSES]); ax.set_ylim(60, 92); ax.set_ylabel("学分加权平均分")
ax.set_title("图1  各班学分加权平均分均值（误差线为95%置信区间）", loc="left"); ax.grid(axis="x", visible=False)
save(fig, "fig1_mean_bar")

# 图2 直方图小多图
bins = np.arange(60, 95.1, 2.5)
fig, axes = plt.subplots(1, 5, figsize=(12, 3), sharey=True, sharex=True)
for ax, c in zip(axes, CLASSES):
    s = g.get_group(c)["学分加权平均分"]
    ax.hist(s, bins=bins, color=CCOL[c], edgecolor="white", linewidth=1.5)
    ax.axvline(s.mean(), color=INK, lw=1.2); ax.axvline(s.median(), color=INK, lw=1.2, ls=":")
    ax.set_title(f"{c}  偏度 {s.skew():+.2f}", fontsize=10.5); ax.set_xlabel("加权平均分")
    ax.grid(axis="x", visible=False)
axes[0].set_ylabel("人数")
fig.suptitle("图2  各班学分加权平均分分布直方图（实线=均值，虚线=中位数，组距2.5分）", x=0.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout(); save(fig, "fig2_hist")

# 图3 成绩等级百分比堆叠条形图
fig, ax = plt.subplots(figsize=(8, 3.8))
left = np.zeros(5)
for lv, col in zip(LEVELS, LCOL):
    v = level_pct[lv].values
    ax.barh(x, v, left=left, color=col, edgecolor="white", linewidth=2, height=.62, label=lv)
    for i, (l, w) in enumerate(zip(left, v)):
        if w >= .07:
            ax.text(l + w / 2, i, f"{w:.0%}", ha="center", va="center", fontsize=9,
                    color="white" if col != LCOL[0] else INK)
    left += v
ax.set_yticks(x, CLASSES); ax.invert_yaxis(); ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(.5, 1.0), fontsize=9)
ax.set_title("图3  各班成绩等级构成（按学分加权平均分划分）", loc="left", pad=28); ax.grid(axis="y", visible=False)
save(fig, "fig3_levels")

# 图4 箱线图 + 散点 + 异常点标注
fig, ax = plt.subplots(figsize=(8, 4.6))
bp = ax.boxplot(groups, positions=x, widths=.5, patch_artist=True, showfliers=False,
                medianprops=dict(color=INK, lw=1.6), whiskerprops=dict(color=INK2), capprops=dict(color=INK2),
                boxprops=dict(linewidth=1, edgecolor=INK2))
for patch, c in zip(bp["boxes"], CLASSES):
    patch.set_facecolor(CCOL[c]); patch.set_alpha(.35)
rng = np.random.default_rng(0)
for i, c in enumerate(CLASSES):
    d = data[data["班级"] == c]
    jit = rng.uniform(-.13, .13, len(d))
    normal = ~d["箱线图异常"]
    ax.scatter(i + jit[normal], d["学分加权平均分"][normal], s=14, color=CCOL[c], edgecolor="white", linewidth=.6, zorder=3)
    ax.scatter(i + jit[~normal], d["学分加权平均分"][~normal], s=60, facecolor="white", edgecolor="#e34948", linewidth=2, zorder=4)
    for (_, r), jj in zip(d[~normal].iterrows(), jit[~normal]):
        ax.annotate(f"{r.ID} ({r.学分加权平均分:.2f})", (i + jj, r.学分加权平均分), xytext=(10, -3),
                    textcoords="offset points", fontsize=8.5, color=INK2)
ax.set_xticks(x, CLASSES); ax.set_ylabel("学分加权平均分"); ax.grid(axis="x", visible=False)
ax.set_title("图4  各班成绩箱线图（红圈=超出 Q1-1.5×IQR 的异常点）", loc="left")
save(fig, "fig4_box")

# 图5 挂科情况
fig, ax = plt.subplots(figsize=(7, 3.6))
fr = other["挂科率"]
ax.bar(x, fr, width=.56, color=[CCOL[c] for c in CLASSES], edgecolor="white", linewidth=2)
for i, c in enumerate(CLASSES):
    ax.text(i, fr[c] + .008, f"{fr[c]:.1%}\n{int(other.loc[c,'挂科人数'])}/{int(n[c])}人，{int(other.loc[c,'不及格门次合计'])}门次",
            ha="center", va="bottom", fontsize=8.8, color=INK)
ax.set_xticks(x, CLASSES); ax.set_ylim(0, .5); ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
ax.set_ylabel("有挂科学生占比"); ax.grid(axis="x", visible=False)
ax.set_title("图5  各班挂科率（至少1门不及格的学生占比）", loc="left")
save(fig, "fig5_fail")

# 图6 相关系数热力图
from matplotlib.colors import LinearSegmentedColormap
div = LinearSegmentedColormap.from_list("div", ["#e34948", "#f0efec", "#2a78d6"])
fig, ax = plt.subplots(figsize=(6.6, 5.4))
im = ax.imshow(corr.values, cmap=div, vmin=-1, vmax=1)
ax.set_xticks(range(len(num_cols)), num_cols, rotation=40, ha="right"); ax.set_yticks(range(len(num_cols)), num_cols)
for i in range(len(num_cols)):
    for j in range(len(num_cols)):
        v = corr.values[i, j]; ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                                       color="white" if abs(v) > .75 else INK)
ax.grid(False); ax.spines[:].set_visible(False)
fig.colorbar(im, ax=ax, shrink=.75, label="Pearson 相关系数")
ax.set_title("图6  各数值属性相关系数矩阵（全体178人）", loc="left")
save(fig, "fig6_corr")

# 图7 QQ 图：同专业两班对比
def qq(ax, a, b, ca, cb):
    qs = np.linspace(.02, .98, 25)
    qa, qb = np.quantile(g.get_group(a)["学分加权平均分"], qs), np.quantile(g.get_group(b)["学分加权平均分"], qs)
    lo, hi = 60, 93
    ax.plot([lo, hi], [lo, hi], color=MUTED, ls="--", lw=1)
    ax.scatter(qa, qb, s=26, color=CCOL[b], edgecolor="white", linewidth=.8, zorder=3)
    mid = np.quantile(g.get_group(a)["学分加权平均分"], .5), np.quantile(g.get_group(b)["学分加权平均分"], .5)
    ax.scatter(*mid, s=70, facecolor="none", edgecolor=INK, lw=1.4, zorder=4)
    ax.annotate("中位数", mid, xytext=(8, -14), textcoords="offset points", fontsize=8.5, color=INK2)
    ax.text(lo + 1, hi - 1.5, "y = x", color=MUTED, fontsize=8.5)
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.set_xlabel(f"{a} 班分位数"); ax.set_ylabel(f"{b} 班分位数")
fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
for ax, (a, b) in zip(axes, [("D1", "D2"), ("T1", "T2"), ("T1", "BD")]):
    qq(ax, a, b, CCOL[a], CCOL[b]); ax.set_title(f"{a} vs {b}", fontsize=11)
fig.suptitle("图7  分位数-分位数图（Q-Q plot）：点在 y=x 上方表示纵轴班级在该分位上成绩更高", x=.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout(); save(fig, "fig7_qq")

# 图8 平行坐标图：各班均值画像（Min-Max 归一化）
pc_cols = ["学分加权平均分", "平均学分绩点", "课程平均分", "通过率", "不及格门次", "不及格学分"]
pm = data.groupby("班级")[pc_cols].mean().loc[CLASSES]
pmn = (pm - pm.min()) / (pm.max() - pm.min())
fig, ax = plt.subplots(figsize=(9, 4.2))
for c in CLASSES:
    ax.plot(range(len(pc_cols)), pmn.loc[c], color=CCOL[c], lw=2, marker="o", ms=8, mec="white", mew=1.5)
    ax.text(len(pc_cols) - 1 + .12, pmn.loc[c].iloc[-1], c, color=INK, va="center", fontsize=9.5, fontweight="bold")
# 末端标签避让
ax.set_xticks(range(len(pc_cols)), pc_cols); ax.set_xlim(-.2, len(pc_cols) - .5)
ax.set_ylabel("Min-Max 归一化值（0=五班最低，1=五班最高）"); ax.grid(axis="y", visible=False)
for i in range(len(pc_cols)): ax.axvline(i, color="#d8d7d2", lw=1, zorder=0)
ax.legend([plt.Line2D([], [], color=CCOL[c], lw=2, marker="o") for c in CLASSES], CLASSES, ncol=5, loc="lower center", bbox_to_anchor=(.5, 1.0))
ax.set_title("图8  平行坐标图：五个班级的多维均值画像", loc="left", pad=26)
save(fig, "fig8_parallel")

# 图9 K 值选择
fig, ax1 = plt.subplots(1, 2, figsize=(9, 3.2))
ax1[0].plot(kscan.k, kscan.SSE, color=KCOL[0], lw=2, marker="o", ms=8, mec="white"); ax1[0].set_title("肘部法：簇内误差平方和 SSE", fontsize=10.5); ax1[0].set_xlabel("k")
ax1[1].plot(kscan.k, kscan["轮廓系数"], color=KCOL[0], lw=2, marker="o", ms=8, mec="white"); ax1[1].set_title("轮廓系数（越大越好）", fontsize=10.5); ax1[1].set_xlabel("k")
for a in ax1: a.axvline(K, color=MUTED, ls="--", lw=1); a.set_xticks(range(2, 7))
fig.suptitle("图9  K-means 聚类数 k 的选择", x=.01, ha="left", fontweight="bold", fontsize=12)
fig.tight_layout(); save(fig, "fig9_kscan")

# 图10 PCA 二维聚类散点
fig, ax = plt.subplots(figsize=(8, 4.8))
for j, nm in enumerate(sorted(names.values())):
    idx = (data["聚类"] == nm).values
    ax.scatter(pcs[idx, 0], pcs[idx, 1], s=40, color=KCOL[j], edgecolor="white", linewidth=1, label=f"{nm}（{idx.sum()}人）", zorder=3)
ax.legend(loc="lower left")
ax.set_xlabel(f"PC1：综合学业水平（解释方差 {expl[0]:.1%}）"); ax.set_ylabel(f"PC2（解释方差 {expl[1]:.1%}）")
ax.set_title("图10  PCA 降维后的 K-means 聚类结果（k=3）", loc="left")
save(fig, "fig10_cluster")

# 图11 聚类×班级构成
fig, ax = plt.subplots(figsize=(8, 3.6))
cp = cl_cross.div(cl_cross.sum(1), axis=0); left = np.zeros(5)
for j, nm in enumerate(sorted(names.values())):
    v = cp[nm].values
    ax.barh(x, v, left=left, color=KCOL[j], edgecolor="white", linewidth=2, height=.62, label=nm)
    for i, (l, w) in enumerate(zip(left, v)):
        if w >= .06: ax.text(l + w / 2, i, f"{int(cl_cross.loc[CLASSES[i], nm])}人", ha="center", va="center", fontsize=9, color="white" if j != 2 else INK)
    left += v
ax.set_yticks(x, CLASSES); ax.invert_yaxis(); ax.set_xlim(0, 1)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0)); ax.grid(axis="y", visible=False)
ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(.5, 1.0), fontsize=9)
ax.set_title("图11  各班学生在三个聚类中的分布", loc="left", pad=28)
save(fig, "fig11_cluster_by_class")

# 图12 不及格门次 vs 加权平均分（按聚类着色）
fig, ax = plt.subplots(figsize=(7.5, 4.2))
jit = rng.uniform(-.12, .12, len(data))
for j, nm in enumerate(sorted(names.values())):
    idx = (data["聚类"] == nm).values
    ax.scatter(data["不及格门次"][idx] + jit[idx], data["学分加权平均分"][idx], s=36, color=KCOL[j], edgecolor="white", linewidth=1, label=nm, zorder=3)
r = data["不及格门次"].corr(data["学分加权平均分"])
ax.set_xticks(range(5)); ax.set_xlabel("不及格门次"); ax.set_ylabel("学分加权平均分"); ax.legend(loc="upper right")
ax.set_title(f"图12  不及格门次与学分加权平均分（r = {r:.2f}）", loc="left")
save(fig, "fig12_scatter")

# =================== 导出 ===================
with pd.ExcelWriter(f"{OUT}/成绩数据_清洗后及分析结果.xlsx") as w:
    data.to_excel(w, sheet_name="清洗集成后数据", index=False)
    audit.to_excel(w, sheet_name="数据质量审查", index=False)
    desc.to_excel(w, sheet_name="描述统计_加权平均分")
    other.to_excel(w, sheet_name="其他指标")
    level_ct.to_excel(w, sheet_name="成绩等级人数")
    pairs.to_excel(w, sheet_name="两两比较", index=False)
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
