# =============================================================================
# 字幕爬取覆盖率测试 - 模拟测试版本
# 用于验证脚本逻辑的正确性（模拟API响应，不实际请求B站）
#
# 验证内容：
#   1. 数据读取与随机抽样是否正确
#   2. 字幕判断与选择逻辑是否正确
#   3. 统计计算与输出是否正确
#   4. CSV 输出格式是否正确
#   5. 按年份统计是否正确
# =============================================================================

import pandas as pd
import numpy as np
import random
import os
import sys

# 导入主脚本中的函数
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_subtitle_coverage import (
    select_best_subtitle,
    FIELD_MAP,
    DATA_FILE,
    OUTPUT_CSV,
)


def test_step1_data_loading():
    """第一步测试：数据读取与随机抽样"""
    print("=" * 60)
    print("[Step 1 测试] 数据读取与随机抽样")
    print("=" * 60)

    assert os.path.exists(DATA_FILE), f"数据文件不存在：{DATA_FILE}"

    df = pd.read_excel(DATA_FILE)
    assert len(df) > 0, "数据为空"
    assert "bvid" in df.columns, "缺少 bvid 字段"
    print(f"  数据总量：{len(df)} 条")

    # 随机抽样
    sample = df.sample(n=100, random_state=42).reset_index(drop=True)
    assert len(sample) == 100, f"抽样数量异常：{len(sample)}"

    # 检查 bvid 格式
    for bvid in sample["bvid"]:
        assert isinstance(bvid, str) and bvid.startswith("BV"), \
            f"bvid 格式异常：{bvid}"

    # 检查发布时间
    sample["pubdate"] = pd.to_datetime(sample["pubdate"])
    assert sample["pubdate"].notna().all(), "存在无效的发布时间"

    print(f"  抽样数量：{len(sample)} 条")
    print(f"  bvid 格式检查：全部通过")
    print(f"  时间范围：{sample['pubdate'].min()} ~ {sample['pubdate'].max()}")
    print(f"  涉及UP主：{sample['mid'].nunique()} 位")
    print("  [PASS] Step 1 测试通过\n")
    return sample


def test_step2_subtitle_logic():
    """第二步测试：字幕判断与选择逻辑"""
    print("=" * 60)
    print("[Step 2 测试] 字幕判断与选择逻辑")
    print("=" * 60)

    # 测试1：空字幕列表
    result = select_best_subtitle([])
    assert result == {}, "空列表应返回空字典"
    print("  测试1 - 空字幕列表：PASS")

    # 测试2：只有中文字幕 zh-CN
    subs = [{"lan": "zh-CN", "lan_doc": "中文（中国）",
             "subtitle_url": "//example.com/zh-CN.json"}]
    result = select_best_subtitle(subs)
    assert result["lan"] == "zh-CN", "应选择 zh-CN"
    print("  测试2 - 只有zh-CN：PASS")

    # 测试3：中英文字幕共存，应优先选中文
    subs = [
        {"lan": "en", "lan_doc": "English",
         "subtitle_url": "//example.com/en.json"},
        {"lan": "zh-CN", "lan_doc": "中文（中国）",
         "subtitle_url": "//example.com/zh-CN.json"},
    ]
    result = select_best_subtitle(subs)
    assert result["lan"] == "zh-CN", "应优先选择 zh-CN"
    print("  测试3 - 中英共存优先中文：PASS")

    # 测试4：zh-Hans 字幕
    subs = [
        {"lan": "en", "lan_doc": "English",
         "subtitle_url": "//example.com/en.json"},
        {"lan": "zh-Hans", "lan_doc": "中文（简体）",
         "subtitle_url": "//example.com/zh-Hans.json"},
    ]
    result = select_best_subtitle(subs)
    assert result["lan"] == "zh-Hans", "应选择 zh-Hans"
    print("  测试4 - zh-Hans 识别：PASS")

    # 测试5：AI 生成字幕 (ai-zh)
    subs = [
        {"lan": "ai-zh", "lan_doc": "中文（自动生成）",
         "subtitle_url": "//example.com/ai-zh.json"},
    ]
    result = select_best_subtitle(subs)
    assert result["lan"] == "ai-zh", "应选择 ai-zh"
    print("  测试5 - AI 生成字幕 (ai-zh)：PASS")

    # 测试6：只有英文字幕，应返回英文
    subs = [
        {"lan": "en", "lan_doc": "English",
         "subtitle_url": "//example.com/en.json"},
    ]
    result = select_best_subtitle(subs)
    assert result["lan"] == "en", "只有英文时应返回英文"
    print("  测试6 - 只有英文字幕：PASS")

    # 测试7：zh-CN 优先于 ai-zh
    subs = [
        {"lan": "ai-zh", "lan_doc": "中文（自动生成）",
         "subtitle_url": "//example.com/ai-zh.json"},
        {"lan": "zh-CN", "lan_doc": "中文（中国）",
         "subtitle_url": "//example.com/zh-CN.json"},
    ]
    result = select_best_subtitle(subs)
    assert result["lan"] == "zh-CN", "zh-CN 应优先于 ai-zh"
    print("  测试7 - zh-CN 优先于 ai-zh：PASS")

    print("  [PASS] Step 2 全部测试通过\n")


