# =============================================================================
# B站视频字幕爬取覆盖率测试脚本
#
# 用途：从 step4_final_data.xlsx 中随机抽取100条视频，
#       逐一调用B站字幕接口，检测CC字幕覆盖率
#
# 依赖：pip install requests pandas numpy openpyxl
# =============================================================================

import requests
import pandas as pd
import numpy as np
import time
import random
import json
import os
import urllib.parse
import hashlib
from functools import reduce
from datetime import datetime

# =============================================================================
# 全局配置
# =============================================================================

# ------------------------------------------
# SESSDATA 配置
# 获取方法：浏览器登录 bilibili.com -> F12 -> Application -> Cookies -> SESSDATA
# ------------------------------------------
RAW_SESSDATA = "e6389147%2C1790388792%2C11e4d%2A32CjCZR08f6XKM29SjayfBUbU5xmdFHybhZLEL7p3FnnfhyMSKRFua23eLtDy6vgNhhqISVnFfdzJIUktIVGVOSEJoa1k1U0hNdTM0eUxvZ0l6eDdXSE9IUWVNYTZncVNTT0QxakExbE5ERjZPbjlZQmt3T3pTd0gwZDVJLXFrOXRLcGJTWVN0RzlBIIEC"
SESSDATA = urllib.parse.unquote(RAW_SESSDATA)
COOKIE = f"SESSDATA={SESSDATA}"

# ------------------------------------------
# 数据文件与字段映射
# ------------------------------------------
DATA_FILE = "step4_final_data.xlsx"
SAMPLE_SIZE = 100  # 随机抽样数量

# 字段名映射（方便适配不同格式的数据文件）
FIELD_MAP = {
    "bvid": "bvid",
    "title": "title",
    "pubdate": "pubdate",
    "view": "view",
    "mid": "mid",
    "up_name": "up_name",
}

# ------------------------------------------
# 爬取参数
# ------------------------------------------
SLEEP_MIN = 1.0  # 请求间隔下限（秒）
SLEEP_MAX = 3.0  # 请求间隔上限（秒）
REQUEST_TIMEOUT = 10  # 请求超时（秒）

# ------------------------------------------
# 输出文件
# ------------------------------------------
OUTPUT_CSV = "subtitle_test_result.csv"

# =============================================================================
# WBI 签名（与 01_video_crawler.py 保持一致）
# =============================================================================

MIXIN_KEY_ENC_TAB = [
    46, 47, 18,  2, 53,  8, 23, 32, 15, 50, 10, 31, 58,  3, 45, 35,
    27, 43,  5, 49, 33,  9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48,  7, 16, 24, 55, 40, 61, 26, 17,  0,  1, 60, 51, 30,  4,
    22, 25, 54, 21, 56, 59,  6, 63, 57, 62, 11, 36, 20, 34, 44, 52
]


def _get_mixin_key(orig: str) -> str:
    return reduce(lambda s, i: s + orig[i], MIXIN_KEY_ENC_TAB, "")[:32]


def _sign_wbi(params: dict, img_key: str, sub_key: str) -> dict:
    mixin_key = _get_mixin_key(img_key + sub_key)
    params["wts"] = round(time.time())
    params = dict(sorted(params.items()))
    query = urllib.parse.urlencode({
        k: "".join(c for c in str(v) if c not in "!'()*")
        for k, v in params.items()
    })
    params["w_rid"] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return params


# =============================================================================
# 核心函数
# =============================================================================

def build_headers() -> dict:
    """构造请求头"""
    return {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.bilibili.com/",
        "Cookie": COOKIE,
    }


def fetch_wbi_keys(headers: dict):
    """从导航接口获取 WBI 密钥对"""
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/nav",
            headers=headers, timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        wbi = resp.json()["data"]["wbi_img"]
        img_key = wbi["img_url"].rsplit("/", 1)[1].split(".")[0]
        sub_key = wbi["sub_url"].rsplit("/", 1)[1].split(".")[0]
        return img_key, sub_key
    except Exception as exc:
        print(f"[WARNING] WBI 密钥获取失败：{exc}")
        return None, None


