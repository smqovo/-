# =============================================================================
# 哔哩哔哩知识区非金钱激励机制研究
# 脚本一：视频元数据采集与弹幕情感量化
#
# 作者：[作者姓名]
# 单位：[学校/院系]
# 数据采集周期：2019年3月—2025年12月
# 输出文件：step1_raw_data.xlsx
#
# 依赖库：requests, pandas, numpy, lxml, snownlp
# 安装命令：pip install requests pandas numpy lxml snownlp openpyxl
# =============================================================================

import requests
import pandas as pd
import numpy as np
import time
import random
import re
import os
import urllib.parse
import hashlib
from functools import reduce
from datetime import datetime
from lxml import etree
from snownlp import SnowNLP

# =============================================================================
# 第一部分：全局配置
# =============================================================================

# ------------------------------------------
# 1.1 身份认证
# 请将 SESSDATA 替换为有效的 B 站登录 Cookie
# 获取方法：浏览器登录 bilibili.com → F12 → Application → Cookies → SESSDATA
# ------------------------------------------
RAW_SESSDATA = "请填入你的SESSDATA"
SESSDATA = urllib.parse.unquote(RAW_SESSDATA)

# ------------------------------------------
# 1.2 目标 UP 主 ID 列表（共 86 位）
# 筛选标准：哔哩哔哩知识区原创 UP 主，视频时长≥60s，发布视频数≥10条
# ------------------------------------------
TARGET_MIDS = [
    483052036, 1641520135, 28760071,  34840587,  519872016, 435931665,
    23947287,  6331931,   323987490, 346563107, 6369831,   473837611,
    421773867, 451320374, 1140672573,35040323,  10085450,  454719565,
    1960752210,809048,    192090,    20050011,  297786973, 253553776,
    10330740,  651039864, 289706107, 609860740, 222103174, 517327498,
    2026173074,1649919642,592240285, 19860125,  28626598,  1643198121,
    75571882,  456664753, 1732848825,326427334, 521974986, 397490386,
    532778711, 1117551831,8096990,   397558501, 300223719, 306935529,
    401791744, 316627722, 1715374867,111541532, 1374452021,318902582,
    382667094, 34264408,  7788379,   1982434140,531131239, 509905775,
    19319172,  1821509509,438173577, 100785033, 270870923, 339233162,
    546189,    415793035, 1937308559,4285334,   43092887,  485197227,
    14229967,  1150791631,294816724, 504934876, 520819684, 673779175,
    485191154, 99336697,  1131457022,3546825306933846, 3546876657797218,
    3546668546919037, 3546584625186941
]

# ------------------------------------------
# 1.3 爬取参数
# ------------------------------------------
PAGE_SIZE  = 30    # 每页视频数量（B 站接口上限30条）
MAX_PAGES  = 10    # 每位 UP 主最多爬取页数（300条/人）
SLEEP_MIN  = 1.0   # 请求间隔下限（秒），防止触发限速
SLEEP_MAX  = 2.5   # 请求间隔上限（秒）

# ------------------------------------------
# 1.4 文件路径
# ------------------------------------------
OUTPUT_FILE  = "step1_raw_data.xlsx"   # 最终输出（含弹幕情感）
BACKUP_FILE  = f"backup_{datetime.now().strftime('%Y%m%d')}.xlsx"  # 断点续传备份

# ------------------------------------------
# 1.5 情感分析参数
# ------------------------------------------
DANMU_SAMPLE_SIZE = 500   # 每条视频随机抽取弹幕数量上限

# 知识区专属情感词典
# 正面词库：表达知识肯定、学习收益、内容质量认可
POSITIVE_LEXICON = {
    "干货", "涨知识", "学到了", "太强了", "讲得好", "清晰", "深度",
    "良心", "用心", "专业", "硬核", "全面", "系统", "实用", "通俗易懂",
    "豁然开朗", "醍醐灌顶", "受益匪浅", "三连", "收藏", "必看", "推荐",
    "白月光", "宝藏", "神作", "神仙", "满分", "绝了", "太好看了",
    "支持", "加油", "期待更新", "催更", "感谢", "感恩", "辛苦了",
    "讲解清晰", "浅显易懂", "逻辑清晰", "条理清楚", "有料", "有深度",
    "真棒", "厉害", "厉害了", "牛", "牛啊", "牛批", "强", "太强",
    "喜欢", "爱了", "爱了爱了", "好看", "好听", "好棒",
    # 可根据实际语料扩充至 600 条
}