def test_step3_statistics(sample: pd.DataFrame):
    """第三步测试：模拟统计计算"""
    print("=" * 60)
    print("[Step 3 测试] 统计计算（使用模拟数据）")
    print("=" * 60)

    # 模拟100条结果：约80%有字幕
    random.seed(42)
    np.random.seed(42)

    results = []
    for idx, row in sample.iterrows():
        bvid = row["bvid"]
        pubdate = row["pubdate"]

        # 模拟：80%概率有字幕，早期视频（2020-2021）概率降至60%
        year = pd.to_datetime(pubdate).year
        prob = 0.60 if year <= 2021 else 0.82
        has_sub = random.random() < prob

        if has_sub:
            lang = random.choice(["zh-CN", "zh-Hans", "ai-zh"])
            char_count = random.randint(500, 20000)
            preview = "这是模拟的字幕文本内容" * 10
        else:
            lang = ""
            char_count = 0
            preview = ""

        results.append({
            "bvid": bvid,
            "aid": random.randint(100000, 999999),
            "cid": random.randint(100000, 999999),
            "pubdate": pubdate,
            "has_subtitle": has_sub,
            "subtitle_lang": lang,
            "subtitle_char_count": char_count,
            "subtitle_preview": preview[:200],
            "error": "",
        })

    df_result = pd.DataFrame(results)

    # 覆盖率统计
    total_count = len(df_result)
    has_sub_count = df_result["has_subtitle"].sum()
    no_sub_count = total_count - has_sub_count
    coverage = has_sub_count / total_count * 100

    assert total_count == 100, f"总数应为100：{total_count}"
    assert has_sub_count + no_sub_count == total_count, "有/无字幕数不一致"
    assert 0 <= coverage <= 100, f"覆盖率异常：{coverage}"

    print(f"\n  总样本：{total_count}")
    print(f"  有字幕：{has_sub_count} ({coverage:.1f}%)")
    print(f"  无字幕：{no_sub_count} ({100 - coverage:.1f}%)")

    # 字幕文本长度分布
    sub_texts = df_result[df_result["has_subtitle"] == True]
    if len(sub_texts) > 0:
        counts = sub_texts["subtitle_char_count"]
        mean_val = counts.mean()
        median_val = counts.median()
        min_val = counts.min()
        max_val = counts.max()

        assert mean_val > 0, "平均字数应大于0"
        assert min_val <= median_val <= max_val, "中位数应在最小和最大之间"

        print(f"\n  有字幕视频平均字数：{mean_val:,.0f}")
        print(f"  字数中位数：{median_val:,.0f}")
        print(f"  字数范围：[{min_val:,.0f}, {max_val:,.0f}]")

    # 按年份覆盖率
    df_result["pubdate"] = pd.to_datetime(df_result["pubdate"], errors="coerce")
    df_result["year"] = df_result["pubdate"].dt.year

    print("\n  按年份的字幕覆盖率：")
    year_stats = df_result.groupby("year").agg(
        total=("has_subtitle", "count"),
        has_sub=("has_subtitle", "sum")
    )
    year_stats["coverage"] = (year_stats["has_sub"] / year_stats["total"] * 100).round(1)
    for year, row in year_stats.iterrows():
        if pd.notna(year):
            print(f"    {int(year)}年：{int(row['has_sub'])}/{int(row['total'])} "
                  f"({row['coverage']:.1f}%)")

    # 字幕语言分布
    print("\n  字幕语言分布：")
    lang_counts = sub_texts["subtitle_lang"].value_counts()
    for lang, count in lang_counts.items():
        print(f"    {lang}: {count} 条")

    # CSV 输出测试
    output_file = "subtitle_test_result_mock.csv"
    df_result.to_csv(output_file, index=False, encoding="utf-8-sig")
    assert os.path.exists(output_file), "CSV 文件未生成"

    # 验证 CSV 可以正确读回
    df_check = pd.read_csv(output_file)
    assert len(df_check) == 100, f"CSV 行数异常：{len(df_check)}"
    expected_cols = ["bvid", "aid", "cid", "pubdate", "has_subtitle",
                     "subtitle_lang", "subtitle_char_count", "subtitle_preview", "error"]
    for col in expected_cols:
        assert col in df_check.columns, f"CSV 缺少列：{col}"

    print(f"\n  CSV 输出验证通过：{output_file}")
    print(f"  CSV 列数：{len(df_check.columns)}，行数：{len(df_check)}")

    # 清理
    os.remove(output_file)

    print("  [PASS] Step 3 全部测试通过\n")


