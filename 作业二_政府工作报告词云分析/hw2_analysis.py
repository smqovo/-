"""2026年政府工作报告文本挖掘：清洗、分词、规范化、去停用词、词频与词性统计、TF-IDF关键词、词云
运行：python hw2_analysis.py <数据目录> <输出目录>
"""
import sys, re, json, collections
import jieba, jieba.posseg as pseg, jieba.analyse
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from wordcloud import WordCloud

DATA, OUT = sys.argv[1], sys.argv[2]
FIG = f"{OUT}/fig"
jieba.setLogLevel(60)
jieba.load_userdict(f"{DATA}/自定义词典.txt")

for f in ["/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
          "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"]:
    font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": ["Liberation Serif", "Noto Serif CJK SC"], "axes.unicode_minus": True,
                     "font.size": 10, "xtick.direction": "in", "ytick.direction": "in", "axes.linewidth": 0.8,
                     "savefig.dpi": 300, "legend.frameon": False})
WC_FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
W1, W2 = 6.3, 5.3

# ---------- 1. 读取与清洗 ----------
raw = open(f"{DATA}/2026年政府工作报告正文.txt", encoding="utf-8").read()
text = raw.replace("　", "").strip()
paras = [p.strip() for p in text.split("\n") if p.strip()]
PARTS = ["一、2025年工作回顾", "二、“十五五”时期主要目标和重大任务", "三、2026年经济社会发展总体要求和政策取向", "四、2026年政府工作任务"]
PART_SHORT = ["2025年工作回顾", "“十五五”目标任务", "2026年总体要求", "2026年工作任务"]
pos = [text.index(h) for h in PARTS] + [len(text)]
part_text = [text[pos[i]:pos[i + 1]] for i in range(4)]
han = lambda s: len(re.findall(r"[一-鿿]", s))
structure = [dict(部分=PART_SHORT[i], 汉字数=han(part_text[i]), 占比=han(part_text[i]) / han(text[pos[0]:])) for i in range(4)]

# 第四部分十项任务的篇幅
p4 = part_text[3]
TASKS = re.findall(r"（([一二三四五六七八九十]+)）([^。]+)。", p4)
tpos = [p4.index(f"（{k}）") for k, _ in TASKS]
end4 = p4.index("新的形势和任务")
tpos.append(end4)
tasks = [dict(序号=k, 任务=t, 汉字数=han(p4[tpos[i]:tpos[i + 1]])) for i, (k, t) in enumerate(TASKS)]

def clean(s):
    s = re.sub(r"[“”《》（）()「」]", "", s)
    s = s.replace("人工智能+", "人工智能")
    return s

# ---------- 2. 分词、规范化、停用词 ----------
stop_g = set(open(f"{DATA}/通用停用词.txt", encoding="utf-8").read().split())
stop_p = set(open(f"{DATA}/公文套语停用词.txt", encoding="utf-8").read().split())
NORMALIZE = {"十四五": "“十四五”", "十五五": "“十五五”"}   # 仅用于显示

def tokenize(s):
    out = []
    for w, f in pseg.cut(clean(s)):
        if not re.fullmatch(r"[一-鿿]+", w): continue   # 去除数字、字母、标点
        out.append((w, f))
    return out

all_tok = tokenize(text)
n_raw = len(all_tok)
tok1 = [(w, f) for w, f in all_tok if len(w) >= 2]                 # 去除单字
tok2 = [(w, f) for w, f in tok1 if w not in stop_g]                # 去除通用停用词
tok3 = [(w, f) for w, f in tok2 if w not in stop_p]                # 去除公文常用套语
pipeline = dict(原始词条=n_raw, 去除单字后=len(tok1), 去除通用停用词后=len(tok2), 去除公文套语后=len(tok3),
                词汇量=len(set(w for w, _ in tok3)))

freq = collections.Counter(w for w, _ in tok3)
top30 = freq.most_common(30)

# 词性分布（去除单字与通用停用词后，保留动词以观察文本的动作性）
POSMAP = {"n": "名词", "vn": "动名词", "v": "动词", "a": "形容词", "ad": "副形词", "d": "副词", "nz": "专有名词",
          "ns": "地名", "nr": "人名", "j": "简称", "l": "习用语", "b": "区别词", "m": "数词", "r": "代词"}
pos_c = collections.Counter(f for _, f in tok2)
pos_tbl = []
for f, c in pos_c.most_common():
    pos_tbl.append(dict(词性=POSMAP.get(f, "其他"), 标记=f, 词次=c, 占比=c / len(tok2)))
pos_df = pd.DataFrame(pos_tbl).groupby("词性", as_index=False).agg(词次=("词次", "sum"), 占比=("占比", "sum")).sort_values("词次", ascending=False)
pos_top = {k: [w for w, _ in collections.Counter(w for w, f in tok2 if f == k).most_common(8)] for k in ["v", "n", "vn"]}

# 预处理示例
EX = "深化拓展“人工智能+”，促进新一代智能终端和智能体加快推广，推动重点行业领域人工智能商业化规模化应用。"
ex_seg = [w for w, _ in pseg.cut(EX)]
ex_clean = [w for w, _ in tokenize(EX)]
ex_final = [w for w in ex_clean if len(w) >= 2 and w not in stop_g and w not in stop_p]

