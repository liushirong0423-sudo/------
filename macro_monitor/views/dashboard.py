"TAB 1 — 风险仪表盘：警报系统、KPI 速览、宏观情景引擎、净流动性"
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..analytics import build_macro_regime, daily_chg, safe_val, zscore
from ..charts import mk_layout, secondary_y_axis
from ..components import kpi
from ..config import GRID



def render(df):
    # 取值
    V = {k: safe_val(df, k) for k in [
        "纳斯达克100","标普500","MSCI新兴市场","VIX","10Y美债","2Y美债",
        "美元指数","黄金","原油WTI","中国10Y国债",
        "沪深300","上证综指","创业板指","美联储净流动性","美高收益债利差",
        "TIPS_10Y实际利率","美国CPI同比","美国失业率","中美利差(10Y)",
        "联邦基金利率",
    ]}
    CHG = {k: daily_chg(df, k) for k in V}

    spread_10_2 = (
        V["10Y美债"] - V["2Y美债"]
        if V["10Y美债"] and V["2Y美债"] else None
    )

    # ── 警报系统 ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">⚠ 风险警报系统</div>', unsafe_allow_html=True)

    def ac(title, desc, level):
        cls  = f"alert-{level}"
        icon = {"red":"🔴","green":"🟢","yellow":"🟡","blue":"🔵"}[level]
        return (f'<div class="alert-card {cls}">'
                f'<div class="alert-title">{icon} {title}</div>'
                f'<div class="alert-desc">{desc}</div></div>')

    alerts = []
    if spread_10_2 is not None:
        if spread_10_2 < -0.2:
            alerts.append(ac("收益率曲线深度倒挂",
                f"10Y-2Y = {spread_10_2:+.2f}%，历史强衰退信号","red"))
        elif spread_10_2 < 0:
            alerts.append(ac("收益率曲线轻微倒挂",
                f"10Y-2Y = {spread_10_2:+.2f}%，需持续关注","yellow"))
        else:
            alerts.append(ac("收益率曲线正常",
                f"10Y-2Y = {spread_10_2:+.2f}%，期限溢价为正","green"))

    if V["VIX"]:
        vx = V["VIX"]
        if vx > 35:
            alerts.append(ac("市场极度恐慌",
                f"VIX={vx:.1f}，系统性风险极高","red"))
        elif vx > 25:
            alerts.append(ac("市场恐慌升温",
                f"VIX={vx:.1f}，突破25警戒线","yellow"))
        else:
            alerts.append(ac("波动率平稳",
                f"VIX={vx:.1f}，低于25警戒线","green"))

    if V["美元指数"]:
        dx = V["美元指数"]
        if dx > 108:
            alerts.append(ac("美元极端强势",
                f"DXY={dx:.1f}，新兴市场资本外流风险极高","red"))
        elif dx > 105:
            alerts.append(ac("美元偏强",
                f"DXY={dx:.1f}，突破105，全球流动性收紧","yellow"))
        else:
            alerts.append(ac("美元指数平稳",
                f"DXY={dx:.1f}，未触发105警戒位","green"))

    if V["美高收益债利差"]:
        hy = V["美高收益债利差"]
        if hy > 600:
            alerts.append(ac("信用市场压力极大",
                f"HY利差={hy:.0f}bps，危机水平","red"))
        elif hy > 400:
            alerts.append(ac("信用利差走阔",
                f"HY利差={hy:.0f}bps，风险偏好下降","yellow"))
        else:
            alerts.append(ac("信用市场稳定",
                f"HY利差={hy:.0f}bps，风险偏好正常","green"))

    cols_a = st.columns(4)
    for i, a in enumerate(alerts):
        cols_a[i % 4].markdown(a, unsafe_allow_html=True)

    # ── KPI 卡片 ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📊 核心指标速览</div>', unsafe_allow_html=True)

    r1 = st.columns(5)
    r1[0].markdown(kpi("纳斯达克100", V["纳斯达克100"], CHG["纳斯达克100"]),        unsafe_allow_html=True)
    r1[1].markdown(kpi("标普500",     V["标普500"],     CHG["标普500"]),            unsafe_allow_html=True)
    r1[2].markdown(kpi("MSCI新兴市场", V["MSCI新兴市场"], CHG["MSCI新兴市场"]),      unsafe_allow_html=True)
    r1[3].markdown(kpi("沪深300",     V["沪深300"],     CHG["沪深300"]),            unsafe_allow_html=True)
    r1[4].markdown(kpi("VIX恐慌",     V["VIX"],         CHG["VIX"], fmt=""),        unsafe_allow_html=True)

    r2 = st.columns(5)
    r2[0].markdown(kpi("10Y美债",     V["10Y美债"],     None, "%", fmt=""),          unsafe_allow_html=True)
    r2[1].markdown(kpi("2Y美债",      V["2Y美债"],      None, "%", fmt=""),          unsafe_allow_html=True)
    r2[2].markdown(kpi("10Y-2Y利差",  spread_10_2,     None, "%", fmt="+"),          unsafe_allow_html=True)
    r2[3].markdown(kpi("美元指数",    V["美元指数"],    CHG["美元指数"], fmt=""),     unsafe_allow_html=True)
    r2[4].markdown(kpi("TIPS实际利率",V["TIPS_10Y实际利率"], None, "%", fmt=""),      unsafe_allow_html=True)

    r3 = st.columns(5)
    r3[0].markdown(kpi("黄金",        V["黄金"],   CHG["黄金"],    "$/oz"),          unsafe_allow_html=True)
    r3[1].markdown(kpi("原油WTI",     V["原油WTI"],CHG["原油WTI"],"$/桶", fmt=""),   unsafe_allow_html=True)
    r3[2].markdown(kpi("中国10Y国债", V["中国10Y国债"], None, "%", fmt=""),           unsafe_allow_html=True)
    r3[3].markdown(kpi("HY信用利差",  V["美高收益债利差"], None, "bps"),              unsafe_allow_html=True)
    r3[4].markdown(kpi("美联储净流动性",V["美联储净流动性"], None, "B$"),             unsafe_allow_html=True)

    r4 = st.columns(5)
    r4[0].markdown(kpi("上证综指",    V["上证综指"],    CHG["上证综指"]),              unsafe_allow_html=True)
    r4[1].markdown(kpi("创业板指",    V["创业板指"],    CHG["创业板指"]),              unsafe_allow_html=True)
    r4[2].markdown(kpi("中美利差10Y", V["中美利差(10Y)"], None, "%", fmt="+"),        unsafe_allow_html=True)
    r4[3].markdown(kpi("联邦基金利率",V["联邦基金利率"],  None, "%", fmt=""),          unsafe_allow_html=True)
    r4[4].markdown(kpi("日经225",     safe_val(df, "日经225"),  daily_chg(df, "日经225")), unsafe_allow_html=True)

    # ── 宏观情景诊断 ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🧠 宏观情景诊断</div>', unsafe_allow_html=True)
    mc1 = build_macro_regime(df, V, spread_10_2)
    _ca1, _ca2 = st.columns([1, 2])
    with _ca1:
        _rc = mc1["regime_color"]
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0d1321,{_rc}18);
                    border:1px solid {_rc}55;border-radius:12px;padding:20px;">
          <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1px;font-weight:600;">当前宏观情景</div>
          <div style="font-size:19px;font-weight:700;color:{_rc};margin:8px 0 6px;">{mc1['regime']}</div>
          <div style="font-size:11px;color:#94a3b8;line-height:1.7;">{mc1['regime_desc']}</div>
          <div style="margin-top:12px;padding-top:10px;border-top:1px solid #1e2a3a;">
            <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1px;">综合风险评分</div>
            <div style="font-size:22px;font-weight:700;color:{'#ef4444' if mc1['risk_score']>=11 else ('#f59e0b' if mc1['risk_score']>=7 else ('#3b82f6' if mc1['risk_score']>=4 else '#22c55e'))}">
              {mc1['risk_score']}/15
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with _ca2:
        _sig_items = list(mc1['signals'].items())
        _scols = st.columns(4)
        for _i, (_key, (_icon, _val, _desc)) in enumerate(_sig_items):
            _bc = "#ef4444" if _icon=="🔴" else ("#f59e0b" if _icon=="🟡" else "#22c55e")
            _scols[_i % 4].markdown(f"""
            <div style="background:#0d1321;border:1px solid {_bc}33;border-left:3px solid {_bc};
                        border-radius:8px;padding:10px 12px;margin:3px 0;min-height:80px;">
              <div style="font-size:9px;color:#475569;text-transform:uppercase;letter-spacing:0.8px;font-weight:600;">{_key}</div>
              <div style="font-size:13px;font-weight:700;color:#f8fafc;margin:4px 0 2px;">{_icon} {_val}</div>
              <div style="font-size:9px;color:#64748b;line-height:1.4;">{_desc[:45]}{'…' if len(_desc)>45 else ''}</div>
            </div>""", unsafe_allow_html=True)

    # ── 关注指标清单 ────────────────────────────────────────────────────
    if mc1['watch_list']:
        st.markdown('<div class="section-title">📌 本期重点关注指标</div>', unsafe_allow_html=True)
        _wl_cols = st.columns(4)
        for _i, (_ind, _reason) in enumerate(mc1['watch_list'][:8]):
            _wl_cols[_i % 4].markdown(
                f'<div class="alert-card alert-yellow">'
                f'<div class="alert-title">📍 {_ind}</div>'
                f'<div class="alert-desc">{_reason}</div></div>',
                unsafe_allow_html=True
            )

    st.divider()

    # ── 主图：股指 + VIX ────────────────────────────────────────────────
    st.markdown('<div class="section-title">📈 核心市场走势</div>', unsafe_allow_html=True)
    c_main, c_side = st.columns([3, 2])

    with c_main:
        fig_main = make_subplots(specs=[[{"secondary_y": True}]])
        for nm, col in [("标普500","#3b82f6"),("纳斯达克100","#22c55e")]:
            if nm in df.columns:
                s = df[nm].dropna()
                fig_main.add_trace(go.Scatter(
                    x=s.index, y=s.values, name=nm,
                    line=dict(color=col, width=1.8),
                ), secondary_y=False)
        if "VIX" in df.columns:
            sv = df["VIX"].dropna()
            fig_main.add_trace(go.Scatter(
                x=sv.index, y=sv.values, name="VIX",
                line=dict(color="#f59e0b", width=1.2, dash="dot"), opacity=0.9,
            ), secondary_y=True)
            fig_main.add_hline(y=25, line_dash="dash", line_color="#ef4444",
                               line_width=0.8,
                               annotation_text="VIX 25",
                               annotation_font=dict(color="#ef4444", size=9),
                               secondary_y=True)
            fig_main.add_hline(y=35, line_dash="dot", line_color="#dc2626",
                               line_width=0.8,
                               annotation_text="VIX 35危机",
                               annotation_font=dict(color="#dc2626", size=9),
                               secondary_y=True)
        lo = mk_layout("标普500 / 纳指  vs  VIX 恐慌指数", h=380)
        lo["yaxis2"] = secondary_y_axis()
        lo["yaxis2"]["title"] = "VIX"
        fig_main.update_layout(**lo)
        fig_main.update_yaxes(title_text="指数点位", secondary_y=False, gridcolor=GRID)
        st.plotly_chart(fig_main, use_container_width=True)

    with c_side:
        # 利差柱图
        if "10Y美债" in df.columns and "2Y美债" in df.columns:
            sp = (df["10Y美债"] - df["2Y美债"]).dropna()
            colors_sp = ["#ef4444" if x < 0 else "#22c55e" for x in sp.values]
            fig_sp = go.Figure()
            fig_sp.add_trace(go.Bar(
                x=sp.index, y=sp.values,
                marker_color=colors_sp, opacity=0.85, name="利差",
            ))
            fig_sp.add_hline(y=0, line_color="#d1d5db", line_width=0.8)
            fig_sp.update_layout(**mk_layout("10Y-2Y 利差（红=倒挂）",
                                             h=185, l=50, r=20, t=36, b=30,
                                             show_legend=False))
            st.plotly_chart(fig_sp, use_container_width=True)

        if "美高收益债利差" in df.columns:
            hy_s = df["美高收益债利差"].dropna()
            fig_hy = go.Figure()
            fig_hy.add_trace(go.Scatter(
                x=hy_s.index, y=hy_s.values, name="HY利差",
                line=dict(color="#a855f7", width=1.5),
                fill="tozeroy", fillcolor="rgba(168,85,247,0.08)",
            ))
            fig_hy.add_hline(y=400, line_dash="dash", line_color="#ef4444",
                             line_width=0.8,
                             annotation_text="400bps预警",
                             annotation_font=dict(color="#ef4444", size=9))
            fig_hy.update_layout(**mk_layout("美国高收益债信用利差 (bps)",
                                             h=185, l=50, r=20, t=36, b=30,
                                             show_legend=False))
            st.plotly_chart(fig_hy, use_container_width=True)

    # ── 美联储净流动性 ────────────────────────────────────────────────────
    if "美联储净流动性" in df.columns:
        st.markdown('<div class="section-title">🏦 美联储流动性</div>', unsafe_allow_html=True)
        fl_s = df["美联储净流动性"].dropna()
        cl, cr = st.columns([3, 1])
        with cl:
            fig_fl = make_subplots(specs=[[{"secondary_y": True}]])
            fig_fl.add_trace(go.Scatter(
                x=fl_s.index, y=fl_s.values, name="净流动性 (B$)",
                line=dict(color="#06b6d4", width=2),
                fill="tozeroy", fillcolor="rgba(6,182,212,0.07)",
            ), secondary_y=False)
            if "标普500" in df.columns:
                spx = df["标普500"].dropna()
                fig_fl.add_trace(go.Scatter(
                    x=spx.index, y=spx.values, name="标普500",
                    line=dict(color="#3b82f6", width=1.2, dash="dot"), opacity=0.65,
                ), secondary_y=True)
            lo_fl = mk_layout("美联储净流动性 = WALCL − TGA − RRP  vs  标普500", h=320)
            lo_fl["yaxis2"] = secondary_y_axis()
            lo_fl["yaxis2"]["title"] = "标普500"
            fig_fl.update_layout(**lo_fl)
            fig_fl.update_yaxes(title_text="净流动性 (十亿美元)", secondary_y=False, gridcolor=GRID)
            st.plotly_chart(fig_fl, use_container_width=True)
        with cr:
            if not fl_s.empty:
                fl_z   = float(zscore(fl_s).iloc[-1]) if len(fl_s) > 1 else 0
                fl_val = float(fl_s.iloc[-1])
                color_z = "#22c55e" if fl_z > 0 else "#ef4444"
                label_z = "💧 宽松偏高" if fl_z > 0.5 else ("🔴 收紧偏低" if fl_z < -0.5 else "➡️ 中性区间")
                st.markdown(f"""
                <div class="kpi-card" style="margin-top:48px;padding:20px;">
                  <div class="kpi-label">净流动性 Z-Score</div>
                  <div class="kpi-value" style="color:{color_z};">{fl_z:+.2f}σ</div>
                  <div class="kpi-label" style="margin-top:10px;">当前规模</div>
                  <div style="font-size:17px;font-weight:600;color:#f8fafc;">{fl_val:,.0f} B$</div>
                  <div style="font-size:11px;color:#475569;margin-top:8px;">{label_z}</div>
                </div>
                """, unsafe_allow_html=True)
    return V, CHG, spread_10_2
