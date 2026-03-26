* =============================================================================
* 哔哩哔哩知识区非金钱激励机制研究
* 脚本三：计量分析主程序
*
* 作者：[王语心]
* 单位：[中国社会科学院大学 经济学院]
* 日期：2026年
*
* 输入文件：step4_final_data.xlsx（脚本二输出）
*
* 输出文件（按顺序）：
*   Table_0_Descriptive.doc   描述性统计
*   Table_1_Baseline.doc      基准逐步回归（H1）
*   Table_2_Lewbel_IV.doc     Lewbel 异方差工具变量内生性检验
*   Table_3A_Hetero_Fans.doc  粉丝规模异质性分析（H5a）
*   Table_3B_Hetero_Duration.doc 视频时长异质性分析（H5b）
*   Table_4A_Nonlinear.doc    非线性效应检验
*   Table_4B_Interaction.doc  交互效应检验
*   Table_5A_Mechanism_Effort.doc  机制一：投入互惠（H2）
*   Table_5B_Mechanism_Feedback.doc 机制二：深度反馈（H3）
*   Table_5C_Mechanism_Flow.doc    机制三：流量证伪（H4）
*   Table_6A_Robustness_Rank.doc   稳健性：秩变量替换
*   Table_6B_Robustness_Lag.doc    稳健性：滞后阶数对比
*   Table_6C_Robustness_Sample.doc 稳健性：样本调整
*   Table_6D_Robustness_Shock.doc  稳健性：疫情外生冲击
*   Figure_1_Placebo_Test.png      安慰剂检验核密度图
*
* 依赖命令：outreg2、ivreg2h（需提前安装）
*   ssc install outreg2
*   ssc install ivreg2h
* =============================================================================

clear all
set more off
set matsize 800

* ⚠️ 修改为你的实际文件路径
cd "C:/Users/wyxov/Desktop/毕业论文/数据+代码"


* =======================================================
* PART 0: 数据读取与面板设置（公共基础）
* =======================================================

* --- 0.1 读取 step4 数据（基准回归、异质性、稳健性共用）---
import excel "step4_final_data.xlsx", firstrow clear

* --- 0.2 面板设置 ---
egen up_id = group(mid)
bysort up_id: gen t = _n
xtset up_id t

* --- 0.3 生成滞后二期变量（基准模型用） ---
gen L2_ln_coin  = L2.ln_coin
gen L2_ln_like  = L2.ln_like
gen L2_ln_fav   = L2.ln_fav
gen L2_ln_view  = L2.ln_view

* --- 0.4 生成滞后一期变量（稳健性对比用） ---
gen L1_ln_coin  = L1.ln_coin
gen L1_ln_like  = L1.ln_like

* --- 0.5 补充变量 ---
capture gen ln_duration = ln(duration + 1)
capture gen ln_fans     = ln(up_fans + 1)
capture gen ln_view     = ln(view + 1)


* =======================================================
* PART 1: 描述性统计与相关性分析
* =======================================================

* -------------------------------------------------------
* [Table 0-A] 主要变量的描述性统计
* -------------------------------------------------------
tabstat Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
        ln_duration ln_view ln_fans,                  ///
        stat(n mean sd min p25 median p75 max)        ///
        col(stat) format(%9.3f)

* 输出为 Word（需安装 tabout 或用 outreg2 的 sum 选项）
* 如 tabout 未安装，可改用以下方式：
estpost tabstat Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
                ln_duration ln_view ln_fans,                   ///
                stat(n mean sd min max) col(stat)
esttab using "Table_0_Descriptive.doc", replace                ///
       cells("count(fmt(0)) mean(fmt(3)) sd(fmt(3)) min(fmt(3)) max(fmt(3))") ///
       noobs label title("描述性统计")

* -------------------------------------------------------
* [Table 0-B] Pearson / Spearman 相关性分析
* -------------------------------------------------------
* Pearson 相关
pwcorr Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
       ln_duration ln_view ln_fans,                   ///
       star(0.05) obs

* 输出相关矩阵（需手动整理或使用 asdoc）
* asdoc 方式（若已安装）:
* asdoc pwcorr Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
*              ln_duration ln_view ln_fans, star(0.05) save(Table_0_Corr.doc) replace


