# =============================================================================
# 哔哩哔哩知识区非金钱激励机制研究
# 脚本二：数据清洗、指标构建与回归数据生成
#
# 作者：[作者姓名]
# 单位：[学校/院系]
#
# 输入文件：step1_raw_data.xlsx（脚本一输出）
# 输出文件：step2_regression_data.xlsx（供 Stata 直接导入）
#
# 核心步骤：
#   1. 数据清洗与过滤
#   2. 内容质量指数（CQI）构建 — CRITIC 客观赋权法
#   3. 变量对数化处理
#   4. 滞后二期变量生成
#   5. 机制分析辅助变量（ln_interval、ln_comment、ln_share）
# =============================================================================

import pandas as pd
import numpy as np
import os

# =============================================================================
# 第一部分：配置
# =============================================================================

INPUT_FILE  = "step1_raw_data.xlsx"
OUTPUT_FILE = "step2_regression_data.xlsx"

# 数据清洗阈值（依据第四章4.2.1节）
MIN_VIEW     = 500     # 最低播放量，剔除长尾噪音视频
MIN_DURATION = 60      # 最短时长（秒），剔除非知识类极短内容
DATE_START   = "2019-03-01"  # 样本起始时间（知识区正式独立运营节点）
DATE_END     = "2025-12-31"  # 样本截止时间

# =============================================================================
# 第二部分：CRITIC 客观赋权法
# =============================================================================

def critic_weight(data: pd.DataFrame) -> pd.Series:
    """
    CRITIC（CRiteria Importance Through Intercriteria Correlation）
    客观赋权法（Diakoulaki, 1995）。

    算法步骤：
        1. Min-Max 归一化，统一量纲；
        2. 计算各指标标准差，衡量对比强度（波动性越大，信息量越高）；
        3. 计算指标间皮尔逊相关系数矩阵，
           冲突性 = sum(1 - r_ij)（与其他指标相关性越低，独立信息越多）；
        4. 信息量 C_j = σ_j × Σ(1 - r_ij)；
        5. 权重 w_j = C_j / Σ C_j。

    Parameters
    ----------
    data : pd.DataFrame
        待赋权指标矩阵，列为各指标，行为样本观测。

    Returns
    -------
    pd.Series
        各指标权重，索引与 data 列名一致，权重之和为 1。

    References
    ----------
    Diakoulaki, D., Mavrotas, G., & Papayannakis, L. (1995).
    Determining objective weights in multiple criteria problems:
    The CRITIC method. *Computers & Operations Research*, 22(7), 763–770.
    """
    # Step 1: Min-Max 归一化
    data_norm = (data - data.min()) / (data.max() - data.min())

    # Step 2: 对比强度（标准差）
    std = data_norm.std()

    # Step 3: 冲突性（相关矩阵列加总）
    corr      = data_norm.corr()
    conflict  = (1 - corr).sum()

    # Step 4: 信息量
    C = std * conflict

    # Step 5: 归一化权重
    return C / C.sum()

