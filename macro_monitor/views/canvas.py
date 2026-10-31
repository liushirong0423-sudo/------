"TAB 3 — 万能画布：任意指标叠加与归一化"
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from ..analytics import minmax, zscore
from ..charts import mk_layout
from ..config import COLORS



def render(df, period_label, norm_mode, canvas_sel):
    st.markdown('<div class="section-title">🔬 多指标归一化叠加画布</div>',
                unsafe_allow_html=True)
    st.caption("消除量纲差异，在同一坐标系直观对比任意指标的历史波动特征与当前背离幅度")

    avail = [c for c in canvas_sel if c in df.columns and not df[c].dropna().empty]
    if not avail:
        st.info("请在左侧侧边栏选择至少一个有效指标。")
    else:
        fig_cv = go.Figure()
        y_lab  = "Z-Score (σ)"

        for i, col in enumerate(avail):
            s = df[col].dropna()
            if s.empty:
                continue
            if norm_mode == "Z-Score":
                y    = zscore(s).values
                y_lab = "Z-Score (σ)"
            elif norm_mode == "Min-Max [0,1]":
                y    = minmax(s).values
                y_lab = "归一化 [0,1]"
            else:
                y    = s.values
                y_lab = "原始值"

            fig_cv.add_trace(go.Scatter(
                x=s.index, y=y, name=col,
                line=dict(color=COLORS[i % len(COLORS)], width=1.8),
                hovertemplate=(
                    f"<b>{col}</b><br>"
                    "%{x|%Y-%m-%d}: %{y:.3f}<extra></extra>"
                ),
            ))

        if norm_mode == "Z-Score":
            for lv, lc, dash in [
                (2,"#ef4444","dot"),(1,"#f59e0b","dash"),
                (-1,"#f59e0b","dash"),(-2,"#ef4444","dot"),
            ]:
                fig_cv.add_hline(
                    y=lv, line_dash=dash, line_color=lc, line_width=0.8,
                    annotation_text=f"{'+' if lv>0 else ''}{lv}σ",
                    annotation_font=dict(color=lc, size=10),
                    annotation_position="right",
                )
            fig_cv.add_hline(y=0, line_color="#374151", line_width=1)

        lo_cv = mk_layout(
            f"多指标归一化叠加 ({norm_mode})  |  {period_label}", h=520)
        lo_cv["yaxis"]["title"] = y_lab
        fig_cv.update_layout(**lo_cv)
        st.plotly_chart(fig_cv, use_container_width=True)

        # 统计摘要
        st.markdown('<div class="section-title">📋 指标状态摘要</div>',
                    unsafe_allow_html=True)
        rows = []
        for col in avail:
            s = df[col].dropna()
            if s.empty:
                continue
            cur  = s.iloc[-1]
            zs   = float(zscore(s).iloc[-1]) if len(s) > 1 else 0.0
            ch1  = (s.iloc[-1]/s.iloc[-2]-1)*100 if len(s) > 1 else 0.0
            pctile = (s < cur).mean() * 100
            status = ("🔴 极端偏高" if zs > 2 else
                      "🔵 极端偏低" if zs < -2 else
                      "🟠 偏高" if zs > 1 else
                      "🟡 偏低" if zs < -1 else "🟢 正常")
            rows.append({
                "指标": col, "最新值": round(cur, 4),
                "Z-Score": f"{zs:+.2f}σ", "日涨跌": f"{ch1:+.2f}%",
                "历史分位": f"{pctile:.1f}%",
                "均值": round(s.mean(), 4), "标准差": round(s.std(), 4),
                "最高": round(s.max(), 4), "最低": round(s.min(), 4),
                "状态": status,
            })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