* =======================================================
* PART 2: 基准回归（逐步回归）
* =======================================================

* -------------------------------------------------------
* [Table 1] 逐步回归 — 4列模型呈现系数稳定性
* -------------------------------------------------------

* Model 1：仅核心解释变量
xtreg Quality_Index L2_ln_coin, fe vce(cluster up_id)
est store M1

* Model 2：加入其他互动类对照变量
xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav, ///
      fe vce(cluster up_id)
est store M2

* Model 3：加入视频特征控制变量
xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view ln_fans,                   ///
      fe vce(cluster up_id)
est store M3

* Model 4：完整模型（加入时间固定效应）
xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view ln_fans                    ///
      i.year i.month,                                ///
      fe vce(cluster up_id)
est store M4

* Model 5：加入 ln_share 作为流量信号对照变量（H4预备）
* 逻辑：在完整模型中直接检验 ln_share 系数，
*       若不显著则为 H4"流量信号无效"提供基准佐证，
*       同时验证 L2_ln_coin 系数在加入 ln_share 后的稳健性
capture gen ln_share = ln(share + 1)   // step2数据中若已存在则跳过
xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view ln_fans ln_share           ///
      i.year i.month,                                ///
      fe vce(cluster up_id)
est store M5

outreg2 [M1 M2 M3 M4 M5] using "Table_1_Baseline.doc", replace ///
        word dec(3) tstat                                        ///
        title("Table 1: Baseline Regression (Step-wise)")        ///
        addnote("M5加入ln_share用于H4流量信号对照检验。Cluster-robust SE at UP-host level. * p<0.1, ** p<0.05, *** p<0.01")


* =======================================================
* PART 3: 内生性检验 — Lewbel 异方差工具变量法
* =======================================================

* -------------------------------------------------------
* [Table 2] Lewbel IV
* 说明：ivreg2h 利用模型残差的异方差结构自动生成内部工具变量
*       无需外部工具变量；需事先安装：ssc install ivreg2h
* -------------------------------------------------------

* 方法：先做组内去均值（within transform）消除个体固定效应，
*       再将去均值变量重命名为短名称后运行 ivreg2h。
*       重命名的原因：ivreg2h 在生成内部工具变量时会自动拼接
*       变量名（格式为 _z_内生变量名_外生变量名_eps），若变量名
*       含 dm_ 前缀则拼接后超出 Stata 32 字符限制，导致报错。

