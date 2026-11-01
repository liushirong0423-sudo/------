"TAB 0 — 整体研判：经济情况、资产情况、投资建议与理由"
import streamlit as st
import pandas as pd

from ..analytics import build_macro_regime, safe_val, zscore, recession_probability


def _fmt(v, unit="", fmt="{:.2f}"):
    return "—" if v is None else fmt.format(v) + unit


def render(df, V, spread_10_2):
    mc = build_macro_regime(df, V, spread_10_2)

    # ── 风险评分配色 ─────────────────────────────────────────────────────
    _rs = mc["risk_score"]
    _rs_color = ("#ef4444" if _rs >= 11 else
                 "#f59e0b" if _rs >= 7 else
                 "#3b82f6" if _rs >= 4 else "#22c55e")
    _rs_label = ("极高风险" if _rs >= 11 else
                 "高风险"   if _rs >= 7 else
                 "中等风险" if _rs >= 4 else "低风险")
    _reg_col = mc["regime_color"]

    _n_red = sum(1 for v in mc["signals"].values() if v[0] == "🔴")
    _n_yel = sum(1 for v in mc["signals"].values() if v[0] == "🟡")
    _n_grn = sum(1 for v in mc["signals"].values() if v[0] == "🟢")

    # ═══════════════════════════════════════════════════════════════════════
    # ① 宏观经济总览 Hero
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🌐 宏观经济与资产总览</div>',
                unsafe_allow_html=True)

    _hero_l, _hero_m, _hero_r = st.columns([2, 1, 2])

    with _hero_l:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0d1321,{_reg_col}15);
                    border:1px solid {_reg_col}55;border-radius:14px;padding:28px;">
          <div style="font-size:10px;color:#475569;text-transform:uppercase;
                      letter-spacing:1.5px;font-weight:700;">当前宏观情景</div>
          <div style="font-size:30px;font-weight:800;color:{_reg_col};
                      margin:10px 0 10px;line-height:1.1;">{mc['regime']}</div>
          <div style="font-size:13px;color:#94a3b8;line-height:1.8;">{mc['regime_desc']}</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px;">
            <span style="background:#ef444420;color:#ef4444;border:1px solid #ef444440;
                         border-radius:20px;padding:3px 12px;font-size:11px;font-weight:700;">
              🔴 异常 {_n_red}</span>
            <span style="background:#f59e0b20;color:#f59e0b;border:1px solid #f59e0b40;
                         border-radius:20px;padding:3px 12px;font-size:11px;font-weight:700;">
              🟡 预警 {_n_yel}</span>
            <span style="background:#22c55e20;color:#22c55e;border:1px solid #22c55e40;
                         border-radius:20px;padding:3px 12px;font-size:11px;font-weight:700;">
              🟢 正常 {_n_grn}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with _hero_m:
        _pct_bar = min(100, _rs / 15 * 100)
        st.markdown(f"""
        <div style="background:#0d1321;border:1px solid {_rs_color}55;
                    border-radius:14px;padding:28px;text-align:center;">
          <div style="font-size:10px;color:#475569;text-transform:uppercase;
                      letter-spacing:1.5px;font-weight:700;">综合风险评分</div>
          <div style="font-size:56px;font-weight:900;color:{_rs_color};
                      margin:6px 0 0;line-height:1;">{_rs}</div>
          <div style="font-size:13px;color:{_rs_color};font-weight:700;margin:6px 0 16px;">
            / 15 · {_rs_label}</div>
          <div style="background:#1e2a3a;border-radius:6px;height:10px;overflow:hidden;">
            <div style="background:linear-gradient(90deg,#22c55e 0%,#f59e0b 50%,#ef4444 100%);
                        width:100%;height:100%;position:relative;">
              <div style="position:absolute;top:0;bottom:0;right:0;
                          background:#0d1321;width:{100-_pct_bar:.0f}%;"></div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin-top:18px;">
            <div style="background:#ef444415;border-radius:8px;padding:10px 4px;">
              <div style="font-size:24px;font-weight:800;color:#ef4444;">{_n_red}</div>
              <div style="font-size:9px;color:#64748b;">异常</div>
            </div>
            <div style="background:#f59e0b15;border-radius:8px;padding:10px 4px;">
              <div style="font-size:24px;font-weight:800;color:#f59e0b;">{_n_yel}</div>
              <div style="font-size:9px;color:#64748b;">预警</div>
            </div>
            <div style="background:#22c55e15;border-radius:8px;padding:10px 4px;">
              <div style="font-size:24px;font-weight:800;color:#22c55e;">{_n_grn}</div>
              <div style="font-size:9px;color:#64748b;">正常</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    with _hero_r:
        # 资产配置建议表
        _rows_html = ""
        for _asset, _sig in mc["regime_assets"].items():
            _ac = ("#22c55e" if "超配" in _sig else
                   "#ef4444" if any(x in _sig for x in ["低配", "谨慎"]) else
                   "#f59e0b")
            _rows_html += (
                f'<tr style="border-bottom:1px solid #1e2a3a;">'
                f'<td style="padding:9px 14px;color:#cbd5e1;font-size:13px;white-space:nowrap;">{_asset}</td>'
                f'<td style="padding:9px 14px;"><span style="color:{_ac};font-size:13px;font-weight:700;">{_sig}</span></td></tr>'
            )
        st.markdown(f"""
        <div style="background:#0d1321;border:1px solid #1e2a3a;border-radius:14px;padding:20px;">
          <div style="font-size:11px;color:#475569;text-transform:uppercase;
                      letter-spacing:1px;font-weight:700;margin-bottom:10px;">
            💼 各大类资产配置参考信号</div>
          <table style="width:100%;border-collapse:collapse;">
            <thead><tr style="background:#111827;">
              <th style="padding:8px 14px;color:#64748b;font-size:10px;text-align:left;
                         text-transform:uppercase;letter-spacing:0.8px;font-weight:700;
                         border-bottom:1px solid #1e2a3a;">资产类别</th>
              <th style="padding:8px 14px;color:#64748b;font-size:10px;text-align:left;
                         text-transform:uppercase;letter-spacing:0.8px;font-weight:700;
                         border-bottom:1px solid #1e2a3a;">配置建议</th>
            </tr></thead>
            <tbody>{_rows_html}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # ② 经济情况研判
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">📊 经济情况研判</div>', unsafe_allow_html=True)
    st.caption("基于通胀、就业、增长、流动性、收益率曲线等核心维度的综合判断")

    # 取关键数值
    cpi    = V.get("美国CPI同比")
    cn_cpi = safe_val(df, "中国CPI同比")
    ppi    = safe_val(df, "中国PPI同比")
    unrate = V.get("美国失业率")
    sahm   = safe_val(df, "Sahm规则指标")
    cn_pmi = safe_val(df, "中国PMI制造业")
    if cn_pmi is None:
        cn_pmi = safe_val(df, "财新PMI制造业")
    nfci   = safe_val(df, "金融条件指数")
    stlfs  = safe_val(df, "金融压力指数")
    be10   = safe_val(df, "10Y盈亏平衡通胀")
    sp10y3m = safe_val(df, "10Y-3M利差")
    rp_12m = recession_probability(sp10y3m) if sp10y3m is not None else None

    def _card(title, value, unit, desc, level):
        c = {"red": "#ef4444", "yellow": "#f59e0b", "green": "#22c55e", "blue": "#3b82f6"}[level]
        return f"""
        <div style="background:#0d1321;border:1px solid {c}33;border-left:4px solid {c};
                    border-radius:10px;padding:14px 16px;height:100%;">
          <div style="font-size:10px;color:#475569;text-transform:uppercase;
                      letter-spacing:0.8px;font-weight:700;">{title}</div>
          <div style="font-size:24px;font-weight:800;color:#f8fafc;margin:6px 0 2px;">
            {_fmt(value, unit)}
          </div>
          <div style="font-size:11px;color:#94a3b8;line-height:1.5;">{desc}</div>
        </div>"""

    _e1 = st.columns(4)
    _e1[0].markdown(_card(
        "美国通胀 (CPI YoY)", cpi, "%",
        ("远超2%目标，收紧压力大" if cpi and cpi > 4 else
         "偏高，粘性风险" if cpi and cpi > 2.5 else
         "受控，接近目标" if cpi else "数据缺失"),
        "red" if cpi and cpi > 4 else "yellow" if cpi and cpi > 2.5 else "green"
    ), unsafe_allow_html=True)
    _e1[1].markdown(_card(
        "市场通胀预期 (10Y BE)", be10, "%",
        ("高于目标，警惕脱锚" if be10 and be10 > 2.5 else
         "预期稳定" if be10 else "数据缺失"),
        "red" if be10 and be10 > 2.5 else "green"
    ), unsafe_allow_html=True)
    _e1[2].markdown(_card(
        "美国失业率", unrate, "%",
        ("就业恶化，衰退信号" if unrate and unrate > 5.5 else
         "就业放缓" if unrate and unrate > 4.5 else
         "就业强劲" if unrate else "数据缺失"),
        "red" if unrate and unrate > 5.5 else "yellow" if unrate and unrate > 4.5 else "green"
    ), unsafe_allow_html=True)
    _e1[3].markdown(_card(
        "Sahm 规则指标", sahm, "",
        ("已触发衰退（≥0.5）" if sahm and sahm >= 0.5 else
         "接近触发线" if sahm and sahm >= 0.3 else
         "未触发，就业无衰退信号" if sahm else "数据缺失"),
        "red" if sahm and sahm >= 0.5 else "yellow" if sahm and sahm >= 0.3 else "green"
    ), unsafe_allow_html=True)

    _e2 = st.columns(4)
    _e2[0].markdown(_card(
        "中国制造业 PMI", cn_pmi, "",
        ("制造业萎缩，需求承压" if cn_pmi and cn_pmi < 49 else
         "接近荣枯线，动能偏弱" if cn_pmi and cn_pmi < 50.5 else
         "制造业扩张" if cn_pmi else "数据缺失"),
        "red" if cn_pmi and cn_pmi < 49 else "yellow" if cn_pmi and cn_pmi < 50.5 else "green"
    ), unsafe_allow_html=True)
    _e2[1].markdown(_card(
        "中国 PPI 同比", ppi, "%",
        ("工业品通缩加剧" if ppi and ppi < -3 else
         "工业品价格下行" if ppi and ppi < 0 else
         "工业品价格上涨" if ppi else "数据缺失"),
        "blue" if ppi and ppi < 0 else "red" if ppi and ppi > 5 else "green"
    ), unsafe_allow_html=True)
    _e2[2].markdown(_card(
        "金融条件指数 NFCI", nfci, "",
        ("金融条件大幅收紧" if nfci and nfci > 0.3 else
         "金融条件偏紧" if nfci and nfci > 0 else
         "金融条件宽松" if nfci else "数据缺失"),
        "red" if nfci and nfci > 0.3 else "yellow" if nfci and nfci > 0 else "green"
    ), unsafe_allow_html=True)
    _e2[3].markdown(_card(
        "12个月衰退概率", rp_12m, "%",
        (f"收益率曲线深度倒挂" if sp10y3m and sp10y3m < -0.5 else
         f"曲线倒挂，需警惕" if sp10y3m and sp10y3m < 0 else
         f"曲线健康" if sp10y3m else "数据缺失"),
        "red" if rp_12m and rp_12m > 40 else "yellow" if rp_12m and rp_12m > 20 else "green"
    ), unsafe_allow_html=True)

    _e3 = st.columns(4)
    _e3[0].markdown(_card(
        "10Y-2Y 利差", spread_10_2, "%",
        ("深度倒挂，强衰退信号" if spread_10_2 and spread_10_2 < -0.5 else
         "轻度倒挂" if spread_10_2 and spread_10_2 < 0 else
         "曲线正常" if spread_10_2 else "数据缺失"),
        "red" if spread_10_2 and spread_10_2 < -0.5 else
        "yellow" if spread_10_2 and spread_10_2 < 0 else "green"
    ), unsafe_allow_html=True)
    _e3[1].markdown(_card(
        "美元指数 DXY", V.get("美元指数"), "",
        ("极强，新兴市场承压" if V.get("美元指数") and V["美元指数"] > 108 else
         "偏强，流动性收紧" if V.get("美元指数") and V["美元指数"] > 104 else
         "中性偏弱，利好大宗" if V.get("美元指数") else "数据缺失"),
        "red" if V.get("美元指数") and V["美元指数"] > 108 else
        "yellow" if V.get("美元指数") and V["美元指数"] > 104 else "green"
    ), unsafe_allow_html=True)
    _e3[2].markdown(_card(
        "VIX 恐慌指数", V.get("VIX"), "",
        ("极度恐慌，系统性风险" if V.get("VIX") and V["VIX"] > 35 else
         "恐慌升温" if V.get("VIX") and V["VIX"] > 25 else
         "低波动，情绪平稳" if V.get("VIX") else "数据缺失"),
        "red" if V.get("VIX") and V["VIX"] > 35 else
        "yellow" if V.get("VIX") and V["VIX"] > 25 else "green"
    ), unsafe_allow_html=True)
    _e3[3].markdown(_card(
        "HY 信用利差", V.get("美高收益债利差"), "bps",
        ("信用危机水平" if V.get("美高收益债利差") and V["美高收益债利差"] > 600 else
         "利差走阔，风险偏好降" if V.get("美高收益债利差") and V["美高收益债利差"] > 400 else
         "信用市场平稳" if V.get("美高收益债利差") else "数据缺失"),
        "red" if V.get("美高收益债利差") and V["美高收益债利差"] > 600 else
        "yellow" if V.get("美高收益债利差") and V["美高收益债利差"] > 400 else "green"
    ), unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # ③ 资产情况
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">💎 资产情况评估</div>', unsafe_allow_html=True)
    st.caption("当前主要资产的价格水平、估值与趋势信号")

    # 派生指标
    csi_pe = safe_val(df, "沪深300_PE")
    cg_ratio = safe_val(df, "铜金比率")
    gsr = safe_val(df, "金银比率")
    ogr = safe_val(df, "油金比率")
    cn_us_sp = safe_val(df, "中美利差(10Y)")
    m1_m2 = safe_val(df, "M1-M2剪刀差")
    tips10 = V.get("TIPS_10Y实际利率")

    def _asset_card(name, value, unit, status, reason, level):
        c = {"red": "#ef4444", "yellow": "#f59e0b", "green": "#22c55e", "blue": "#3b82f6"}[level]
        return f"""
        <div style="background:#0d1321;border:1px solid {c}33;border-radius:10px;
                    padding:16px;height:100%;">
          <div style="display:flex;justify-content:space-between;align-items:baseline;">
            <span style="font-size:12px;color:#94a3b8;font-weight:600;">{name}</span>
            <span style="font-size:10px;color:{c};font-weight:700;border:1px solid {c}55;
                         background:{c}15;border-radius:12px;padding:1px 8px;">{status}</span>
          </div>
          <div style="font-size:22px;font-weight:800;color:#f8fafc;margin:8px 0 6px;">
            {_fmt(value, unit)}
          </div>
          <div style="font-size:11px;color:#64748b;line-height:1.5;">{reason}</div>
        </div>"""

    _a1 = st.columns(4)
    # 美股
    spx = V.get("标普500")
    spx_lvl = "green"
    spx_status = "趋势偏强"
    spx_reason = "风险资产受益于当前宏观组合"
    if mc["regime"].startswith("Stagflation") or mc["regime"].startswith("Deflation"):
        spx_lvl = "yellow"
        spx_status = "承压"
        spx_reason = "滞胀/通缩环境下股票承压"
    _a1[0].markdown(_asset_card("标普500", spx, "点", spx_status, spx_reason, spx_lvl),
                    unsafe_allow_html=True)
    # A股
    a_lvl = "green" if csi_pe and csi_pe < 14 else "yellow" if csi_pe else "blue"
    a_status = "估值偏低" if csi_pe and csi_pe < 14 else "估值中性" if csi_pe else "数据待补"
    a_reason = f"PE={csi_pe:.1f}，" + ("处于历史低位，安全边际较高" if csi_pe and csi_pe < 14 else
                                       "估值合理" if csi_pe else "暂无PE数据")
    _a1[1].markdown(_asset_card("沪深300", V.get("沪深300"), "点", a_status, a_reason, a_lvl),
                    unsafe_allow_html=True)
    # 黄金
    au_lvl = "green" if mc["regime"].startswith(("Stagflation", "Deflation")) else "yellow"
    au_status = "避险配置价值高" if au_lvl == "green" else "中性"
    au_reason = ("滞胀/通缩环境下黄金保值避险功能凸显" if au_lvl == "green" else
                 "通胀受控环境下黄金吸引力一般")
    _a1[2].markdown(_asset_card("黄金", V.get("黄金"), "$/oz", au_status, au_reason, au_lvl),
                    unsafe_allow_html=True)
    # 原油
    oil_lvl = "green" if mc["regime"].startswith(("Reflation", "Stagflation")) else "red"
    oil_status = "通胀受益" if oil_lvl == "green" else "需求承压"
    oil_reason = ("再通胀/滞胀期能源商品受益" if oil_lvl == "green" else
                  "通缩期需求走弱压制油价")
    _a1[3].markdown(_asset_card("原油WTI", V.get("原油WTI"), "$/桶", oil_status, oil_reason, oil_lvl),
                    unsafe_allow_html=True)

    _a2 = st.columns(4)
    # 美国长债
    bond_lvl = "green" if mc["regime"].startswith("Deflation") else "red" if mc["regime"].startswith(("Reflation", "Stagflation")) else "yellow"
    bond_status = "避险首选" if bond_lvl == "green" else "承压" if bond_lvl == "red" else "中性"
    bond_reason = ("通缩期降息预期推升长债价格" if bond_lvl == "green" else
                   "通胀/再通胀期长债收益率上行、价格承压" if bond_lvl == "red" else
                   "金发女孩期债市机会有限")
    _a2[0].markdown(_asset_card("美国10Y国债", V.get("10Y美债"), "%", bond_status, bond_reason, bond_lvl),
                    unsafe_allow_html=True)
    # 中国10Y
    cn_bond_lvl = "green" if cn_us_sp and cn_us_sp < 0 else "yellow"
    _a2[1].markdown(_asset_card(
        "中国10Y国债", V.get("中国10Y国债"), "%",
        "利差支撑" if cn_bond_lvl == "green" else "中性",
        ("中美利差倒挂，国内利率相对有吸引力" if cn_us_sp and cn_us_sp < 0 else
         "中美利差为正，关注外资流向"), cn_bond_lvl
    ), unsafe_allow_html=True)
    # 铜金比率
    cg_lvl = "green" if cg_ratio and cg_ratio > 0.25 else "red" if cg_ratio and cg_ratio < 0.18 else "yellow"
    _a2[2].markdown(_asset_card(
        "铜金比率", cg_ratio, "",
        "风险偏好强" if cg_lvl == "green" else "避险主导" if cg_lvl == "red" else "中性",
        ("铜强金弱，全球增长预期向好" if cg_lvl == "green" else
         "金强铜弱，衰退担忧升温" if cg_lvl == "red" else
         "信号不明确"), cg_lvl
    ), unsafe_allow_html=True)
    # 金银比率
    gsr_lvl = "yellow"
    gsr_status = "中性"
    gsr_reason = "金银比率处于历史中性区间"
    if gsr and gsr > 85:
        gsr_lvl = "green"
        gsr_status = "白银低估"
        gsr_reason = "金银比率极高，白银相对黄金被低估，反弹概率大"
    elif gsr and gsr < 60:
        gsr_lvl = "red"
        gsr_status = "白银高估"
        gsr_reason = "金银比率极低，白银相对黄金偏贵，注意回调风险"
    _a2[3].markdown(_asset_card("金银比率", gsr, "", gsr_status, gsr_reason, gsr_lvl),
                    unsafe_allow_html=True)

    _a3 = st.columns(4)
    # 实际利率
    _a3[0].markdown(_asset_card(
        "10Y TIPS 实际利率", tips10, "%",
        "持有黄金机会成本高" if tips10 and tips10 > 1.5 else "有利黄金" if tips10 and tips10 < 0.5 else "中性",
        ("实际利率高企压制黄金估值" if tips10 and tips10 > 1.5 else
         "实际利率偏低，利好无息资产黄金" if tips10 and tips10 < 0.5 else
         "实际利率中性"), "red" if tips10 and tips10 > 1.5 else "green" if tips10 and tips10 < 0.5 else "yellow"
    ), unsafe_allow_html=True)
    # 中美利差
    _a3[1].markdown(_asset_card(
        "中美利差(10Y)", cn_us_sp, "%",
        "人民币承压" if cn_us_sp and cn_us_sp < -1 else "资本流出压力" if cn_us_sp and cn_us_sp < 0 else "利差支撑",
        ("美国利率大幅高于中国，资金外流压力大" if cn_us_sp and cn_us_sp < -1 else
         "美国利率高于中国，存在流出压力" if cn_us_sp and cn_us_sp < 0 else
         "中国利率高于美国，利好人民币与A股外资流入"),
        "red" if cn_us_sp and cn_us_sp < -1 else "yellow" if cn_us_sp and cn_us_sp < 0 else "green"
    ), unsafe_allow_html=True)
    # M1-M2剪刀差
    _a3[2].markdown(_asset_card(
        "M1-M2 剪刀差", m1_m2, "%",
        "企业活期活跃" if m1_m2 and m1_m2 > 0 else "资金定期化",
        ("M1>M2，企业活期存款活跃，经济活力强" if m1_m2 and m1_m2 > 0 else
         "M1<M2，资金定期化，需求偏弱，关注政策刺激"),
        "green" if m1_m2 and m1_m2 > 0 else "yellow"
    ), unsafe_allow_html=True)
    # 油金比率
    ogr_lvl = "yellow"
    ogr_status = "中性"
    ogr_reason = "油金比率处于合理区间"
    if ogr and ogr > 1.0:
        ogr_lvl = "red"
        ogr_status = "通胀过热信号"
        ogr_reason = "油金比率极端高位，反映通胀过热或供给冲击"
    elif ogr and ogr < 0.4:
        ogr_lvl = "green"
        ogr_status = "需求极弱"
        ogr_reason = "油金比率极低，需求极度疲软，可能处于周期底部"
    _a3[3].markdown(_asset_card("油金比率", ogr, "", ogr_status, ogr_reason, ogr_lvl),
                    unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # ④ 投资建议与理由
    # ═══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🎯 适合投资的资产及理由</div>', unsafe_allow_html=True)
    st.caption("基于当前宏观情景与各资产信号的综合研判，给出方向性配置建议")

    # 生成推荐理由
    recommend = []
    for _asset, _sig in mc["regime_assets"].items():
        if "超配" in _sig:
            recommend.append((_asset, _sig, "green"))
        elif any(x in _sig for x in ["低配", "谨慎"]):
            recommend.append((_asset, _sig, "red"))
        else:
            recommend.append((_asset, _sig, "yellow"))

    # 构建详细理由
    reason_map = {
        "美股": ("成长/科技股在流动性宽松与盈利增长期表现突出；"
                 "滞胀期盈利下修与估值压缩双重压力，建议防御板块为主。"),
        "A股": ("估值处于历史低位叠加政策刺激预期，安全边际较高；"
                "关注M1-M2剪刀差转正与社融放量信号确认拐点。"),
        "港股": ("低估值+高股息提供安全垫，但受外资流向与美元指数影响较大；"
                 "美元走弱时港股弹性显著。"),
        "黄金": ("实际利率下行、央行购金、地缘避险三重支撑；"
                 "滞胀与通缩环境下均是首选避险资产。"),
        "大宗商品": ("再通胀期能源与工业金属受益于需求复苏；"
                     "通缩期需求走弱则承压，关注铜金比率方向。"),
        "长期国债": ("通缩/衰退期降息预期推升长债价格；"
                     "再通胀/滞胀期收益率上行压制债价，建议短久期。"),
        "现金": ("高风险期现金为王，等待更好的布局时点；"
                 "低风险期现金机会成本较高，应适度投入风险资产。"),
    }

    _cols_rec = st.columns(3)
    for _i, (_asset, _sig, _lvl) in enumerate(recommend):
        _c = {"red": "#ef4444", "yellow": "#f59e0b", "green": "#22c55e"}[_lvl]
        _reason = reason_map.get(_asset, "")
        _cols_rec[_i % 3].markdown(f"""
        <div style="background:linear-gradient(135deg,#0d1321,{_c}10);
                    border:1px solid {_c}44;border-radius:12px;padding:18px;margin:6px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:16px;font-weight:800;color:#f8fafc;">{_asset}</span>
            <span style="font-size:12px;font-weight:700;color:{_c};
                         border:1px solid {_c}55;background:{_c}15;
                         border-radius:12px;padding:2px 10px;">{_sig}</span>
          </div>
          <div style="font-size:11px;color:#94a3b8;line-height:1.7;margin-top:10px;">
            {_reason}
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════
    # ⑤ 重点关注与异常
    # ═══════════════════════════════════════════════════════════════════════
    _wl_col, _an_col = st.columns([1, 1])

    with _wl_col:
        st.markdown('<div class="section-title">📌 重点关注指标</div>', unsafe_allow_html=True)
        if mc["watch_list"]:
            for _ind, _reason in mc["watch_list"][:6]:
                st.markdown(
                    f'<div class="alert-card alert-yellow" style="margin:5px 0;">'
                    f'<div class="alert-title">📍 {_ind}</div>'
                    f'<div class="alert-desc">{_reason}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown('<div style="color:#22c55e;font-size:13px;">暂无触发预警的指标</div>',
                        unsafe_allow_html=True)

    with _an_col:
        st.markdown('<div class="section-title">⚡ 极端偏离指标</div>', unsafe_allow_html=True)
        if mc["anomalies"]:
            _anom_rows = []
            for _col_a, _zs_a, _val_a in mc["anomalies"][:6]:
                _anom_rows.append({
                    "指标": _col_a,
                    "当前值": f"{_val_a:.4g}",
                    "Z-Score": f"{_zs_a:+.2f}σ",
                    "方向": ("📈 偏高" if _zs_a > 0 else "📉 偏低"),
                })
            st.dataframe(pd.DataFrame(_anom_rows), use_container_width=True, hide_index=True, height=240)
        else:
            st.markdown('<div style="color:#22c55e;font-size:13px;">当前无显著极端偏离指标</div>',
                        unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # ⑥ 一句话总结
    # ═══════════════════════════════════════════════════════════════════════
    _top_assets = [a for a, s in mc["regime_assets"].items() if "超配" in s]
    _avoid_assets = [a for a, s in mc["regime_assets"].items() if any(x in s for x in ["低配", "谨慎"])]
    _summary = (
        f"当前处于「{mc['regime']}」环境，综合风险评分 {_rs}/15（{_rs_label}）。"
        f"{'建议超配：' + '、'.join(_top_assets) + '。' if _top_assets else ''}"
        f"{'建议低配/谨慎：' + '、'.join(_avoid_assets) + '。' if _avoid_assets else ''}"
    )
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0d1321,#111827);
                border:1px solid {_reg_col}55;border-radius:12px;padding:20px;margin-top:8px;">
      <div style="font-size:11px;color:#475569;text-transform:uppercase;
                  letter-spacing:1px;font-weight:700;margin-bottom:8px;">📋 一句话研判</div>
      <div style="font-size:15px;color:#e2e8f0;line-height:1.8;">{_summary}</div>
      <div style="font-size:10px;color:#374151;margin-top:12px;padding-top:10px;
                  border-top:1px solid #1e2a3a;">
        ⚠ 免责声明：本研判基于量化模型与历史规律，仅供研究参考，不构成任何投资建议。市场有风险，投资须谨慎。
      </div>
    </div>
    """, unsafe_allow_html=True)