# 负面词库：表达内容质量批评、失望情绪
NEGATIVE_LEXICON = {
    "水视频", "水货", "划水", "注水", "空洞", "没营养", "废话多",
    "标题党", "挂羊头卖狗肉", "误导", "不严谨", "出错了", "有误",
    "错误", "失望", "一般", "无聊", "睡着了", "难看", "无语",
    "不推荐", "脑残", "差评", "劝退", "弃坑", "取关", "取消关注",
    "浪费时间", "啥也没说", "重复啰嗦", "一直重复",
    # 可根据实际语料扩充至 400 条
}

# =============================================================================
# 第二部分：B 站 WBI 签名（接口鉴权，勿修改）
# =============================================================================
# WBI 签名是 B 站 2023 年起对 /space/wbi/arc/search 等接口的防爬机制，
# 通过对请求参数进行 MD5 混淆签名以验证请求合法性。
# 参考：https://github.com/SocialSisterYi/bilibili-API-collect

MIXIN_KEY_ENC_TAB = [
    46, 47, 18,  2, 53,  8, 23, 32, 15, 50, 10, 31, 58,  3, 45, 35,
    27, 43,  5, 49, 33,  9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48,  7, 16, 24, 55, 40, 61, 26, 17,  0,  1, 60, 51, 30,  4,
    22, 25, 54, 21, 56, 59,  6, 63, 57, 62, 11, 36, 20, 34, 44, 52
]

def _get_mixin_key(orig: str) -> str:
    """按混淆表重排字符串，取前32位作为签名密钥。"""
    return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, "")[:32]

def _sign_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    """对请求参数附加 WBI 签名（wts + w_rid）。"""
    mixin_key = _get_mixin_key(img_key + sub_key)
    params["wts"] = round(time.time())
    params = dict(sorted(params.items()))
    query = urllib.parse.urlencode({
        k: "".join(c for c in str(v) if c not in "!'()*")
        for k, v in params.items()
    })
    params["w_rid"] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return params

def _fetch_wbi_keys(headers: dict):
    """从导航接口获取当前有效的 WBI 密钥对。"""
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/nav",
            headers=headers, timeout=8
        )
        resp.raise_for_status()
        wbi = resp.json()["data"]["wbi_img"]
        img_key = wbi["img_url"].rsplit("/", 1)[1].split(".")[0]
        sub_key = wbi["sub_url"].rsplit("/", 1)[1].split(".")[0]
        return img_key, sub_key
    except Exception as exc:
        raise RuntimeError(f"WBI 密钥获取失败：{exc}")

# =============================================================================
# 第三部分：视频元数据采集
# =============================================================================

def _build_headers() -> dict:
    """构造浏览器伪装请求头。"""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.bilibili.com/",
        "Cookie": f"SESSDATA={SESSDATA}",
    }

def _fetch_up_info(mid: int, headers: dict) -> dict:
    """
    获取 UP 主基本信息（昵称、粉丝数）。

    Parameters
    ----------
    mid : int
        UP 主的用户 ID。
    headers : dict
        请求头。

    Returns
    -------
    dict
        包含 name（昵称）和 fans（粉丝数）的字典；失败时返回默认值。
    """
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/card",
            headers=headers, params={"mid": mid}, timeout=8
        )
        data = resp.json()
        if data["code"] == 0:
            card = data["data"]["card"]
            return {"name": card["name"], "fans": int(card["fans"])}
    except Exception:
        pass
    return {"name": "Unknown", "fans": 0}