# ---------- 3. TF-IDF 关键词（jieba 自带 IDF 语料） ----------
jieba.analyse.set_stop_words(f"{DATA}/通用停用词.txt")
tfidf_text = " ".join(w for w, _ in tok3)
tfidf = jieba.analyse.extract_tags(tfidf_text, topK=20, withWeight=True)

# ---------- 4. 各部分高频词 ----------
part_freq = []
for s in part_text:
    tk = [w for w, _ in tokenize(s) if len(w) >= 2 and w not in stop_g and w not in stop_p]
    part_freq.append(collections.Counter(tk))
part_top = [pf.most_common(10) for pf in part_freq]

# ---------- 5. 图表 ----------
disp = lambda w: NORMALIZE.get(w, w)
# 图：高频词前20条形图
top20 = freq.most_common(20)[::-1]
fig, ax = plt.subplots(figsize=(W2, 4.6))
ax.barh([disp(w) for w, _ in top20], [c for _, c in top20], color="0.6", edgecolor="black", linewidth=0.5, height=0.65)
for i, (_, c) in enumerate(top20): ax.text(c + 1.5, i, str(c), va="center", fontsize=8.5)
ax.set_xlabel("词频"); ax.tick_params(axis="y", length=0); ax.set_xlim(0, max(c for _, c in top20) * 1.12)
fig.savefig(f"{FIG}/fig_top20.png", bbox_inches="tight"); plt.close(fig)

# 图：总体词云
def make_wc(fr, w=1600, h=900, n=150, seed=7):
    return WordCloud(font_path=WC_FONT, width=w, height=h, background_color="white", max_words=n,
                     prefer_horizontal=1.0, colormap="viridis", random_state=seed, margin=4,
                     relative_scaling=0.5).generate_from_frequencies({disp(k): v for k, v in fr.items()})
wc = make_wc(freq)
fig, ax = plt.subplots(figsize=(W1, W1 * 900 / 1600))
ax.imshow(wc, interpolation="bilinear"); ax.axis("off")
fig.savefig(f"{FIG}/fig_wordcloud.png", bbox_inches="tight", pad_inches=0.02); plt.close(fig)

# 图：四个部分词云
fig, axes = plt.subplots(2, 2, figsize=(W1, 4.2))
for k, (ax, pf) in enumerate(zip(axes.flat, part_freq)):
    ax.imshow(make_wc(pf, 1000, 620, 60, seed=3), interpolation="bilinear"); ax.axis("off")
    ax.set_title(f"({'abcd'[k]}) {PART_SHORT[k]}", fontsize=10)
fig.tight_layout(); fig.savefig(f"{FIG}/fig_wordcloud_parts.png", bbox_inches="tight"); plt.close(fig)

# 图：第四部分十项任务篇幅
td = pd.DataFrame(tasks)
lab = [f"（{r.序号}）{re.sub(r'^(着力|加紧|加快|持续|进一步|扎实|推动|更大力度|加强)', '', r.任务)}" for r in td.itertuples()]
fig, ax = plt.subplots(figsize=(W1, 3.6))
ax.barh(lab[::-1], td.汉字数[::-1], color="0.6", edgecolor="black", linewidth=0.5, height=0.65)
for i, v in enumerate(td.汉字数[::-1]): ax.text(v + 15, i, str(v), va="center", fontsize=8.5)
ax.set_xlabel("汉字数"); ax.tick_params(axis="y", length=0); ax.set_xlim(0, td.汉字数.max() * 1.12)
fig.savefig(f"{FIG}/fig_tasks.png", bbox_inches="tight"); plt.close(fig)

# ---------- 6. 导出 ----------
pd.DataFrame(freq.most_common(), columns=["词语", "词频"]).to_csv(f"{OUT}/词频表.csv", index=False, encoding="utf-8-sig")
res = dict(chars=len(raw.replace("　", "").replace("\n", "")), han=han(text), paras=len(paras),
           structure=structure, tasks=tasks, pipeline=pipeline, top30=top30, pos=pos_df.to_dict("records"),
           pos_top=pos_top, example=dict(raw=EX, seg=ex_seg, clean=ex_clean, final=ex_final),
           tfidf=tfidf, part_top=part_top, n_stop_g=len(stop_g), n_stop_p=len(stop_p),
           n_userdict=sum(1 for _ in open(f"{DATA}/自定义词典.txt", encoding="utf-8")),
           freq_sel={w: freq.get(w, 0) for w in ["发展", "建设", "经济", "改革", "创新", "科技", "消费", "投资", "就业", "民生", "安全", "风险",
                                                  "高质量发展", "新质生产力", "人工智能", "内需", "扩大内需", "绿色", "绿色低碳", "开放", "人才", "教育",
                                                  "产业", "企业", "市场", "政策", "养老", "医疗", "农村", "乡村", "粮食", "债务", "房地产", "金融"]},
           part_n=[sum(pf.values()) for pf in part_freq])
json.dump(res, open(f"{OUT}/results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: res[k] for k in ["chars", "han", "paras", "structure", "pipeline", "n_stop_g", "n_stop_p", "n_userdict"]}, ensure_ascii=False, indent=0, default=float))
print(top30); print(res["pos"][:10]); print(pos_top); print(tfidf); print(part_top); print(tasks); print(res["example"])