# =============================================================================
# 第三部分：数据清洗
# =============================================================================

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    执行数据清洗，生成供指标构建使用的中间数据集。

    清洗规则：
        (1) 剔除播放量 < MIN_VIEW 的低曝光噪音视频；
        (2) 剔除时长 < MIN_DURATION 的非知识类极短视频；
        (3) 剔除缺失 sentiment_score 的视频（弹幕采集失败）；
        (4) 按样本时间窗口过滤；
        (5) 按 UP 主（mid）和发布时间（pubdate）升序排序，
            为后续滞后项构造做准备。

    Parameters
    ----------
    df : pd.DataFrame
        原始采集数据（step1_raw_data.xlsx）。

    Returns
    -------
    pd.DataFrame
        清洗后的数据集。
    """
    n0 = len(df)
    df = df.copy()

    # 时间格式统一
    df["pubdate"] = pd.to_datetime(df["pubdate"])

    # (1) 时间窗口过滤
    df = df[(df["pubdate"] >= DATE_START) & (df["pubdate"] <= DATE_END)]

    # (2) 播放量过滤
    df = df[df["view"] >= MIN_VIEW]

    # (3) 时长过滤
    df = df[df["duration"] >= MIN_DURATION]

    # (4) 剔除情感得分缺失行
    df = df[pd.notna(df["sentiment_score"])]

    # (5) 按 UP 主和发布时间排序
    df = df.sort_values(["mid", "pubdate"]).reset_index(drop=True)

    print(f"  数据清洗：{n0} → {len(df)} 条（剔除 {n0 - len(df)} 条）")
    return df

# =============================================================================
# 第四部分：内容质量指数（CQI）构建
# =============================================================================

def build_quality_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    基于 CRITIC 客观赋权法构建内容质量指数（Content Quality Index, CQI）。

    两个维度：
        - 币播比（coin_ratio）：投币数 / 播放量，刻画稀缺资源被认可程度；
          对数变换：ln(coin_ratio × 1000 + 1)，压缩右偏分布。
        - 弹幕情感（sentiment_score）：已在 [0, 1] 范围内，无需取对数。

    合成公式：
        CQI = (norm(coin_log) × w_coin + norm(sentiment) × w_sent) × 100

    取值范围：0—100 分。

    Parameters
    ----------
    df : pd.DataFrame
        含 coin、view、sentiment_score 列的清洗后数据。

    Returns
    -------
    pd.DataFrame
        追加 Quality_Index 列的数据集。
    """
    # 币播比对数变换（×1000 缩放防止数值过小，+1 防止 log(0)）
    coin_log  = np.log((df["coin"] / df["view"]) * 1000 + 1)
    sentiment = df["sentiment_score"]

    indicators = pd.DataFrame({
        "coin": coin_log,
        "sent": sentiment
    })

    # CRITIC 赋权
    weights = critic_weight(indicators)
    w_coin = weights["coin"]
    w_sent = weights["sent"]

    print(f"\n  CRITIC 赋权结果：")
    print(f"    币播比权重 = {w_coin:.4f}（{w_coin*100:.1f}%）")
    print(f"    弹幕情感权重 = {w_sent:.4f}（{w_sent*100:.1f}%）")
    print(f"    权重比例 = {w_coin/w_sent:.2f} : 1")

    # Min-Max 归一化后合成指数
    ind_norm = (indicators - indicators.min()) / (indicators.max() - indicators.min())
    df["Quality_Index"] = (
        ind_norm["coin"] * w_coin + ind_norm["sent"] * w_sent
    ) * 100

    return df

# =============================================================================
# 第五部分：变量构造
# =============================================================================