def fetch_video_info(bvid: str, headers: dict) -> dict:
    """
    通过 BV 号获取视频的 aid 和 cid。
    返回 {"aid": xxx, "cid": xxx} 或空字典。
    """
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/web-interface/view",
            headers=headers, params={"bvid": bvid}, timeout=REQUEST_TIMEOUT
        )
        data = resp.json()
        if data["code"] == 0:
            return {
                "aid": data["data"]["aid"],
                "cid": data["data"]["cid"],
            }
        else:
            print(f"    [API错误] code={data['code']}, msg={data.get('message','')}")
    except Exception as exc:
        print(f"    [请求异常] {exc}")
    return {}


def fetch_subtitle_info(aid: int, cid: int, headers: dict) -> list:
    """
    调用 B站 player/v2 接口获取字幕列表。
    返回 subtitles 数组（可能为空列表）。
    """
    try:
        resp = requests.get(
            "https://api.bilibili.com/x/player/v2",
            headers=headers,
            params={"aid": aid, "cid": cid},
            timeout=REQUEST_TIMEOUT
        )
        data = resp.json()
        if data["code"] == 0:
            subtitles = (data.get("data", {})
                             .get("subtitle", {})
                             .get("subtitles", []))
            return subtitles if subtitles else []
    except Exception:
        pass
    return []


