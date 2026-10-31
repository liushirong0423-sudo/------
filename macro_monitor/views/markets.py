"TAB 2 — 全球市场：股指 / 大宗 / 加密 / 黄金 vs 实际利率 / 外汇"
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..analytics import hex_to_rgba, zscore
from ..charts import mk_layout, secondary_y_axis
from ..config import COLORS, GRID, YFINANCE_EQUITY, YFINANCE_FX



def render(df, period_label):
    # ── 全球股指（基准=100）────────────────────────────────────────────
    st.markdown('<div class="section-title">🌍 全球股指走势（基准化 = 100）</div>',
                unsafe_allow_html=True)
    eq_cols = [c for c in list(YFINANCE_EQUITY.keys()) +
               ["沪深300","恒生指数","上证综指","创业板指","中证500"]
               if c in df.columns]
    if eq_cols:
        fig_eq = go.Figure()
        for i, nm in enumerate(eq_cols):
            s = df[nm].dropna()
            if s.empty:
                continue
            fig_eq.add_trace(go.Scatter(
                x=s.index, y=(s / s.iloc[0] * 100).values, name=nm,
                line=dict(color=COLORS[i % len(COLORS)], width=1.8),
            ))
        fig_eq.add_hline(y=100, line_dash="dot", line_color="#374151", line_width=1)
        fig_eq.update_layout(**mk_layout(
            f"全球主要股指（起点=100，{period_label}）", h=420))
        st.plotly_chart(fig_eq, use_container_width=True)

    # ── 大宗商品 ──────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🛢 大宗商品</div>', unsafe_allow_html=True)
    cm1, cm2, cm3 = st.columns(3)
    for col_ui, (nm, color) in zip(
        [cm1, cm2, cm3],
        [("黄金","#f59e0b"),("原油WTI","#6b7280"),("铜","#fb923c")],
    ):
        if nm not in df.columns:
            continue
        s = df[nm].dropna()
        fig_c = go.Figure()
        fig_c.add_trace(go.Scatter(
            x=s.index, y=s.values, name=nm,
            line=dict(color=color, width=2),
            fill="tozeroy", fillcolor=hex_to_rgba(color, 0.08),
        ))
        fig_c.update_layout(**mk_layout(nm, h=260, l=50, r=20, t=40, b=30,
                                        show_legend=False))
        col_ui.plotly_chart(fig_c, use_container_width=True)

    # ── 黄金 vs 实际利率 ──────────────────────────────────────────────
    if "黄金" in df.columns and "TIPS_10Y实际利率" in df.columns:
        st.markdown('<div class="section-title">⚖ 黄金 vs TIPS 实际利率（负相关验证）</div>',
                    unsafe_allow_html=True)
        fig_gv = make_subplots(specs=[[{"secondary_y": True}]])
        s_g = df["黄金"].dropna()
        s_t = df["TIPS_10Y实际利率"].dropna()
        fig_gv.add_trace(go.Scatter(
            x=s_g.index, y=s_g.values, name="黄金 ($/oz)",
            line=dict(color="#f59e0b", width=1.8),
        ), secondary_y=False)
        fig_gv.add_trace(go.Scatter(
            x=s_t.index, y=s_t.values, name="TIPS 10Y实际利率 (%)",
            line=dict(color="#ef4444", width=1.4, dash="dash"),
        ), secondary_y=True)
        lo_gv = mk_layout("黄金价格 vs 10Y TIPS 实际利率（负相关）", h=340)
        lo_gv["yaxis2"] = secondary_y_axis()
        lo_gv["yaxis2"]["title"] = "实际利率 (%)"
        fig_gv.update_layout(**lo_gv)
        fig_gv.update_yaxes(title_text="黄金 ($/oz)", secondary_y=False, gridcolor=GRID)
        st.plotly_chart(fig_gv, use_container_width=True)

    # ── 外汇 ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">💱 外汇市场（Z-Score 对比）</div>',
                unsafe_allow_html=True)
    fx_cols = [c for c in YFINANCE_FX.keys() if c in df.columns]
    if fx_cols:
        fig_fx = go.Figure()
        for i, nm in enumerate(fx_cols):
            s = df[nm].dropna()
            if s.empty:
                continue
            fig_fx.add_trace(go.Scatter(
                x=s.index, y=zscore(s).values, name=nm,
                line=dict(color=COLORS[i % len(COLORS)], width=1.6),
            ))
        fig_fx.add_hline(y=0, line_color="#374151", line_width=1)
        fig_fx.update_layout(**mk_layout("外汇市场 Z-Score 标准化对比", h=320))
        st.plotly_chart(fig_fx, use_container_width=True)

    # ── 比特币 ───────────────────────────────────────────────────────
    if "比特币" in df.columns:
        st.markdown('<div class="section-title">₿ 加密货币</div>', unsafe_allow_html=True)
        btc = df["比特币"].dropna()
        fig_btc = go.Figure()
        fig_btc.add_trace(go.Scatter(
            x=btc.index, y=btc.values, name="比特币",
            line=dict(color="#f59e0b", width=1.8),
            fill="tozeroy", fillcolor="rgba(245,158,11,0.06)",
        ))
        fig_btc.update_layout(**mk_layout("比特币价格 (USD)", h=280))
        st.plotly_chart(fig_btc, use_container_width=True)
