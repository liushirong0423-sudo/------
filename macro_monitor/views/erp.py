"TAB 4 — 股债利差 ERP：沪深300 / 美股 ERP / TIPS / 收益率曲线"
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..analytics import safe_val, zscore
from ..charts import mk_layout, secondary_y_axis
from ..config import COLORS, GRID



def render(df):
    st.markdown('<div class="section-title">💰 股权风险溢价 (ERP) — 股票相对债券的吸引力</div>',
                unsafe_allow_html=True)
    st.caption("ERP = 盈利收益率 (100/PE) − 10Y国债收益率（%）。ERP↑ → 股票性价比提升")

    etabs = st.tabs(["📈 美股/纳指 ERP", "📊 实际利率体系", "📉 完整收益率曲线", "🌏 中美利差"])

    # ── 美股 & 纳指 ERP ──────────────────────────────────────────────
    with etabs[0]:
        tnx_cur = safe_val(df, "10Y美债")
        sp_pe, ndx_pe = None, None
        try:
            import yfinance as yf
            for _tk in ["SPY", "IVV", "VOO"]:
                try:
                    _pe = yf.Ticker(_tk).info.get("trailingPE") or yf.Ticker(_tk).info.get("forwardPE")
                    if _pe and 5 < float(_pe) < 200:
                        sp_pe = float(_pe); break
                except Exception:
                    continue
            for _tk in ["QQQ", "QQQM"]:
                try:
                    _pe = yf.Ticker(_tk).info.get("trailingPE") or yf.Ticker(_tk).info.get("forwardPE")
                    if _pe and 5 < float(_pe) < 300:
                        ndx_pe = float(_pe); break
                except Exception:
                    continue
        except Exception:
            pass

        if tnx_cur and (sp_pe or ndx_pe):
            # ── KPI 行 ──
            _kpi_cols = st.columns(7)
            _kpi_cols[0].metric("10Y美债", f"{tnx_cur:.2f}%")
            if sp_pe:
                sp_ey  = 100 / sp_pe
                sp_erp = sp_ey - tnx_cur
                _ec    = "normal" if sp_erp > 0 else "inverse"
                _kpi_cols[1].metric("标普500 PE",  f"{sp_pe:.1f}×")
                _kpi_cols[2].metric("标普500 盈利收益率", f"{sp_ey:.2f}%")
                _kpi_cols[3].metric("标普500 ERP", f"{sp_erp:+.2f}%",
                                    delta=f"{'高于' if sp_erp>0 else '低于'}无风险利率",
                                    delta_color=_ec)
            if ndx_pe:
                ndx_ey  = 100 / ndx_pe
                ndx_erp = ndx_ey - tnx_cur
                _ec2    = "normal" if ndx_erp > 0 else "inverse"
                _kpi_cols[4].metric("纳指100 PE",  f"{ndx_pe:.1f}×")
                _kpi_cols[5].metric("纳指100 盈利收益率", f"{ndx_ey:.2f}%")
                _kpi_cols[6].metric("纳指100 ERP", f"{ndx_erp:+.2f}%",
                                    delta=f"{'高于' if ndx_erp>0 else '低于'}无风险利率",
                                    delta_color=_ec2)

            # ── 对比柱图 ──
            _erp_items = {}
            if sp_pe:  _erp_items["标普500 ERP"] = (100/sp_pe - tnx_cur, "#3b82f6")
            if ndx_pe: _erp_items["纳指100 ERP"] = (100/ndx_pe - tnx_cur, "#a855f7")
            if _erp_items:
                _names = list(_erp_items.keys())
                _vals  = [_erp_items[k][0] for k in _names]
                _clrs  = ["#22c55e" if v > 0 else "#ef4444" for v in _vals]
                fig_erp = go.Figure(go.Bar(
                    x=_names, y=_vals,
                    marker_color=_clrs,
                    text=[f"{v:+.2f}%" for v in _vals],
                    textposition="outside",
                    textfont=dict(size=15, color="#f8fafc"),
                    width=0.35,
                ))
                fig_erp.add_hline(y=0, line_color="#475569", line_width=1,
                                  annotation_text="ERP=0 (股债无差异)",
                                  annotation_font=dict(color="#6b7280", size=10))
                lo_erp = mk_layout("股票风险溢价 ERP = 盈利收益率 (100/PE) − 10Y美债收益率",
                                   h=340, show_legend=False)
                lo_erp["yaxis"]["title"] = "ERP (%)"
                fig_erp.update_layout(**lo_erp)
                st.plotly_chart(fig_erp, use_container_width=True)

            st.caption(
                "• **ERP > 0**：盈利收益率 > 无风险利率 → 股票相对债券有吸引力\n"
                "• **ERP < 0**：持有国债回报更高 → 股票估值偏贵，注意回调风险\n"
                "• 纳指100 PE 通常远高于标普500，ERP 更低，对利率上行更为敏感"
            )
        else:
            st.info("PE 或10Y美债数据暂不可用，请稍后刷新。")

    # 实际利率体系
    with etabs[1]:
        tips_cfg = {
            "TIPS_10Y实际利率": ("#3b82f6", "10Y TIPS实际利率"),
            "10Y盈亏平衡通胀":  ("#f59e0b", "10Y盈亏平衡通胀预期"),
            "5Y5Y远期通胀":     ("#22c55e", "5Y5Y远期通胀预期"),
        }
        avail_t = {k: v for k, v in tips_cfg.items() if k in df.columns}
        if avail_t:
            fig_t = go.Figure()
            for nm, (color, label) in avail_t.items():
                s = df[nm].dropna()
                fig_t.add_trace(go.Scatter(
                    x=s.index, y=s.values, name=label,
                    line=dict(color=color, width=1.8),
                ))
            fig_t.add_hline(y=0, line_color="#475569", line_width=1,
                            annotation_text="零线",
                            annotation_font=dict(color="#475569", size=9))
            fig_t.add_hline(y=2, line_dash="dash", line_color="#374151", line_width=0.8,
                            annotation_text="2%通胀目标",
                            annotation_font=dict(color="#374151", size=9))
            fig_t.update_layout(**mk_layout("TIPS 实际利率 & 通胀预期体系（FRED）", h=400))
            st.plotly_chart(fig_t, use_container_width=True)
            st.caption(
                "• **TIPS 10Y实际利率↑** → 持有现金/债券更具吸引力，黄金与成长股承压\n"
                "• **盈亏平衡通胀↑** → 市场预期通胀上升，黄金/大宗/TIPS受益\n"
                "• **5Y5Y远期通胀** → 央行长期通胀锚是否松动的核心指标"
            )
        else:
            st.info("TIPS 实际利率数据加载中，请稍后刷新（FRED API）。")

    # 完整收益率曲线
    with etabs[2]:
        rate_nm = {"2Y":"2Y美债","5Y":"5Y美债","10Y":"10Y美债","30Y":"30Y美债"}
        avail_r = {k: v for k, v in rate_nm.items() if v in df.columns}
        if len(avail_r) >= 2:
            cl, cr = st.columns([3, 2])
            with cl:
                fig_yc = go.Figure()
                for i, (t, nm) in enumerate(avail_r.items()):
                    s = df[nm].dropna()
                    fig_yc.add_trace(go.Scatter(
                        x=s.index, y=s.values, name=t,
                        line=dict(color=COLORS[i], width=1.8),
                    ))
                fig_yc.update_layout(**mk_layout("美国国债收益率历史走势", h=380))
                st.plotly_chart(fig_yc, use_container_width=True)
            with cr:
                tenor_v = {"2Y": 2,"5Y": 5,"10Y": 10,"30Y": 30}
                xs = [tenor_v[t] for t in avail_r if safe_val(df, avail_r[t])]
                ys = [safe_val(df, avail_r[t]) for t in avail_r if safe_val(df, avail_r[t])]
                if xs and ys:
                    fig_snap = go.Figure()
                    fig_snap.add_trace(go.Scatter(
                        x=xs, y=ys, mode="lines+markers",
                        line=dict(color="#3b82f6", width=2.2),
                        marker=dict(size=9, color="#3b82f6",
                                    line=dict(color="#f8fafc", width=1.5)),
                        name="当前收益率",
                    ))
                    lo_s = mk_layout("当前收益率曲线形状", h=380, l=55, r=20, show_legend=False)
                    lo_s["xaxis"]["tickvals"] = xs
                    lo_s["xaxis"]["ticktext"] = [f"{x}Y" for x in xs]
                    lo_s["xaxis"]["title"]    = "期限"
                    lo_s["yaxis"]["title"]    = "收益率 (%)"
                    fig_snap.update_layout(**lo_s)
                    st.plotly_chart(fig_snap, use_container_width=True)

    # ── 中美利差 ──────────────────────────────────────────────────────
    with etabs[3]:
        st.markdown('<div class="section-title">🌏 中美利差 & 全球国债比较</div>',
                    unsafe_allow_html=True)
        st.caption("中美利差 = 美国10Y − 中国10Y。利差为负表示资金倾向流向美国，人民币汇率承压；利差为正则反之。")

        if "中美利差(10Y)" in df.columns:
            cn_us_sp = df["中美利差(10Y)"].dropna()
            _cl, _cr = st.columns([3, 1])
            with _cl:
                fig_cnus = make_subplots(specs=[[{"secondary_y": True}]])
                for _nm, _col in [("10Y美债","#3b82f6"),("中国10Y国债","#ef4444")]:
                    if _nm in df.columns:
                        _s = df[_nm].dropna()
                        fig_cnus.add_trace(go.Scatter(
                            x=_s.index, y=_s.values, name=_nm,
                            line=dict(color=_col, width=1.8),
                        ), secondary_y=False)
                fig_cnus.add_trace(go.Scatter(
                    x=cn_us_sp.index, y=cn_us_sp.values,
                    name="中美利差 (US−CN, %)",
                    line=dict(color="#a855f7", width=1.5, dash="dash"),
                    fill="tozeroy", fillcolor="rgba(168,85,247,0.07)",
                ), secondary_y=True)
                fig_cnus.add_hline(y=0, secondary_y=True,
                                   line_color="#374151", line_width=1,
                                   annotation_text="利差=0",
                                   annotation_font=dict(color="#475569", size=9))
                lo_cn = mk_layout("中美10年期国债收益率 & 利差（美国 − 中国）", h=400)
                lo_cn["yaxis2"] = secondary_y_axis()
                lo_cn["yaxis2"]["title"] = "利差 (%)"
                fig_cnus.update_layout(**lo_cn)
                fig_cnus.update_yaxes(title_text="收益率 (%)", secondary_y=False, gridcolor=GRID)
                st.plotly_chart(fig_cnus, use_container_width=True)
            with _cr:
                _cur_sp = float(cn_us_sp.iloc[-1]) if not cn_us_sp.empty else None
                if _cur_sp is not None:
                    _z_sp  = float(zscore(cn_us_sp).iloc[-1]) if len(cn_us_sp) > 1 else 0
                    _pct_sp = (cn_us_sp < _cur_sp).mean() * 100
                    _col_sp = "#ef4444" if _cur_sp < 0 else "#22c55e"
                    _lbl_sp = ("🔴 美国利率更高，资金偏向流出中国"
                               if _cur_sp < 0 else
                               "🟢 中国利率更高，利差支撑人民币")
                    st.markdown(f"""
                    <div class="kpi-card" style="padding:20px;margin-top:24px;">
                      <div class="kpi-label">中美10Y利差</div>
                      <div class="kpi-value" style="color:{_col_sp};">{_cur_sp:+.2f}%</div>
                      <div class="kpi-label" style="margin-top:10px;">Z-Score</div>
                      <div style="font-size:18px;font-weight:600;color:#f8fafc;">{_z_sp:+.2f}σ</div>
                      <div class="kpi-label" style="margin-top:10px;">历史分位</div>
                      <div style="font-size:16px;font-weight:600;color:#f8fafc;">{_pct_sp:.1f}%</div>
                      <div style="font-size:11px;color:#475569;margin-top:10px;line-height:1.5;">{_lbl_sp}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # 全球国债快照柱图
            st.markdown('<div class="section-title">🌐 中美国债收益率结论</div>',
                        unsafe_allow_html=True)
            _v_us  = safe_val(df, "10Y美债")
            _v_cn  = safe_val(df, "中国10Y国债")
            _v_ffr = safe_val(df, "联邦基金利率")
            _bond_data = [
                ("美国10Y国债", _v_us,  "#3b82f6"),
                ("中国10Y国债", _v_cn,  "#ef4444"),
                ("美联储基准利率", _v_ffr, "#f59e0b"),
            ]
            _bond_data = [(n, v, c) for n, v, c in _bond_data if v is not None]
            if _bond_data:
                _fig_gb = go.Figure(go.Bar(
                    x=[r[0] for r in _bond_data],
                    y=[r[1] for r in _bond_data],
                    marker_color=[r[2] for r in _bond_data],
                    text=[f"{r[1]:.2f}%" for r in _bond_data],
                    textposition="outside",
                    textfont=dict(color="#94a3b8", size=11),
                ))
                _fig_gb.update_layout(**mk_layout(
                    "关键利率水平对比（%）", h=300, show_legend=False))
                st.plotly_chart(_fig_gb, use_container_width=True)

            # 结论文字
            if _cur_sp is not None and _v_us is not None and _v_cn is not None:
                _concl_color = "#ef4444" if _cur_sp < -1 else ("#f59e0b" if _cur_sp < 0 else "#22c55e")
                _concl = (
                    f"当前美国10Y（{_v_us:.2f}%）{'高于' if _cur_sp > 0 else '低于'}"
                    f"中国10Y（{_v_cn:.2f}%），利差为 **{_cur_sp:+.2f}%**。"
                )
                if _cur_sp < -1:
                    _concl += "美国利率大幅高于中国，跨境资本存在较强的流向美国动力，人民币面临贬值压力，A股外资流入受到抑制。建议关注中国央行的汇率调控动作和北向资金动态。"
                elif _cur_sp < 0:
                    _concl += "美国利率略高于中国，汇率承压但尚属可控，需持续跟踪利差走势变化。"
                else:
                    _concl += "中国利率高于美国，利差有助于吸引外资流入中国债券市场，对人民币汇率形成支撑，利好A股和港股外资回流。"
                st.info(_concl)
        else:
            st.info("中美利差数据加载中，需要中国10Y国债（akshare）和美国10Y国债（yfinance）同时可用。")
