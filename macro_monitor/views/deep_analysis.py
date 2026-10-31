"TAB 5 — 深度分析：相关性 / 中美宏观 / 波动率与 Z-Score"
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..charts import mk_layout
from ..config import BG, BG_CARD, BORDER, TEXT



def render(df, period_label):
    sub1, sub2, sub3 = st.tabs(["🔗 相关性矩阵","📉 宏观经济","📊 滚动统计"])

    # ── 相关性矩阵 ──────────────────────────────────────────────────────
    with sub1:
        st.markdown('<div class="section-title">🔗 宏观指标相关性热力图</div>',
                    unsafe_allow_html=True)
        # ── 先过滤出高频、有足够数据的序列 ──
        df_ret_all = df.pct_change().dropna(how="all")
        ret_density = df_ret_all.notna().mean()
        hf_all = ret_density[ret_density > 0.10].index.tolist()
        hf_all = [c for c in hf_all if not c.endswith("_PE")
                  and df_ret_all[c].dropna().shape[0] > 60]

        # ── 精选核心指标（默认显示，避免杂乱）──
        CORE_HEAT = [
            "纳斯达克100","标普500","道琼斯","MSCI新兴市场","德国DAX",
            "沪深300","恒生指数","上证综指",
            "10Y美债","2Y美债","VIX","SKEW指数","VVIX",
            "美元指数","欧元/美元","美元/人民币",
            "黄金","原油WTI","铜","铜金比率",
            "美高收益债利差","TIPS_10Y实际利率",
            "美联储储总资产",
        ]
        default_sel = [c for c in CORE_HEAT if c in hf_all]
        extra_opts  = [c for c in hf_all if c not in default_sel]

        with st.expander("⚙️ 自定义指标选择", expanded=False):
            sel_cols = st.multiselect(
                "从所有高频指标中选择（建议 ≤30 个）",
                options=hf_all,
                default=default_sel,
                key="corr_sel",
            )
        if not sel_cols:
            sel_cols = default_sel

        heat_cols = [c for c in sel_cols if c in df_ret_all.columns]
        if len(heat_cols) < 3:
            st.warning("有效序列不足，请调整选择后重试。")
        else:
            df_ret  = df_ret_all[heat_cols].dropna(axis=1, thresh=int(len(df_ret_all) * 0.4))
            heat_cols = list(df_ret.columns)
            corr    = df_ret.corr(method="pearson")
            n       = len(heat_cols)
            # 动态字号：指标越多字越小，超过30个隐藏数字
            txt_size  = max(6, 11 - n // 5)
            show_text = n <= 28
            labels    = [c[:8] if len(c) > 8 else c for c in corr.columns]
            chart_h   = max(500, min(900, 380 + n * 14))

            fig_hm = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=labels, y=labels,
                colorscale=[
                    [0.0, "#0c2d6b"],[0.35, "#1d4ed8"],
                    [0.5,  "#0d1321"],
                    [0.65, "#9f1239"],[1.0, "#dc2626"],
                ],
                zmin=-1, zmax=1,
                text=np.round(corr.values, 2) if show_text else None,
                texttemplate="%{text}" if show_text else None,
                textfont=dict(size=txt_size, color="#d1d5db") if show_text else None,
                colorbar=dict(
                    title=dict(text="ρ", font=dict(color="#94a3b8", size=12)),
                    tickvals=[-1, -0.5, 0, 0.5, 1],
                    tickfont=dict(color="#94a3b8", size=10),
                    bgcolor=BG_CARD,
                    bordercolor=BORDER,
                    borderwidth=1,
                    thickness=14,
                    len=0.8,
                ),
            ))
            fig_hm.update_layout(dict(
                paper_bgcolor=BG_CARD, plot_bgcolor=BG,
                font=dict(color=TEXT, family="Inter", size=10),
                height=chart_h,
                margin=dict(l=90, r=60, t=44, b=90),
                title=dict(
                    text=f"宏观指标日收益率相关性  |  {period_label}  |  共 {n} 个指标",
                    font=dict(color="#94a3b8", size=13), x=0, xanchor="left",
                ),
                xaxis=dict(tickangle=-45, tickfont=dict(size=max(8, 11 - n // 6))),
                yaxis=dict(tickfont=dict(size=max(8, 11 - n // 6))),
            ))
            st.plotly_chart(fig_hm, use_container_width=True)

            if "纳斯达克100" in corr.columns:
                ndx_c = corr["纳斯达克100"].drop("纳斯达克100").sort_values(ascending=False)
                cl, cr = st.columns([1, 2])
                with cl:
                    st.markdown("**与纳指相关性排名**")
                    df_rank = pd.DataFrame({
                        "指标": ndx_c.index,
                        "ρ": ndx_c.values.round(3),
                        "关系": [
                            "📈 顺周期" if v > 0.3
                            else ("📉 逆周期" if v < -0.3
                                  else "➡️ 弱相关")
                            for v in ndx_c.values
                        ],
                    })
                    st.dataframe(df_rank, use_container_width=True, hide_index=True)
                with cr:
                    clrs = ["#ef4444" if v > 0 else "#3b82f6" for v in ndx_c.values]
                    fig_bar = go.Figure(go.Bar(
                        x=ndx_c.values, y=ndx_c.index,
                        orientation="h", marker_color=clrs,
                        text=[f"{v:.3f}" for v in ndx_c.values],
                        textposition="outside",
                        textfont=dict(size=10, color="#94a3b8"),
                    ))
                    lo_b = mk_layout("与纳指相关系数 ρ", h=420, l=130, r=80, show_legend=False)
                    lo_b["xaxis"]["range"] = [-1.15, 1.15]
                    lo_b["xaxis"]["zerolinecolor"] = "#374151"
                    fig_bar.update_layout(**lo_b)
                    st.plotly_chart(fig_bar, use_container_width=True)

    # ── 宏观经济指标 ──────────────────────────────────────────────────
    with sub2:
        st.markdown('<div class="section-title">🇺🇸 美国宏观经济指标（FRED）</div>',
                    unsafe_allow_html=True)
        macro_us = [
            ("美国CPI同比",    "#ef4444",  "通胀率 (%)",    2,   "2%通胀目标"),
            ("核心PCE同比",    "#f97316",  "核心PCE (%)",   2,   "2%目标"),
            ("美国失业率",     "#3b82f6",  "失业率 (%)",    4,   "4%参考"),
            ("密歇根消费信心", "#22c55e",  "消费信心指数",  None, None),
            ("M2货币供应",     "#a855f7",  "M2 (十亿美元)", None, None),
            ("美投资级债利差", "#06b6d4",  "IG利差 (bps)",  None, None),
        ]
        avail_m = [(k, c, l, thr, tl) for k, c, l, thr, tl in macro_us if k in df.columns]
        if avail_m:
            for row_start in range(0, len(avail_m), 3):
                row_items = avail_m[row_start:row_start+3]
                cols_m = st.columns(len(row_items))
                for col_ui, (nm, color, ylabel, thr, tl) in zip(cols_m, row_items):
                    s = df[nm].dropna()
                    if s.empty:
                        continue
                    fig_m = go.Figure()
                    fig_m.add_trace(go.Scatter(
                        x=s.index, y=s.values, name=nm,
                        line=dict(color=color, width=2),
                        fill="tozeroy",
                        fillcolor=f"rgba(99,99,99,0.07)",
                    ))
                    if thr is not None:
                        fig_m.add_hline(
                            y=thr, line_dash="dash", line_color="#374151",
                            line_width=0.8,
                            annotation_text=tl,
                            annotation_font=dict(color="#374151", size=9),
                        )
                    cur = float(s.iloc[-1])
                    fig_m.update_layout(**mk_layout(
                        f"{nm}  当前: {cur:.2f}", h=240,
                        l=48, r=15, t=42, b=30, show_legend=False))
                    fig_m.update_yaxes(title_text=ylabel)
                    col_ui.plotly_chart(fig_m, use_container_width=True)
        else:
            st.info("美国宏观数据加载中（FRED API），请稍后刷新。")

        # 中国宏观
        cn_m_cols = [c for c in [
            "中国CPI同比","中国PPI同比","中国PMI制造业","财新PMI制造业","中国M2同比"
        ] if c in df.columns]
        if cn_m_cols:
            st.markdown('<div class="section-title">🇨🇳 中国宏观经济指标（akshare）</div>',
                        unsafe_allow_html=True)
            cols_cn = st.columns(len(cn_m_cols))
            for col_ui, nm in zip(cols_cn, cn_m_cols):
                s = df[nm].dropna()
                color = "#ef4444" if "CPI" in nm else "#3b82f6"
                fig_cn = go.Figure()
                fig_cn.add_trace(go.Scatter(
                    x=s.index, y=s.values, name=nm,
                    line=dict(color=color, width=2),
                    fill="tozeroy", fillcolor="rgba(59,130,246,0.07)",
                ))
                if "PMI" in nm:
                    fig_cn.add_hline(y=50, line_dash="dash", line_color="#374151",
                                     line_width=0.8,
                                     annotation_text="荣枯线 50",
                                     annotation_font=dict(color="#374151", size=9))
                cur = float(s.iloc[-1])
                fig_cn.update_layout(**mk_layout(
                    f"{nm}  当前: {cur:.2f}", h=260,
                    l=48, r=15, t=42, b=30, show_legend=False))
                col_ui.plotly_chart(fig_cn, use_container_width=True)

    # ── 滚动统计 ──────────────────────────────────────────────────────
    with sub3:
        st.markdown('<div class="section-title">📊 滚动统计分析</div>',
                    unsafe_allow_html=True)
        roll_opts = [c for c in df.columns if df[c].dropna().shape[0] > 100]
        if not roll_opts:
            st.info("数据不足，无法进行滚动统计。")
        else:
            rc1, rc2, rc3 = st.columns([2, 1, 1])
            with rc1:
                roll_col = st.selectbox("分析标的", roll_opts, index=0)
            with rc2:
                roll_win = st.slider("滚动窗口（交易日）", 10, 252, 60, 5)
            with rc3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

            s   = df[roll_col].dropna()
            ret = s.pct_change().dropna()
            r_mean  = s.rolling(roll_win).mean().dropna()
            r_std   = ret.rolling(roll_win).std().dropna() * np.sqrt(252) * 100
            r_zscore= ((s - s.rolling(roll_win).mean()) /
                       s.rolling(roll_win).std()).dropna()

            c1, c2 = st.columns(2)
            with c1:
                fig_r1 = go.Figure()
                fig_r1.add_trace(go.Scatter(
                    x=s.index, y=s.values, name="价格",
                    line=dict(color="#3b82f6", width=1.5), opacity=0.8,
                ))
                fig_r1.add_trace(go.Scatter(
                    x=r_mean.index, y=r_mean.values,
                    name=f"{roll_win}日均线",
                    line=dict(color="#f59e0b", width=2, dash="dash"),
                ))
                fig_r1.update_layout(**mk_layout(
                    f"{roll_col} · 价格 & {roll_win}日均线", h=320))
                st.plotly_chart(fig_r1, use_container_width=True)

            with c2:
                fig_r2 = go.Figure()
                fig_r2.add_trace(go.Scatter(
                    x=r_std.index, y=r_std.values,
                    name=f"{roll_win}日年化波动率",
                    line=dict(color="#a855f7", width=1.8),
                    fill="tozeroy", fillcolor="rgba(168,85,247,0.07)",
                ))
                fig_r2.update_layout(**mk_layout(
                    f"{roll_col} · {roll_win}日滚动年化波动率 (%)", h=320))
                st.plotly_chart(fig_r2, use_container_width=True)

            # 滚动 Z-Score 柱图（背离度）
            fig_r3 = go.Figure()
            bar_clr = ["#ef4444" if abs(v) > 2 else
                       ("#f59e0b" if abs(v) > 1 else "#22c55e")
                       for v in r_zscore.values]
            fig_r3.add_trace(go.Bar(
                x=r_zscore.index, y=r_zscore.values,
                marker_color=bar_clr, name="滚动Z-Score",
                hovertemplate="%{x|%Y-%m-%d}: %{y:.3f}<extra></extra>",
            ))
            for lv, lc in [(2,"#ef4444"),(1,"#f59e0b"),(-1,"#f59e0b"),(-2,"#ef4444")]:
                fig_r3.add_hline(y=lv, line_dash="dash",
                                 line_color=lc, line_width=0.8)
            fig_r3.update_layout(**mk_layout(
                f"{roll_col} · {roll_win}日滚动 Z-Score（绿=正常 / 橙=1σ / 红=2σ）", h=280))
            st.plotly_chart(fig_r3, use_container_width=True)