def download_subtitle_text(subtitle_url: str, headers: dict) -> str:
    """
    下载字幕 JSON 文件，提取所有 content 字段拼接为完整文本。
    """
    if not subtitle_url.startswith("http"):
        subtitle_url = "https:" + subtitle_url
    try:
        resp = requests.get(subtitle_url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        sub_data = resp.json()
        body = sub_data.get("body", [])
        texts = [item.get("content", "") for item in body]
        return "".join(texts)
    except Exception:
        return ""


def select_best_subtitle(subtitles: list) -> dict:
    """
    从字幕列表中优先选取中文字幕。
    优先级：zh-CN > zh-Hans > ai-zh > 包含 'zh' 的 > 第一条
    """
    if not subtitles:
        return {}

    priority_langs = ["zh-CN", "zh-Hans"]
    for lang in priority_langs:
        for sub in subtitles:
            if sub.get("lan", "") == lang:
                return sub

    # 包含 zh 的（如 ai-zh 等AI生成字幕）
    for sub in subtitles:
        if "zh" in sub.get("lan", "").lower():
            return sub

    # 兜底返回第一条
    return subtitles[0]


# =============================================================================
# 主流程
# =============================================================================

def main():
    print("=" * 60)
    print("B站视频字幕爬取覆盖率测试")
    print("=" * 60)

    # 打印 Cookie 前20字符，确认是否正确加载
    print(f"Cookie 前30字符: {COOKIE[:30]}...")
    if "请替换" in COOKIE:
        print("[ERROR] SESSDATA 未配置！请编辑脚本开头的 RAW_SESSDATA")
        return

    # ------------------------------------------
    # 第一步：读取数据并随机抽样
    # ------------------------------------------
    print(f"\n[Step 1] 从 {DATA_FILE} 随机抽取 {SAMPLE_SIZE} 条视频...")

    if not os.path.exists(DATA_FILE):
        print(f"[ERROR] 找不到数据文件：{DATA_FILE}")
        return

    df_all = pd.read_excel(DATA_FILE)
    print(f"  数据总量：{len(df_all)} 条")

    # 确保有 bvid 字段
    bvid_col = FIELD_MAP["bvid"]
    if bvid_col not in df_all.columns:
        print(f"[ERROR] 数据中找不到 bvid 字段（配置名：{bvid_col}）")
        return

    # 随机抽样
    sample_size = min(SAMPLE_SIZE, len(df_all))
    df_sample = df_all.sample(n=sample_size, random_state=42).reset_index(drop=True)
    print(f"  已抽取 {len(df_sample)} 条样本")

    # ------------------------------------------
    # 第二步：逐一爬取字幕
    # ------------------------------------------
    print(f"\n[Step 2] 开始爬取字幕...")
    headers = build_headers()

    results = []
    total = len(df_sample)

    for idx, row in df_sample.iterrows():
        bvid = row[FIELD_MAP["bvid"]]
        title = row.get(FIELD_MAP.get("title", "title"), "")
        pubdate = row.get(FIELD_MAP.get("pubdate", "pubdate"), "")

        # 获取 aid 和 cid
        info = fetch_video_info(bvid, headers)
        if not info:
            print(f"  [{idx+1}/{total}] {bvid} - [X] 无法获取视频信息")
            results.append({
                "bvid": bvid,
                "aid": "",
                "cid": "",
                "pubdate": pubdate,
                "has_subtitle": False,
                "subtitle_lang": "",
                "subtitle_char_count": 0,
                "subtitle_preview": "",
                "error": "无法获取aid/cid",
            })
            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
            continue

        aid, cid = info["aid"], info["cid"]

        # 获取字幕信息
        subtitles = fetch_subtitle_info(aid, cid, headers)

        if subtitles:
            best = select_best_subtitle(subtitles)
            lang = best.get("lan", "unknown")

            # 下载字幕文本
            sub_url = best.get("subtitle_url", "")
            text = download_subtitle_text(sub_url, headers)
            char_count = len(text)
            preview = text[:200] if text else ""

            print(f"  [{idx+1}/{total}] {bvid} - [OK] 有字幕 ({lang}, {char_count}字)")
            results.append({
                "bvid": bvid,
                "aid": aid,
                "cid": cid,
                "pubdate": pubdate,
                "has_subtitle": True,
                "subtitle_lang": lang,
                "subtitle_char_count": char_count,
                "subtitle_preview": preview,
                "error": "",
            })
        else:
            print(f"  [{idx+1}/{total}] {bvid} - [X] 无字幕")
            results.append({
                "bvid": bvid,
                "aid": aid,
                "cid": cid,
                "pubdate": pubdate,
                "has_subtitle": False,
                "subtitle_lang": "",
                "subtitle_char_count": 0,
                "subtitle_preview": "",
                "error": "",
            })

        time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))

    # ------------------------------------------
    # 第三步：统计与输出
    # ------------------------------------------
    print("\n" + "=" * 50)
    print("========== 测试完成 ==========")
    print("=" * 50)

    df_result = pd.DataFrame(results)

    # 覆盖率统计
    total_count = len(df_result)
    has_sub = df_result["has_subtitle"].sum()
    no_sub = total_count - has_sub
    coverage = has_sub / total_count * 100 if total_count > 0 else 0

    print(f"\n总样本：{total_count}")
    print(f"有字幕：{has_sub} ({coverage:.1f}%)")
    print(f"无字幕：{no_sub} ({100 - coverage:.1f}%)")

    # 字幕文本长度分布
    sub_texts = df_result[df_result["has_subtitle"] == True]
    if len(sub_texts) > 0:
        counts = sub_texts["subtitle_char_count"]
        print(f"\n有字幕视频平均字数：{counts.mean():,.0f}")
        print(f"字数中位数：{counts.median():,.0f}")
        print(f"字数范围：[{counts.min():,.0f}, {counts.max():,.0f}]")
        print(f"标准差：{counts.std():,.0f}")

    # 按年份覆盖率
    if FIELD_MAP["pubdate"] in df_sample.columns:
        df_result["pubdate"] = pd.to_datetime(df_result["pubdate"], errors="coerce")
        df_result["year"] = df_result["pubdate"].dt.year

        print("\n按年份的字幕覆盖率：")
        year_stats = df_result.groupby("year").agg(
            total=("has_subtitle", "count"),
            has_sub=("has_subtitle", "sum")
        )
        year_stats["coverage"] = (year_stats["has_sub"] / year_stats["total"] * 100).round(1)
        for year, row in year_stats.iterrows():
            if pd.notna(year):
                print(f"  {int(year)}年：{int(row['has_sub'])}/{int(row['total'])} "
                      f"({row['coverage']:.1f}%)")

    # 字幕语言分布
    if len(sub_texts) > 0:
        print("\n字幕语言分布：")
        lang_counts = sub_texts["subtitle_lang"].value_counts()
        for lang, count in lang_counts.items():
            print(f"  {lang}: {count} 条")

    # 保存详细结果 CSV
    df_result.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n详细结果已保存至：{OUTPUT_CSV}")


if __name__ == "__main__":
    main()