def build_variables(df: pd.DataFrame) -> pd.DataFrame:
    """
    构造用于面板回归的全部变量，包括：

    一、对数变换（ln(X+1) 处理右偏分布，+1 避免 log(0)）：
        ln_coin, ln_like, ln_fav, ln_view, ln_fans, ln_duration,
        ln_share, ln_comment

    二、滞后二期变量（基于 UP 主内部时间序列）：
        L2_ln_coin, L2_ln_like, L2_ln_fav
        注：采用二阶滞后（shift(2)）而非一阶，一方面控制内生性，
            另一方面符合创作者将激励内化为行为变化所需的实际周期；
            前两条视频因无法构造完整二阶滞后而在此步被剔除。

    三、机制分析辅助变量：
        ln_interval：相邻视频发布间隔天数的对数值（投入互惠机制中介）
        ln_comment ：评论总数的对数值（深度反馈机制中介）
        ln_share   ：分享数的对数值（流量信号证伪变量 H4）

    四、时间固定效应变量：
        year, month

    Parameters
    ----------
    df : pd.DataFrame
        含质量指数的清洗数据集。

    Returns
    -------
    pd.DataFrame
        含全部回归变量的最终数据集（已剔除滞后缺失行）。
    """
    df = df.copy()

    # -------------------------------------------------------------------------
    # (1) 对数变换
    # -------------------------------------------------------------------------
    for col, src in [
        ("ln_coin",     "coin"),
        ("ln_like",     "like"),
        ("ln_fav",      "favorite"),
        ("ln_view",     "view"),
        ("ln_fans",     "up_fans"),
        ("ln_duration", "duration"),
        ("ln_share",    "share"),
        ("ln_comment",  "reply"),      # reply = 评论总数
    ]:
        df[col] = np.log(df[src] + 1)

    # -------------------------------------------------------------------------
    # (2) 滞后二期变量（在同一 UP 主内部滚动，不跨 UP 主）
    # -------------------------------------------------------------------------
    for col in ["ln_coin", "ln_like", "ln_fav"]:
        df[f"L2_{col}"] = df.groupby("mid")[col].shift(2)

    # -------------------------------------------------------------------------
    # (3) 内容打磨周期（相邻视频发布间隔天数）
    #     ln_interval = ln(interval_days + 1)
    # -------------------------------------------------------------------------
    df["pubdate"] = pd.to_datetime(df["pubdate"])
    # 取同一 UP 主内前一条视频的发布日期
    df["prev_pubdate"] = df.groupby("mid")["pubdate"].shift(1)
    df["interval_days"] = (
        (df["pubdate"] - df["prev_pubdate"])
        .dt.total_seconds()
        .div(86400)                # 秒转天
        .clip(lower=0)             # 极少数数据异常导致负值，截断为 0
    )
    df["ln_interval"] = np.log(df["interval_days"] + 1)
    df.drop(columns=["prev_pubdate", "interval_days"], inplace=True)

    # -------------------------------------------------------------------------
    # (4) 时间固定效应变量
    # -------------------------------------------------------------------------
    df["year"]  = df["pubdate"].dt.year
    df["month"] = df["pubdate"].dt.month

    # -------------------------------------------------------------------------
    # (5) 剔除滞后缺失行（每位 UP 主前两条视频无法构造完整二阶滞后）
    # -------------------------------------------------------------------------
    n_before = len(df)
    df = df.dropna(subset=["L2_ln_coin", "L2_ln_like", "L2_ln_fav",
                            "Quality_Index"]).reset_index(drop=True)
    print(f"\n  滞后处理：剔除 {n_before - len(df)} 行（前两期缺失），"
          f"最终样本量 = {len(df)} 条")

    return df

# =============================================================================
# 第六部分：主程序
# =============================================================================

def main():
    print("=" * 60)
    print("变量构建流程启动")
    print(f"输入文件：{INPUT_FILE}")
    print("=" * 60)

    # 读取原始数据
    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(f"找不到输入文件：{INPUT_FILE}\n"
                                "请先运行 01_video_crawler.py")
    df = pd.read_excel(INPUT_FILE)
    print(f"\n读取成功，原始样本量：{len(df)} 条")

    # Step 1：数据清洗
    print("\n[Step 1] 数据清洗...")
    df = clean_data(df)

    # Step 2：内容质量指数构建
    print("\n[Step 2] CRITIC 赋权 — 内容质量指数构建...")
    df = build_quality_index(df)

    # Step 3：变量构造
    print("\n[Step 3] 变量对数化与滞后处理...")
    df = build_variables(df)

    # Step 4：输出最终数据
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n[完成] 回归数据已保存至：{OUTPUT_FILE}")

    # 描述性统计摘要
    key_vars = ["Quality_Index", "L2_ln_coin", "L2_ln_like", "L2_ln_fav",
                "ln_duration", "ln_view", "ln_fans", "ln_share",
                "ln_comment", "ln_interval"]
    existing = [v for v in key_vars if v in df.columns]
    print("\n主要变量描述性统计：")
    print(df[existing].describe().round(4).to_string())

    # 样本覆盖情况
    print(f"\n样本时间范围：{df['pubdate'].min().date()} — "
          f"{df['pubdate'].max().date()}")
    print(f"UP 主数量：{df['mid'].nunique()} 位")
    print(f"视频总条数：{len(df)} 条")

if __name__ == "__main__":
    main()
