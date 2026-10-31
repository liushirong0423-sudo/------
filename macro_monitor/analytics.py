"""分析工具：归一化 / 统计 / 宏观情景诊断引擎 / 衰退概率模型"""
import pandas as pd
import plotly.graph_objects as go

def hex_to_rgba(hex_color: str, alpha: float = 0.08) -> str:
    """Convert #rrggbb to rgba(r,g,b,alpha)"""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def zscore(s: pd.Series) -> pd.Series:
    std = s.std()
    return (s - s.mean()) / std if std > 0 else s * 0

def minmax(s: pd.Series) -> pd.Series:
    mn, mx = s.min(), s.max()
    return (s - mn) / (mx - mn) if mx > mn else s * 0

def safe_val(df, col):
    if col not in df.columns:
        return None
    s = df[col].dropna()
    return float(s.iloc[-1]) if not s.empty else None

def daily_chg(df, col):
    if col not in df.columns:
        return None
    s = df[col].dropna()
    if len(s) < 2:
        return None
    return (s.iloc[-1] / s.iloc[-2] - 1) * 100

def add_bands(fig, s: pd.Series, row=1, col=1):
    mean, std = s.mean(), s.std()
    for n, alpha in [(2, 0.07), (1, 0.14)]:
        fig.add_trace(go.Scatter(
            x=list(s.index) + list(s.index[::-1]),
            y=[mean + n*std]*len(s) + [mean - n*std]*len(s),
            fill="toself",
            fillcolor=f"rgba(59,130,246,{alpha})",
            line=dict(color="rgba(0,0,0,0)"),
            name=f"±{n}σ通道", showlegend=True, hoverinfo="skip",
        ), row=row, col=col)
    fig.add_hline(
        y=mean, line_dash="dash", line_color="#374151", line_width=1,
        annotation_text=f"μ={mean:.2f}",
        annotation_font=dict(color="#475569", size=9),
        row=row, col=col,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 宏观情景诊断引擎
# ═══════════════════════════════════════════════════════════════════════════
def build_macro_regime(df_: pd.DataFrame, V_: dict, spread_102_) -> dict:
    """
    分析宏观指标，返回：
    regime, regime_color, regime_desc, regime_assets,
    signals, watch_list, anomalies
    """
    signals    = {}   # key → (icon, value_str, description)
    watch_list = []   # [(indicator, reason)]

    # ── 通胀 ──
    cpi  = V_.get("美国CPI同比")
    be10 = safe_val(df_, "10Y盈亏平衡通胀")
    if cpi is not None:
        if cpi > 4:
            signals["通胀"] = ("🔴", f"CPI {cpi:.1f}%", "高通胀：远超2%目标，货币政策收紧压力大")
            watch_list.append(("美国CPI同比", f"当前{cpi:.1f}%，远超2%目标，警惕加息预期持续抬升"))
        elif cpi > 2.5:
            signals["通胀"] = ("🟡", f"CPI {cpi:.1f}%", "通胀偏高：高于目标，粘性风险需关注")
            watch_list.append(("美国CPI同比", f"当前{cpi:.1f}%，通胀粘性，关注降息路径"))
        else:
            signals["通胀"] = ("🟢", f"CPI {cpi:.1f}%", "通胀受控：接近或低于2%目标")
    if be10 is not None and be10 > 2.5:
        watch_list.append(("10Y盈亏平衡通胀", f"市场通胀预期{be10:.2f}%，高于美联储目标，警惕脱锚"))

    # ── 就业/增长 ──
    unrate = V_.get("美国失业率")
    if unrate is not None:
        if unrate > 5.5:
            signals["就业"] = ("🔴", f"失业率 {unrate:.1f}%", "就业明显恶化：衰退信号确认")
            watch_list.append(("美国失业率", f"升至{unrate:.1f}%，衰退概率大幅上升"))
        elif unrate > 4.5:
            signals["就业"] = ("🟡", f"失业率 {unrate:.1f}%", "就业放缓：劳动市场降温，关注趋势")
            watch_list.append(("美国失业率", f"{unrate:.1f}%，关注就业趋势是否持续恶化"))
        else:
            signals["就业"] = ("🟢", f"失业率 {unrate:.1f}%", "就业健康：劳动市场依然强劲")

    # ── 收益率曲线 ──
    if spread_102_ is not None:
        if spread_102_ < -0.5:
            signals["收益率曲线"] = ("🔴", f"10Y-2Y={spread_102_:+.2f}%", "深度倒挂：历史预测衰退准确率极高，滞后12-18月")
            watch_list.append(("10Y-2Y利差", f"深度倒挂{spread_102_:+.2f}%，衰退风险极高"))
        elif spread_102_ < 0:
            signals["收益率曲线"] = ("🟡", f"10Y-2Y={spread_102_:+.2f}%", "轻度倒挂：衰退信号，需结合其他指标确认")
            watch_list.append(("10Y-2Y利差", f"倒挂{spread_102_:+.2f}%，保持持续关注"))
        elif spread_102_ < 0.5:
            signals["收益率曲线"] = ("🟡", f"10Y-2Y={spread_102_:+.2f}%", "曲线平坦：期限溢价偏低，市场预期增长放缓")
        else:
            signals["收益率曲线"] = ("🟢", f"10Y-2Y={spread_102_:+.2f}%", "曲线正常：期限溢价健康，经济预期良好")

    # ── 信用风险 ──
    hy = V_.get("美高收益债利差")
    if hy is not None:
        if hy > 600:
            signals["信用风险"] = ("🔴", f"HY={hy:.0f}bps", "信用极度压力：系统性风险高企，危机水平")
            watch_list.append(("美高收益债利差", f"HY利差{hy:.0f}bps，已达信用危机信号"))
        elif hy > 400:
            signals["信用风险"] = ("🟡", f"HY={hy:.0f}bps", "信用利差走阔：风险偏好下降，关注违约率")
            watch_list.append(("美高收益债利差", f"{hy:.0f}bps超400bps警戒线，需持续跟踪"))
        else:
            signals["信用风险"] = ("🟢", f"HY={hy:.0f}bps", "信用市场平稳：违约风险可控")

    # ── 市场波动率 ──
    vix = V_.get("VIX")
    if vix is not None:
        if vix > 35:
            signals["波动率"] = ("🔴", f"VIX={vix:.1f}", "极度恐慌：历史大底往往在此区间出现，短期风险极高")
            watch_list.append(("VIX恐慌指数", f"VIX={vix:.1f}，市场极度恐慌，系统性事件信号"))
        elif vix > 25:
            signals["波动率"] = ("🟡", f"VIX={vix:.1f}", "市场恐慌升温：突破25警戒线，注意风险敞口")
            watch_list.append(("VIX恐慌指数", f"突破25警戒线（当前{vix:.1f}），注意仓位管理"))
        elif vix > 18:
            signals["波动率"] = ("🟡", f"VIX={vix:.1f}", "波动率偏高：市场不确定性上升，注意节奏")
        else:
            signals["波动率"] = ("🟢", f"VIX={vix:.1f}", "低波动：市场情绪平稳，警惕自满情绪")

    # ── 美元 ──
    dxy = V_.get("美元指数")
    if dxy is not None:
        if dxy > 108:
            signals["美元"] = ("🔴", f"DXY={dxy:.1f}", "美元极强：新兴市场面临资本外流和债务压力")
            watch_list.append(("美元指数", f"DXY={dxy:.1f}，强美元压制新兴市场、大宗商品及人民币"))
        elif dxy > 104:
            signals["美元"] = ("🟡", f"DXY={dxy:.1f}", "美元偏强：全球流动性相对收紧")
        else:
            signals["美元"] = ("🟢", f"DXY={dxy:.1f}", "美元中性偏弱：有利于新兴市场和大宗商品")

    # ── 美联储流动性 ──
    if "美联储净流动性" in df_.columns:
        fl_s = df_["美联储净流动性"].dropna()
        if len(fl_s) > 1:
            fl_z = float(zscore(fl_s).iloc[-1])
            fl_v = float(fl_s.iloc[-1])
            if fl_z > 0.5:
                signals["流动性"] = ("🟢", f"{fl_v:,.0f}B$", "流动性宽裕：净流动性偏高，利好风险资产")
            elif fl_z < -0.5:
                signals["流动性"] = ("🔴", f"{fl_v:,.0f}B$", "流动性偏紧：净流动性偏低，压制风险资产")
                watch_list.append(("美联储净流动性", f"Z-Score={fl_z:+.2f}σ，流动性偏紧，关注市场承压"))
            else:
                signals["流动性"] = ("🟡", f"{fl_v:,.0f}B$", "流动性中性：关注后续美联储操作动向")

    # ── 中国经济 ──
    cn_pmi = safe_val(df_, "中国PMI制造业")
    if cn_pmi is None:
        cn_pmi = safe_val(df_, "财新PMI制造业")
    if cn_pmi is not None:
        if cn_pmi < 49:
            signals["中国PMI"] = ("🔴", f"PMI={cn_pmi:.1f}", "中国制造业萎缩：全球需求下行压力，大宗商品承压")
            watch_list.append(("中国PMI制造业", f"PMI={cn_pmi:.1f}，低于荣枯线，关注中国经济走弱的全球传导"))
        elif cn_pmi < 50.5:
            signals["中国PMI"] = ("🟡", f"PMI={cn_pmi:.1f}", "中国制造业接近荣枯线：经济动能偏弱，政策窗口期")
            watch_list.append(("中国PMI制造业", f"PMI={cn_pmi:.1f}，接近荣枯线，关注政策刺激力度"))
        else:
            signals["中国PMI"] = ("🟢", f"PMI={cn_pmi:.1f}", "中国制造业扩张：有利于大宗商品和全球需求")

    # ── 中美利差 ──
    cn_us_sp = safe_val(df_, "中美利差(10Y)")
    if cn_us_sp is not None:
        if cn_us_sp < -1.0:
            signals["中美利差"] = ("🔴", f"中美={cn_us_sp:+.2f}%", "美国相对中国利差大幅为正：资金明显流向美国，人民币承压")
            watch_list.append(("中美利差(10Y)", f"利差{cn_us_sp:+.2f}%，资金流出压力大，关注人民币汇率"))
        elif cn_us_sp < 0:
            signals["中美利差"] = ("🟡", f"中美={cn_us_sp:+.2f}%", "美国利率高于中国：资本流出压力存在")
        else:
            signals["中美利差"] = ("🟢", f"中美={cn_us_sp:+.2f}%", "中国利率高于美国：利差支撑人民币和A股外资流入")

    # ── Sahm 规则 ──
    sahm = safe_val(df_, "Sahm规则指标")
    if sahm is not None:
        if sahm >= 0.5:
            signals["Sahm规则"] = ("🔴", f"Sahm={sahm:.2f}", "已触发衰退：历史准确率接近100%，经济进入或即将进入衰退")
            watch_list.append(("Sahm规则指标", f"Sahm={sahm:.2f}≥0.5触发线，历史上每次衰退均被捕获"))
        elif sahm >= 0.3:
            signals["Sahm规则"] = ("🟡", f"Sahm={sahm:.2f}", "接近触发线：就业市场持续恶化，衰退前期信号增强")
            watch_list.append(("Sahm规则指标", f"Sahm={sahm:.2f}接近0.5触发线，就业趋势值得警惕"))
        else:
            signals["Sahm规则"] = ("🟢", f"Sahm={sahm:.2f}", "未触发：就业市场暂无衰退信号，Sahm < 0.3阈值")

    # ── 金融条件 (NFCI) ──
    nfci = safe_val(df_, "金融条件指数")
    if nfci is not None:
        if nfci > 0.3:
            signals["金融条件"] = ("🔴", f"NFCI={nfci:.3f}", "金融条件大幅收紧：信贷/股票/影子银行系统均承压")
            watch_list.append(("金融条件指数NFCI", f"={nfci:.3f}>0.3，金融条件显著偏紧，历史对应市场压力期"))
        elif nfci > 0:
            signals["金融条件"] = ("🟡", f"NFCI={nfci:.3f}", "金融条件偏紧：高于历史均值（0），信贷环境有压力")
        else:
            signals["金融条件"] = ("🟢", f"NFCI={nfci:.3f}", "金融条件宽松：低于历史均值，有利于信贷扩张")

    # ── 铜金比率（全球经济景气信号）──
    cg_ratio = safe_val(df_, "铜金比率")
    if cg_ratio is not None and "铜金比率" in df_.columns:
        cg_s = df_["铜金比率"].dropna()
        if len(cg_s) > 60:
            cg_z = float(zscore(cg_s).iloc[-1])
            if cg_z > 0.5:
                signals["铜金比率"] = ("🟢", f"铜金={cg_ratio:.3f}", "铜金比率偏高：全球需求旺盛，周期性资产占优")
            elif cg_z < -0.5:
                signals["铜金比率"] = ("🔴", f"铜金={cg_ratio:.3f}", "铜金比率偏低：避险主导，全球增长预期走弱")
                watch_list.append(("铜金比率", f"Z={cg_z:+.2f}σ，历史低位，全球需求不足信号"))
            else:
                signals["铜金比率"] = ("🟡", f"铜金={cg_ratio:.3f}", "铜金比率中性：经济景气度无明显方向")

    # ── 10Y-3M利差（NY Fed衰退概率核心变量）──
    sp10y3m = safe_val(df_, "10Y-3M利差")
    if sp10y3m is not None:
        _rp = recession_probability(sp10y3m)
        if sp10y3m < -0.5:
            signals["10Y-3M"] = ("🔴", f"={sp10y3m:+.2f}%", f"深度倒挂：NY Fed衰退概率约{_rp:.0f}%")
            watch_list.append(("10Y-3M利差", f"倒挂{sp10y3m:+.2f}%，衰退概率{_rp:.0f}%"))
        elif sp10y3m < 0:
            signals["10Y-3M"] = ("🟡", f"={sp10y3m:+.2f}%", f"轻度倒挂：衰退概率{_rp:.0f}%，需持续跟踪")
        else:
            signals["10Y-3M"] = ("🟢", f"={sp10y3m:+.2f}%", f"曲线健康：衰退概率仅{_rp:.0f}%，10Y>3M")

    # ── 宏观情景四象限判断 ──
    growth_ok   = signals.get("就业",      ("🟢",))[0] == "🟢"
    infla_high  = signals.get("通胀",      ("🟢",))[0] in ("🔴", "🟡")
    be10_high   = be10 > 2.5 if be10 is not None else False

    if growth_ok and not (infla_high or be10_high):
        regime       = "Goldilocks · 金发女孩"
        regime_color = "#22c55e"
        regime_desc  = ("经济增长健康，通胀受控。历史上最有利于风险资产的宏观组合。"
                        "成长股、科技股、信用债均倾向表现良好，建议适度偏多风险资产。")
        regime_assets = {
            "美股":   "🟢 超配（成长/科技）",
            "A股":    "🟢 超配",
            "港股":   "🟢 超配",
            "黄金":   "🟡 中性",
            "大宗商品": "🟡 中性",
            "长期国债": "🟡 中性",
            "现金":   "🔴 低配",
        }
    elif growth_ok and (infla_high or be10_high):
        regime       = "Reflation · 再通胀"
        regime_color = "#f59e0b"
        regime_desc  = ("经济扩张但通胀压力上升。有利于周期性资产、大宗商品和TIPS，"
                        "名义长债承压，成长股相对价值股劣势。关注货币政策转向时点。")
        regime_assets = {
            "美股":   "🟡 中性（偏周期/价值）",
            "A股":    "🟡 关注政策节奏",
            "港股":   "🟡 中性",
            "黄金":   "🟡 中性（TIPS更优）",
            "大宗商品": "🟢 超配（能源/铜）",
            "长期国债": "🔴 低配",
            "现金":   "🟡 中性",
        }
    elif not growth_ok and (infla_high or be10_high):
        regime       = "Stagflation · 滞胀"
        regime_color = "#ef4444"
        regime_desc  = ("经济放缓但通胀高企，是最难应对的宏观环境。黄金、能源类大宗商品和"
                        "短久期债券相对抗跌，股票（尤其成长股）和长债均承压，建议提高防御性。")
        regime_assets = {
            "美股":   "🔴 低配（防御为主）",
            "A股":    "🔴 谨慎",
            "港股":   "🔴 谨慎",
            "黄金":   "🟢 超配",
            "大宗商品": "🟢 超配（能源）",
            "长期国债": "🔴 低配",
            "现金":   "🟢 超配",
        }
    else:
        regime       = "Deflation · 通缩/衰退"
        regime_color = "#3b82f6"
        regime_desc  = ("经济萎缩，通胀下行。长期国债、黄金和防御性股票通常有较好表现，"
                        "高收益债和周期股承压。等待政策宽松信号（降息/QE）再布局风险资产。")
        regime_assets = {
            "美股":   "🟡 防御板块为主",
            "A股":    "🟡 政策刺激预期",
            "港股":   "🟡 谨慎",
            "黄金":   "🟢 超配",
            "大宗商品": "🔴 低配",
            "长期国债": "🟢 超配",
            "现金":   "🟢 超配",
        }

    # ── 异常偏离检测（Z-Score绝对值最大的8个指标）──
    anomalies = []
    for col in df_.columns:
        s = df_[col].dropna()
        if len(s) < 30 or col.endswith("_PE"):
            continue
        zs = float(zscore(s).iloc[-1])
        if abs(zs) > 1.5:
            anomalies.append((col, zs, float(s.iloc[-1])))
    anomalies.sort(key=lambda x: abs(x[1]), reverse=True)
    anomalies = anomalies[:8]

    # ── 综合风险评分（满分15分）──
    risk_score = 0
    for key, thr_r, thr_y in [
        ("通胀",       2, 1), ("就业",    2, 1), ("收益率曲线", 2, 1),
        ("信用风险",   2, 1), ("波动率",  2, 1), ("流动性",    1, 0),
        ("Sahm规则",   2, 1), ("金融条件", 1, 0),
    ]:
        icon = signals.get(key, ("🟢",))[0]
        risk_score += thr_r if icon == "🔴" else (thr_y if icon == "🟡" else 0)

    return {
        "regime":        regime,
        "regime_color":  regime_color,
        "regime_desc":   regime_desc,
        "regime_assets": regime_assets,
        "signals":       signals,
        "watch_list":    watch_list[:10],
        "anomalies":     anomalies,
        "risk_score":    risk_score,
    }


def recession_probability(spread_10y_3m) -> float:
    """
    基于纽约联储 Probit 模型估算未来 12 个月衰退概率 (0–100%)。
    参考: Estrella & Mishkin (1998), NY Fed yield curve research。
    模型：P = Φ(α + β·spread), α=-0.5779, β=-0.8045
    当 10Y-3M < 0（倒挂）时概率明显升高。
    """
    if spread_10y_3m is None:
        return 0.0
    import math
    z = -0.5779 + (-0.8045) * float(spread_10y_3m)
    return float((1.0 + math.erf(z / math.sqrt(2.0))) / 2.0 * 100.0)