def _fetch_video_stat(bvid: str, headers: dict) -> dict | None:
    """
    获取单条视频的统计数据。

    采集字段：
        view（播放量）、coin（投币数）、like（点赞数）、
        favorite（收藏数）、share（分享数）、reply（评论数）、
        duration（时长/秒）、pubdate（发布时间戳）、copyright（原创标记）

    Parameters
    ----------
    bvid : str
        视频 BV 号。
    headers : dict
        请求头。

    Returns
    -------
    dict or None
        统计字段字典；视频不存在、转载或请求失败时返回 None。
    """
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/view",
            headers=headers, params={"bvid": bvid}, timeout=8
        )
        data = resp.json()
        if data["code"] != 0:
            return None
        base = data["data"]
        if base["copyright"] != 1:   # 剔除转载视频
            return None
        stat = base["stat"]
        return {
            "view":     stat["view"],
            "coin":     stat["coin"],
            "like":     stat["like"],
            "favorite": stat["favorite"],
            "share":    stat["share"],
            "reply":    stat["reply"],     # 评论总数（用于构造 ln_comment）
            "duration": base["duration"],
            "pubdate":  datetime.fromtimestamp(base["pubdate"]),
        }
    except Exception:
        return None

def crawl_videos() -> pd.DataFrame:
    """
    主采集流程：遍历目标 UP 主列表，批量采集视频元数据。

    断点续传逻辑：
        若备份文件已存在，则读取其中已完成的 UP 主列表，
        本次运行自动跳过这些 UP 主，仅爬取剩余部分。

    Returns
    -------
    pd.DataFrame
        所有采集到的视频记录。
    """
    headers = _build_headers()
    img_key, sub_key = _fetch_wbi_keys(headers)

    # 断点续传：读取已有备份
    if os.path.exists(BACKUP_FILE):
        existing = pd.read_excel(BACKUP_FILE)
        all_records = existing.to_dict("records")
        done_mids   = set(existing["mid"].unique())
        print(f"[续传] 已恢复 {len(all_records)} 条记录，"
              f"覆盖 {len(done_mids)} 位 UP 主。")
    else:
        all_records = []
        done_mids   = set()

    remaining = [m for m in TARGET_MIDS if m not in done_mids]
    print(f"[启动] 共需处理 {len(remaining)} 位 UP 主。")

    for idx, mid in enumerate(remaining):
        up_info = _fetch_up_info(mid, headers)
        print(f"  [{idx+1}/{len(remaining)}] "
              f"{up_info['name']} (mid={mid})", end="", flush=True)

        up_records = []
        for page in range(1, MAX_PAGES + 1):
            params = _sign_wbi(
                {"mid": mid, "ps": PAGE_SIZE, "pn": page,
                 "tid": 0, "order": "pubdate", "keyword": ""},
                img_key, sub_key
            )
            try:
                resp = requests.get(
                    "https://api.bilibili.com/x/space/wbi/arc/search",
                    headers=headers, params=params, timeout=10
                )
                vlist = (resp.json()
                             .get("data", {})
                             .get("list", {})
                             .get("vlist", []))
                if not vlist:
                    break   # 已无更多视频

                for v in vlist:
                    stat = _fetch_video_stat(v["bvid"], headers)
                    if stat is None:
                        continue
                    up_records.append({
                        "mid":     mid,
                        "up_name": up_info["name"],
                        "up_fans": up_info["fans"],
                        "bvid":    v["bvid"],
                        "title":   v["title"],
                        **stat,
                    })
                    print(".", end="", flush=True)
                    time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

            except Exception as exc:
                print(f"\n    [警告] 第{page}页请求异常：{exc}")
                break
            time.sleep(random.uniform(0.8, 1.5))   # 翻页间隔

        # 每位 UP 主完成后立即写入备份
        if up_records:
            all_records.extend(up_records)
            pd.DataFrame(all_records).to_excel(BACKUP_FILE, index=False)
        print(f" 完成（本次新增 {len(up_records)} 条）")

    return pd.DataFrame(all_records)

# =============================================================================
# 第四部分：弹幕情感量化
# =============================================================================

def _get_cid(bvid: str, headers: dict) -> int | None:
    """
    通过 BV 号获取视频 CID。

    弹幕 XML 接口以 CID（稿件分集 ID）而非 BV 号标识内容，
    因此需先通过视频详情接口查询对应 CID。

    Parameters
    ----------
    bvid : str
        视频 BV 号。
    headers : dict
        请求头。

    Returns
    -------
    int or None
        CID；失败时返回 None。
    """
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/view",
            headers=headers, params={"bvid": bvid}, timeout=8
        )
        data = resp.json()
        if data["code"] == 0:
            return data["data"]["cid"]
    except Exception:
        pass
    return None