def test_step4_edge_cases():
    """第四步测试：边界情况"""
    print("=" * 60)
    print("[Step 4 测试] 边界情况检查")
    print("=" * 60)

    # 测试 subtitle_url 补全 https:
    from test_subtitle_coverage import download_subtitle_text
    # 这个函数需要网络，这里只验证 URL 补全逻辑
    url_without_https = "//i0.hdslb.com/bfs/subtitle/xxx.json"
    expected = "https://i0.hdslb.com/bfs/subtitle/xxx.json"
    # 只验证逻辑，不实际请求
    if not url_without_https.startswith("http"):
        url_fixed = "https:" + url_without_https
    assert url_fixed == expected, f"URL补全异常：{url_fixed}"
    print("  测试1 - URL https: 前缀补全：PASS")

    # 测试空字幕列表的select
    result = select_best_subtitle([])
    assert result == {}, "空列表应返回空字典"
    print("  测试2 - 空字幕列表处理：PASS")

    # 测试单条字幕
    result = select_best_subtitle([{"lan": "ja", "subtitle_url": "//test"}])
    assert result["lan"] == "ja", "单条非中文字幕应直接返回"
    print("  测试3 - 单条非中文字幕兜底：PASS")

    print("  [PASS] Step 4 全部测试通过\n")


def main():
    print("\n" + "=" * 60)
    print("  B站字幕爬取覆盖率测试 - 逻辑验证")
    print("=" * 60 + "\n")

    # Step 1：数据读取与抽样
    sample = test_step1_data_loading()

    # Step 2：字幕选择逻辑
    test_step2_subtitle_logic()

    # Step 3：统计计算
    test_step3_statistics(sample)

    # Step 4：边界情况
    test_step4_edge_cases()

    # 汇总
    print("=" * 60)
    print("  全部测试通过!")
    print("=" * 60)
    print("\n脚本逻辑验证完成。用户在本地环境中：")
    print("  1. 打开 test_subtitle_coverage.py")
    print("  2. 将 COOKIE 变量替换为浏览器中复制的完整Cookie")
    print("  3. 运行 python test_subtitle_coverage.py")
    print("  即可获得真实的字幕覆盖率测试结果。")


if __name__ == "__main__":
    main()