* Step 1：计算组内均值并去均值
foreach v of varlist Quality_Index L2_ln_coin L2_ln_like ///
                     L2_ln_fav ln_duration ln_view ln_fans {
    bysort up_id: egen mean_`v' = mean(`v')
    gen dm_`v' = `v' - mean_`v'
    drop mean_`v'
}

* Step 2：将去均值变量重命名为短名称（避免 ivreg2h 拼接时超长）
rename dm_Quality_Index  wY
rename dm_L2_ln_coin     wX
rename dm_L2_ln_like     wLk
rename dm_L2_ln_fav      wFv
rename dm_ln_duration    wDr
rename dm_ln_view        wVw
rename dm_ln_fans        wFn

* Step 3：生成年份和月份虚拟变量（时间固定效应保留）
tab year,  gen(dy_)
tab month, gen(dm_)

* Step 4：运行 Lewbel IV
* 语法说明：(wX = ) 表示 wX 为内生变量，= 号后留空由 ivreg2h
*           自动利用异方差结构生成工具变量，无需手动指定外部工具
ivreg2h wY wLk wFv wDr wVw wFn dy_* dm_* ///
        (wX = ),                           ///
        cluster(up_id)

outreg2 using "Table_2_Lewbel_IV.doc", replace         ///
        word dec(3) tstat                               ///
        title("Table 2: Endogeneity Test — Lewbel IV") ///
        addnote("Within-transformed variables. Heteroscedasticity-based IV (Lewbel 2012). * p<0.1, ** p<0.05, *** p<0.01")

* Step 5：清理临时变量，避免后续分析污染
drop wY wX wLk wFv wDr wVw wFn dy_* dm_*


* =======================================================
* PART 4: 异质性分析
* =======================================================

* -------------------------------------------------------
* 分组变量构建（使用实质性阈值，与论文描述一致）
* -------------------------------------------------------

* 粉丝量级：以 100 万为阈值（ln(1000001) ≈ 13.816）
gen is_head = (up_fans >= 1000000) if !missing(up_fans)
label define head_lbl 1 "头部(>100万)" 0 "尾部(<100万)"
label values is_head head_lbl

* 视频时长：以 15 分钟（900 秒）为阈值
gen is_long = (duration >= 900) if !missing(duration)
label define long_lbl 1 "长视频(≥15min)" 0 "短视频(<15min)"
label values is_long long_lbl

* -------------------------------------------------------
* [Table 3-A] 按粉丝量级分组回归
* -------------------------------------------------------
xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view i.year i.month             ///
      if is_head == 1, fe vce(cluster up_id)
est store Head

xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view i.year i.month             ///
      if is_head == 0, fe vce(cluster up_id)
est store Tail

outreg2 [Head Tail] using "Table_3A_Hetero_Fans.doc", replace ///
        word dec(3) tstat                                       ///
        title("Table 3A: Heterogeneity by Fan Level")          ///
        addnote("* p<0.1, ** p<0.05, *** p<0.01")

* -------------------------------------------------------
* [Table 3-B] 按视频时长分组回归
* -------------------------------------------------------
xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view i.year i.month             ///
      if is_long == 1, fe vce(cluster up_id)
est store Long

xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view i.year i.month             ///
      if is_long == 0, fe vce(cluster up_id)
est store Short

outreg2 [Long Short] using "Table_3B_Hetero_Duration.doc", replace ///
        word dec(3) tstat                                            ///
        title("Table 3B: Heterogeneity by Video Duration")          ///
        addnote("* p<0.1, ** p<0.05, *** p<0.01")


* =======================================================
* PART 5: 进一步分析
* =======================================================

* -------------------------------------------------------
* [Table 4-A] 非线性效应检验（加入投币数平方项）
* -------------------------------------------------------
gen L2_ln_coin_sq = L2_ln_coin ^ 2

xtreg Quality_Index L2_ln_coin L2_ln_coin_sq        ///
      L2_ln_like L2_ln_fav                          ///
      ln_duration ln_view ln_fans                   ///
      i.year i.month,                               ///
      fe vce(cluster up_id)
est store Nonlinear

outreg2 [M4 Nonlinear] using "Table_4A_Nonlinear.doc", replace ///
        word dec(3) tstat                                        ///
        title("Table 4A: Non-linear Effect Test")               ///
        addnote("M4 = baseline model without quadratic term. * p<0.1, ** p<0.05, *** p<0.01")

* -------------------------------------------------------
* [Table 4-B] 点赞与投币的交互效应
* 理论依据：检验稀缺性（投币）与零成本互动（点赞）的差异逻辑
* -------------------------------------------------------
gen coin_like_inter = L2_ln_coin * L2_ln_like

xtreg Quality_Index L2_ln_coin L2_ln_like coin_like_inter ///
      L2_ln_fav ln_duration ln_view ln_fans               ///
      i.year i.month,                                     ///
      fe vce(cluster up_id)
est store Interact

outreg2 [M4 Interact] using "Table_4B_Interaction.doc", replace ///
        word dec(3) tstat                                         ///
        title("Table 4B: Interaction Effect — Coin × Like")      ///
        addnote("* p<0.1, ** p<0.05, *** p<0.01")


* =======================================================
* PART 6: 机制分析（使用 step4 数据）
* =======================================================

* --- 重新读取含机制变量的数据 ---
import excel "step4_final_data.xlsx", firstrow clear

* 面板设置
egen up_id = group(mid)
bysort up_id: gen t = _n
xtset up_id t

* 变量生成
gen L2_ln_coin  = L2.ln_coin
gen L2_ln_like  = L2.ln_like
gen ln_share    = ln(share + 1)
capture gen ln_duration = ln(duration + 1)

* 处理发布日期，生成打磨周期（polishing_days）
* 尝试 A：pubdate 已是 Stata 日期数值
capture confirm numeric variable pubdate
if _rc == 0 {
    gen date = dofc(pubdate)
}
else {
    * 尝试 B：pubdate 是字符串格式 "DMY hms"
    gen double pubdate_num = clock(pubdate, "DMY hms")
    gen date = dofc(pubdate_num)
    drop pubdate_num
}
format date %td

* 打磨周期 = 相邻两条视频的发布间隔天数（同一UP主内部）
sort up_id date
gen polishing_days = date - date[_n-1] if up_id == up_id[_n-1]

* 对打磨周期取对数（压缩右偏分布）
* 变量名与第三章保持一致：ln_interval（论文3.3节命名）
gen ln_interval = ln(polishing_days + 1)

* 生成评论互动深度变量
* 论文H3定义：ln_comment = 评论数的对数值（而非评论字符数）
capture gen ln_comment = ln(reply + 1)   // reply 字段即视频评论数

* -------------------------------------------------------
* [Table 5-A] 机制一：投入互惠机制（打磨周期中介）H2
* 检验路径：投币激励 → 内容打磨周期(ln_interval) → 内容质量
* -------------------------------------------------------

* 第一步：投币激励 → 打磨周期（a 路径）
xtreg ln_interval L2_ln_coin L2_ln_like ///
      i.year i.month,                   ///
      fe vce(cluster up_id)
outreg2 using "Table_5A_Mechanism_Effort.doc", replace ///
        word dec(3) tstat                               ///
        title("Table 5A: Mechanism 1 — Polishing Period (H2a)")

* 第二步：投币激励 + 打磨周期 → 内容质量（b 路径 + c' 路径）
xtreg Quality_Index L2_ln_coin ln_interval L2_ln_like ///
      ln_duration ln_view i.year i.month,             ///
      fe vce(cluster up_id)
outreg2 using "Table_5A_Mechanism_Effort.doc", append  ///
        word dec(3) tstat                               ///
        addnote("a路径(H2a) + b/c'路径(H2b)。Sobel/Bootstrap中介检验需另行执行。* p<0.1, ** p<0.05, *** p<0.01")

* -------------------------------------------------------
* [Table 5-B] 机制二：深度反馈机制（评论互动深度中介）H3
* 检验路径：投币激励 → 评论互动深度(ln_comment) → 内容质量
* 变量说明：ln_comment = ln(total_comments+1)，total_comments为视频评论总数
* -------------------------------------------------------

* 第一步：投币激励 → 评论互动深度（a 路径）
gen ln_comment = ln(total_comments + 1)
xtreg ln_comment L2_ln_coin L2_ln_like ///
      i.year i.month,                  ///
      fe vce(cluster up_id)
outreg2 using "Table_5B_Mechanism_Feedback.doc", replace ///
        word dec(3) tstat                                  ///
        title("Table 5B: Mechanism 2 — Comment Depth (H3a)")

* 第二步：投币激励 + 评论互动深度 → 内容质量（b 路径 + c' 路径）
xtreg Quality_Index L2_ln_coin ln_comment L2_ln_like ///
      ln_duration ln_view i.year i.month,            ///
      fe vce(cluster up_id)
outreg2 using "Table_5B_Mechanism_Feedback.doc", append ///
        word dec(3) tstat                               ///
        addnote("a路径(H3a) + b/c'路径(H3b)。* p<0.1, ** p<0.05, *** p<0.01")

* -------------------------------------------------------
* [Table 5-C] 机制三：流量传播路径证伪检验 H4
* 检验路径：投币激励 → 分享数(ln_share) → 内容质量
* 理论预期：若 H4 成立，ln_share 对 Quality_Index 的 b 路径
*           系数应不显著，且引入 ln_share 后 L2_ln_coin 的
*           直接效应 c' 应保持稳健显著
* -------------------------------------------------------

* 第一步：投币激励 → 分享数（a 路径）
xtreg ln_share L2_ln_coin L2_ln_like ///
      i.year i.month,                ///
      fe vce(cluster up_id)
outreg2 using "Table_5C_Mechanism_Flow.doc", replace ///
        word dec(3) tstat                              ///
        title("Table 5C: Mechanism 3 — Traffic Falsification (H4)")

* 第二步：投币激励 + 分享数 → 内容质量（b 路径 + c' 路径）
xtreg Quality_Index L2_ln_coin ln_share L2_ln_like ///
      ln_duration ln_view i.year i.month,          ///
      fe vce(cluster up_id)
outreg2 using "Table_5C_Mechanism_Flow.doc", append ///
        word dec(3) tstat                            ///
        addnote("H4证伪检验：预期ln_share的b路径系数不显著。* p<0.1, ** p<0.05, *** p<0.01")


* =======================================================
* PART 7: 稳健性检验
* =======================================================

* --- 重新读取 step4 数据，避免机制数据变量污染 ---
import excel "step4_final_data.xlsx", firstrow clear

egen up_id = group(mid)
bysort up_id: gen t = _n
xtset up_id t

gen L2_ln_coin  = L2.ln_coin
gen L1_ln_coin  = L1.ln_coin
gen L2_ln_like  = L2.ln_like
gen L1_ln_like  = L1.ln_like
gen L2_ln_fav   = L2.ln_fav
capture gen ln_duration = ln(duration + 1)
capture gen ln_view     = ln(view + 1)
capture gen ln_fans     = ln(up_fans + 1)

* -------------------------------------------------------
* [Figure 1] 稳健性检验一：安慰剂检验（500次随机置换）
* -------------------------------------------------------
* 原理：随机打乱投币数据与视频的对应关系，若真实系数
*       远超置换分布，则排除随机因素导致显著性的可能

permute L2_ln_coin beta = _b[L2_ln_coin],    ///
        reps(500) seed(123)                   ///
        saving("placebo_results.dta", replace): ///
        xtreg Quality_Index L2_ln_coin L2_ln_like ///
              i.year i.month, fe

* 绘制安慰剂检验核密度图（红线标注真实系数 1.302）
use "placebo_results.dta", clear
#delimit ;
kdensity beta,
    xline(1.302, lcolor(red) lwidth(thick) lpattern(solid))
    xline(0,     lcolor(black) lwidth(medium) lpattern(dash))
    xscale(range(-0.5 1.6))
    xlabel(-0.5(0.5)1.5)
    xtitle("置换系数估计值")
    ytitle("核密度")
    legend(off)
    note("红色实线为真实估计系数（1.302）；虚线为零值参照线")
    scheme(s1mono);
#delimit cr
graph export "Figure_1_Placebo_Test.png", replace width(2400)

* 回到 step4 数据
import excel "step4_final_data.xlsx", firstrow clear
egen up_id = group(mid)
bysort up_id: gen t = _n
xtset up_id t
gen L2_ln_coin  = L2.ln_coin
gen L1_ln_coin  = L1.ln_coin
gen L2_ln_like  = L2.ln_like
gen L2_ln_fav   = L2.ln_fav
capture gen ln_duration = ln(duration + 1)
capture gen ln_view     = ln(view + 1)
capture gen ln_fans     = ln(up_fans + 1)

* -------------------------------------------------------
* [Table 6-A] 稳健性检验二：变量替换（秩变量替代对数变量）
* -------------------------------------------------------
* 原理：将投币数替换为其在月度截面内的排名百分位，
*       消除特定函数变换形式对结论的影响

sort year month
bysort year month: egen rank_tmp   = rank(L2_ln_coin)
bysort year month: egen count_tmp  = count(L2_ln_coin)
gen L2_coin_rank = (rank_tmp / count_tmp) * 100
drop rank_tmp count_tmp

sort up_id t
xtreg Quality_Index L2_coin_rank L2_ln_like L2_ln_fav ///
      ln_duration ln_view i.year i.month,              ///
      fe vce(cluster up_id)
est store Rank

outreg2 [Rank] using "Table_6A_Robustness_Rank.doc", replace ///
        word dec(3) tstat                                      ///
        title("Table 6A: Robustness — Rank Variable")         ///
        addnote("L2_coin_rank: percentile rank within year-month cross-section. * p<0.1, ** p<0.05, *** p<0.01")

* -------------------------------------------------------
* [Table 6-B] 稳健性检验三：滞后阶数对比
* （滞后一期 vs 滞后二期，验证基准模型选择的合理性）
* -------------------------------------------------------

* 滞后一期模型
xtreg Quality_Index L1_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view i.year i.month,            ///
      fe vce(cluster up_id)
est store Lag1

* 滞后二期模型（与基准一致，此处重跑以便并列输出）
xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view i.year i.month,            ///
      fe vce(cluster up_id)
est store Lag2

outreg2 [Lag1 Lag2] using "Table_6B_Robustness_Lag.doc", replace ///
        word dec(3) tstat                                           ///
        title("Table 6B: Robustness — Lag Order Comparison")       ///
        addnote("Lag1 = L1.ln_coin; Lag2 = L2.ln_coin (baseline). * p<0.1, ** p<0.05, *** p<0.01")

* -------------------------------------------------------
* [Table 6-C] 稳健性检验四：样本调整（剔除极端UP主）
* （剔除观测值最多的前5%和最少的后5%的UP主）
* -------------------------------------------------------
bysort up_id: gen obs_count = _N
sum obs_count, detail
scalar p5_val  = r(p5)
scalar p95_val = r(p95)

xtreg Quality_Index L2_ln_coin L2_ln_like L2_ln_fav ///
      ln_duration ln_view i.year i.month             ///
      if obs_count > p5_val & obs_count < p95_val,  ///
      fe vce(cluster up_id)
est store TrimSample

outreg2 [TrimSample] using "Table_6C_Robustness_Sample.doc", replace ///
        word dec(3) tstat                                               ///
        title("Table 6C: Robustness — Trimmed Sample")                 ///
        addnote("Excluded UP-hosts with obs count in bottom/top 5 percentile. * p<0.1, ** p<0.05, *** p<0.01")

* -------------------------------------------------------
* [Table 6-D] 稳健性检验五：外生冲击（新冠疫情交互项）
* （2020—2022 年为疫情冲击期，检验系数是否发生结构性变化）
* -------------------------------------------------------
gen covid           = (year >= 2020 & year <= 2022)
gen coin_covid_inter = L2_ln_coin * covid

sort up_id t
xtreg Quality_Index L2_ln_coin coin_covid_inter covid ///
      L2_ln_like L2_ln_fav                            ///
      ln_duration ln_view i.year i.month,             ///
      fe vce(cluster up_id)
est store CovidShock

outreg2 [CovidShock] using "Table_6D_Robustness_Shock.doc", replace ///
        word dec(3) tstat                                              ///
        title("Table 6D: Robustness — COVID-19 Shock")               ///
        addnote("covid = 1 if year in [2020,2022]. Interaction term tests structural break. * p<0.1, ** p<0.05, *** p<0.01")


* =======================================================
* 输出文件清单：
*   Table_0_Descriptive.doc       — 描述性统计
*   Table_1_Baseline.doc          — 基准逐步回归（4列）
*   Table_2_Lewbel_IV.doc         — 内生性检验
*   Table_3A_Hetero_Fans.doc      — 异质性：粉丝量级
*   Table_3B_Hetero_Duration.doc  — 异质性：视频时长
*   Table_4A_Nonlinear.doc        — 非线性效应
*   Table_4B_Interaction.doc      — 投币×点赞交互效应
*   Table_5A_Mechanism_Effort.doc — 机制一：打磨周期
*   Table_5B_Mechanism_Flow.doc   — 机制二：流量（证伪）
*   Table_5C_Mechanism_Feedback.doc — 机制三：评论深度
*   Table_6A_Robustness_Rank.doc  — 稳健性：秩变量
*   Table_6B_Robustness_Lag.doc   — 稳健性：滞后阶数对比
*   Table_6C_Robustness_Sample.doc — 稳健性：样本调整
*   Table_6D_Robustness_Shock.doc — 稳健性：疫情冲击
*   Figure_1_Placebo_Test.png     — 安慰剂检验核密度图
* =======================================================