def _score_text(text: str) -> float | None:
    """
    对单条弹幕文本进行情感打分，采用混合策略：
        1. 专属词典优先：若文本命中正/负面词典，直接赋予确定性分值
           （正面 → 0.95，负面 → 0.05），以修正 SnowNLP 对知识区
           领域词汇的识别偏差；
        2. SnowNLP 兜底：未命中词典时调用 SnowNLP 通用情感模型。

    Parameters
    ----------
    text : str
        清洗后的弹幕文本。

    Returns
    -------
    float or None
        情感得分（0—1，越高越正面）；文本过短时返回 None。
    """
    if len(text) < 2:
        return None
    # 优先查专属词典
    for word in POSITIVE_LEXICON:
        if word in text:
            return 0.95
    for word in NEGATIVE_LEXICON:
        if word in text:
            return 0.05
    # SnowNLP 兜底
    try:
        return SnowNLP(text).sentiments
    except Exception:
        return None

def analyze_danmu(bvid: str, headers: dict) -> float | None:
    """
    采集视频弹幕并计算情感得分。

    流程：
        BV号 → CID → XML 弹幕文件 → 随机抽样（≤500条）
        → 逐条清洗与打分 → 算术均值

    Parameters
    ----------
    bvid : str
        视频 BV 号。
    headers : dict
        请求头（调用 CID 接口需要）。

    Returns
    -------
    float or None
        该视频弹幕情感均值（0—1）；无弹幕或抓取失败时返回 None。
    """
    cid = _get_cid(bvid, headers)
    if cid is None:
        return None

    url = f"https://comment.bilibili.com/{cid}.xml"
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = "utf-8"
        xml_root = etree.fromstring(resp.content)
        all_danmu = xml_root.xpath("//d/text()")

        if not all_danmu:
            return 0.5   # 无弹幕，给中性分

        # 随机抽样（不足 DANMU_SAMPLE_SIZE 条则取全量）
        sample = (random.sample(all_danmu, DANMU_SAMPLE_SIZE)
                  if len(all_danmu) > DANMU_SAMPLE_SIZE
                  else all_danmu)

        scores = []
        for raw in sample:
            clean = re.sub(r"[^\w\u4e00-\u9fff]", "", raw)
            s = _score_text(clean)
            if s is not None:
                scores.append(s)

        return float(np.mean(scores)) if scores else 0.5

    except Exception:
        return None

def enrich_with_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """
    为 DataFrame 中每条视频补充弹幕情感得分列（sentiment_score）。

    断点续传：若 sentiment_score 列中某行已有数值，则跳过该行。

    Parameters
    ----------
    df : pd.DataFrame
        包含 bvid 列的视频数据表。

    Returns
    -------
    pd.DataFrame
        追加 sentiment_score 列后的数据表。
    """
    headers = _build_headers()

    if "sentiment_score" not in df.columns:
        df["sentiment_score"] = np.nan

    total = len(df)
    for idx, row in df.iterrows():
        # 跳过已处理行（断点续传）
        if pd.notna(row["sentiment_score"]):
            continue

        score = analyze_danmu(row["bvid"], headers)
        df.at[idx, "sentiment_score"] = score

        if (idx + 1) % 50 == 0:
            print(f"  弹幕情感进度：{idx+1}/{total}")
            df.to_excel(BACKUP_FILE, index=False)   # 定期保存

        time.sleep(random.uniform(1.0, 2.0))

    return df

# =============================================================================
# 第五部分：主程序
# =============================================================================

def main():
    print("=" * 60)
    print("B 站知识区数据采集流程启动")
    print(f"目标 UP 主数量：{len(TARGET_MIDS)} 位")
    print("=" * 60)

    # Step 1：视频元数据采集
    print("\n[Step 1] 视频元数据采集...")
    df = crawl_videos()
    print(f"  采集完成，共获取 {len(df)} 条视频记录。")

    # Step 2：弹幕情感量化
    print("\n[Step 2] 弹幕情感量化...")
    df = enrich_with_sentiment(df)
    missing = df["sentiment_score"].isna().sum()
    print(f"  情感量化完成（{len(df) - missing} 条成功，{missing} 条失败）。")

    # Step 3：保存最终文件
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\n[完成] 原始数据已保存至：{OUTPUT_FILE}")
    print(f"  包含字段：{list(df.columns)}")
    print(f"  样本量：{len(df)} 条")

if __name__ == "__main__":
    main()
