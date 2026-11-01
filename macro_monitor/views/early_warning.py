"TAB 7 — 早期预警雷达：衰退概率、劳动力市场、信用与流动性"
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..analytics import recession_probability, safe_val, zscore
from ..charts import mk_layout, secondary_y_axis
from ..components import kpi
from ..config import COLORS, GRID



def render(df, period_label):
    st.markdown("""
    <div class="hero-banner" style="margin-bottom:14px;">
      <div style="font-size:14px;font-weight:700;color:#f8fafc;">🔮 早期预警雷达</div>
      <div style="font-size:11px;color:#64748b;margin-top:4px;">
        基于领先指标体系的宏观风险前瞻预判 ·
        NY Fed衰退概率 · Sahm规则 · 铜金比率 · 金融压力 · 大宗商品信号
      </div>
    </div>
    """, unsafe_allow_html=True)

    ew_sub1, ew_sub2, ew_sub3 = st.tabs([
        "📉 衰退概率仪表", "💹 金融压力监测", "🌿 大宗商品信号"
    ])

    # ────────────────────────────────────────────────────────────────────
    # Sub1 — 衰退概率仪表
    # ────────────────────────────────────────────────────────────────────
    with ew_sub1:
        st.markdown('<div class="section-title">📉 衰退前瞻预判体系</div>',
                    unsafe_allow_html=True)

        _sp10y3m  = safe_val(df, "10Y-3M利差")
        _rec_prob = recession_probability(_sp10y3m)
        _sahm_v   = safe_val(df, "Sahm规则指标")
        _icsa_v   = safe_val(df, "初申请失业金人数")
        _unrate_v = safe_val(df, "美国失业率")

        # KPI 行
        ew_k1, ew_k2, ew_k3, ew_k4 = st.columns(4)
        _rpc = "#ef4444" if _rec_prob > 40 else ("#f59e0b" if _rec_prob > 20 else "#22c55e")
        ew_k1.markdown(f"""
        <div class="kpi-card" style="border-color:{_rpc}55;">
          <div class="kpi-label">衰退概率 (12M)</div>
          <div class="kpi-value" style="color:{_rpc};">{_rec_prob:.1f}%</div>
          <div class="kpi-change" style="color:#64748b;">NY Fed 利率曲线模型</div>
        </div>""", unsafe_allow_html=True)

        ew_k2.markdown(kpi("10Y-3M利差", _sp10y3m, None, "%", fmt="+"),
                       unsafe_allow_html=True)

        _sahm_c = ("#ef4444" if _sahm_v is not None and _sahm_v >= 0.5 else
                   "#f59e0b" if _sahm_v is not None and _sahm_v >= 0.3 else "#22c55e")
        _sahm_lbl = ("🔴 已触发衰退" if _sahm_v is not None and _sahm_v >= 0.5 else
                     "🟡 预警区间"   if _sahm_v is not None and _sahm_v >= 0.3 else "🟢 安全")
        ew_k3.markdown(f"""
        <div class="kpi-card" style="border-color:{_sahm_c}55;">
          <div class="kpi-label">Sahm 规则指标</div>
          <div class="kpi-value" style="color:{_sahm_c};">{f'{_sahm_v:.2f}' if _sahm_v is not None else 'N/A'}</div>
          <div class="kpi-change" style="color:#64748b;">{_sahm_lbl} (触发线 = 0.5)</div>
        </div>""", unsafe_allow_html=True)

        ew_k4.markdown(kpi("初申请失业金(千人)", _icsa_v, None, "", fmt=","),
                       unsafe_allow_html=True)

        st.divider()

        # 图表区
        _ewc1, _ewc2 = st.columns(2)

        with _ewc1:
            if "10Y-3M利差" in df.columns:
                _sp3m_s = df["10Y-3M利差"].dropna()
                _clrs_3m = ["#ef4444" if x < 0 else "#22c55e" for x in _sp3m_s.values]
                _fig_3m = go.Figure()
                _fig_3m.add_trace(go.Bar(
                    x=_sp3m_s.index, y=_sp3m_s.values,
                    marker_color=_clrs_3m, opacity=0.85, name="10Y-3M",
                ))
                _fig_3m.add_hline(y=0, line_color="#d1d5db", line_width=0.8)
                _fig_3m.update_layout(**mk_layout(
                    "10Y-3M 利差（红=倒挂 · NY Fed 衰退预测核心变量）",
                    h=310, show_legend=False))
                st.plotly_chart(_fig_3m, use_container_width=True)
                st.caption(
                    "• 10Y-3M 倒挂是 NY Fed 官方衰退模型的核心输入，预测力强于 10Y-2Y\n"
                    "• 每次倒挂后平均 6-18 个月出现衰退（Estrella & Mishkin 1998）\n"
                    f"• 当前衰退概率估算：**{_rec_prob:.1f}%**"
                )
            else:
                st.info("10Y-3M 利差数据加载中（FRED: T10Y3M）")

        with _ewc2:
            if "Sahm规则指标" in df.columns:
                _sahm_s = df["Sahm规则指标"].dropna()
                _fig_sahm = go.Figure()
                _fig_sahm.add_trace(go.Scatter(
                    x=_sahm_s.index, y=_sahm_s.values, name="Sahm规则",
                    line=dict(color="#a855f7", width=2),
                    fill="tozeroy", fillcolor="rgba(168,85,247,0.08)",
                ))
                _fig_sahm.add_hline(y=0.5, line_dash="dash", line_color="#ef4444",
                                    line_width=1.2,
                                    annotation_text="0.5 衰退触发线",
                                    annotation_font=dict(color="#ef4444", size=9))
                _fig_sahm.add_hline(y=0.3, line_dash="dash", line_color="#f59e0b",
                                    line_width=0.8,
                                    annotation_text="0.3 预警线",
                                    annotation_font=dict(color="#f59e0b", size=9))
                _fig_sahm.update_layout(**mk_layout(
                    "Sahm 规则指标（失业率3月均值 − 过去12月最低值）",
                    h=310, show_legend=False))
                st.plotly_chart(_fig_sahm, use_container_width=True)
                st.caption(
                    "• **Sahm ≥ 0.5**：历史上每次衰退均被准确识别，无漏报记录\n"
                    "• 由前美联储经济学家 Claudia Sahm 于 2019 年提出，现为 NBER 参考指标\n"
                    "• 相比 NBER 官方衰退认定，实时性超前约 4-8 个月"
                )
            else:
                st.info("Sahm 规则基于失业率计算（需 FRED: UNRATE）")

        # 初申请失业金趋势
        if "初申请失业金人数" in df.columns:
            st.markdown('<div class="section-title">📋 初申请失业金趋势（周频高频领先指标）</div>',
                        unsafe_allow_html=True)
            _icsa_s = df["初申请失业金人数"].dropna()
            _fig_icsa = make_subplots(specs=[[{"secondary_y": True}]])
            _fig_icsa.add_trace(go.Scatter(
                x=_icsa_s.index, y=_icsa_s.values, name="初申请(千人)",
                line=dict(color="#06b6d4", width=1.8),
                fill="tozeroy", fillcolor="rgba(6,182,212,0.07)",
            ), secondary_y=False)
            _icsa_ma4 = _icsa_s.rolling(4).mean()
            _fig_icsa.add_trace(go.Scatter(
                x=_icsa_ma4.index, y=_icsa_ma4.values, name="4周均线",
                line=dict(color="#f59e0b", width=2, dash="dash"),
            ), secondary_y=False)
            _fig_icsa.add_hline(
                y=300, secondary_y=False,
                line_dash="dash", line_color="#ef4444", line_width=0.8,
                annotation_text="30万 警戒线",
                annotation_font=dict(color="#ef4444", size=9),
            )
            _lo_ic = mk_layout(
                "美国初申请失业金人数（千人）— 每周四发布，领先非农约1-2周",
                h=300)
            _fig_icsa.update_layout(**_lo_ic)
            _fig_icsa.update_yaxes(title_text="人数（千）", secondary_y=False, gridcolor=GRID)
            st.plotly_chart(_fig_icsa, use_container_width=True)
            st.caption(
                "• 初申请失业金（Initial Claims）是最高频的劳动市场先行信号，每周四上午8:30公布\n"
                "• 4周均线升破 **30万人** 通常预示就业市场明显降温，进入衰退风险区\n"
                "• 2020年3月曾在一周内从20万骤升至600万+，是衰退爆发的极端先行信号"
            )

    # ────────────────────────────────────────────────────────────────────
    # Sub2 — 金融压力监测
    # ────────────────────────────────────────────────────────────────────
    with ew_sub2:
        st.markdown('<div class="section-title">💹 金融市场压力综合监测</div>',
                    unsafe_allow_html=True)

        _ew2c1, _ew2c2 = st.columns(2)

        with _ew2c1:
            if "金融条件指数" in df.columns:
                _nfci_s = df["金融条件指数"].dropna()
                _fig_nfci = go.Figure()
                _fig_nfci.add_trace(go.Scatter(
                    x=_nfci_s.index, y=_nfci_s.values, name="NFCI",
                    line=dict(color="#3b82f6", width=2),
                    fill="tozeroy", fillcolor="rgba(59,130,246,0.07)",
                ))
                _fig_nfci.add_hline(y=0, line_color="#475569", line_width=1,
                                    annotation_text="历史均值=0",
                                    annotation_font=dict(color="#475569", size=9))
                _fig_nfci.add_hline(y=0.3, line_dash="dash", line_color="#ef4444",
                                    line_width=0.8,
                                    annotation_text="0.3 偏紧警戒",
                                    annotation_font=dict(color="#ef4444", size=9))
                _fig_nfci.update_layout(**mk_layout(
                    "芝加哥联储金融条件指数 NFCI（<0 宽松 / >0 收紧）",
                    h=320, show_legend=False))
                st.plotly_chart(_fig_nfci, use_container_width=True)
                st.caption(
                    "NFCI 综合反映信贷市场、股票市场和影子银行系统的金融条件，"
                    "覆盖 105 个金融指标，历史均值=0，越高越紧"
                )
            else:
                st.info("NFCI 数据加载中（FRED: NFCI）")

        with _ew2c2:
            if "金融压力指数" in df.columns:
                _fsi_s = df["金融压力指数"].dropna()
                _fig_fsi = go.Figure()
                _fig_fsi.add_trace(go.Scatter(
                    x=_fsi_s.index, y=_fsi_s.values, name="STLFSI",
                    line=dict(color="#a855f7", width=2),
                    fill="tozeroy", fillcolor="rgba(168,85,247,0.07)",
                ))
                _fig_fsi.add_hline(y=0, line_color="#475569", line_width=1,
                                   annotation_text="历史均值=0",
                                   annotation_font=dict(color="#475569", size=9))
                _fig_fsi.update_layout(**mk_layout(
                    "圣路易斯联储金融压力指数 STLFSI（>0 压力上升）",
                    h=320, show_legend=False))
                st.plotly_chart(_fig_fsi, use_container_width=True)
                st.caption(
                    "STLFSI 基于 18 个金融市场变量（国债/MBS/货币市场/企业债/股权溢价）综合计算，"
                    "每周更新，是金融压力的高频实时信号"
                )
            else:
                st.info("金融压力指数加载中（FRED: STLFSI4）")

        # 工业生产指数
        if "工业生产指数" in df.columns:
            st.markdown('<div class="section-title">🏭 工业生产指数（经济周期同步指标）</div>',
                        unsafe_allow_html=True)
            _indpro_s = df["工业生产指数"].dropna()
            _fig_ip = make_subplots(specs=[[{"secondary_y": True}]])
            _fig_ip.add_trace(go.Scatter(
                x=_indpro_s.index, y=_indpro_s.values, name="工业生产指数",
                line=dict(color="#22c55e", width=2),
            ), secondary_y=False)
            _ip_mom = _indpro_s.pct_change().dropna() * 100
            _fig_ip.add_trace(go.Bar(
                x=_ip_mom.index, y=_ip_mom.values, name="环比(%)",
                marker_color=["#22c55e" if x >= 0 else "#ef4444" for x in _ip_mom.values],
                opacity=0.55,
            ), secondary_y=True)
            _lo_ip = mk_layout("美国工业生产指数 & 环比变化率（FRED: INDPRO）", h=300)
            _lo_ip["yaxis2"] = secondary_y_axis()
            _lo_ip["yaxis2"]["title"] = "环比(%)"
            _fig_ip.update_layout(**_lo_ip)
            _fig_ip.update_yaxes(title_text="指数（2017=100）", secondary_y=False, gridcolor=GRID)
            st.plotly_chart(_fig_ip, use_container_width=True)
            st.caption(
                "工业生产指数是 NBER 经济周期识别委员会使用的 4 大官方参考指标之一，"
                "月频下降连续 2-3 个月通常预示经济步入收缩阶段"
            )

    # ────────────────────────────────────────────────────────────────────
    # Sub3 — 大宗商品信号
    # ────────────────────────────────────────────────────────────────────
    with ew_sub3:
        st.markdown('<div class="section-title">🌿 大宗商品宏观信号解读</div>',
                    unsafe_allow_html=True)
        st.caption("大宗商品价格体系蕴含全球增长预期、通胀压力和避险情绪的前瞻信号")

        # 铜金比率
        if "铜金比率" in df.columns:
            _cau_s = df["铜金比率"].dropna()
            _ew3c1, _ew3c2 = st.columns([3, 1])
            with _ew3c1:
                _fig_cau = make_subplots(specs=[[{"secondary_y": True}]])
                _fig_cau.add_trace(go.Scatter(
                    x=_cau_s.index, y=_cau_s.values, name="铜金比率(×1000)",
                    line=dict(color="#fb923c", width=2),
                    fill="tozeroy", fillcolor="rgba(251,146,60,0.08)",
                ), secondary_y=False)
                if "10Y美债" in df.columns:
                    _tnx_cau = df["10Y美债"].dropna()
                    _fig_cau.add_trace(go.Scatter(
                        x=_tnx_cau.index, y=_tnx_cau.values, name="10Y美债(%)",
                        line=dict(color="#3b82f6", width=1.4, dash="dash"), opacity=0.8,
                    ), secondary_y=True)
                _lo_cau = mk_layout(
                    "铜金比率（×1000）vs 10Y 美债收益率 — 全球增长信号", h=360)
                _lo_cau["yaxis2"] = secondary_y_axis()
                _lo_cau["yaxis2"]["title"] = "10Y美债(%)"
                _fig_cau.update_layout(**_lo_cau)
                _fig_cau.update_yaxes(title_text="铜金比率", secondary_y=False, gridcolor=GRID)
                st.plotly_chart(_fig_cau, use_container_width=True)
            with _ew3c2:
                _cau_cur = float(_cau_s.iloc[-1])
                _cau_z   = float(zscore(_cau_s).iloc[-1]) if len(_cau_s) > 1 else 0.0
                _cau_pct = (_cau_s < _cau_cur).mean() * 100
                _cau_col = "#22c55e" if _cau_z > 0 else "#ef4444"
                _cau_lbl = ("📈 全球增长乐观" if _cau_z > 0.5 else
                             "📉 增长担忧上升" if _cau_z < -0.5 else "➡️ 中性")
                st.markdown(f"""
                <div class="kpi-card" style="padding:20px;margin-top:24px;">
                  <div class="kpi-label">铜金比率</div>
                  <div class="kpi-value" style="color:{_cau_col};">{_cau_cur:.3f}</div>
                  <div class="kpi-label" style="margin-top:10px;">Z-Score</div>
                  <div style="font-size:18px;font-weight:600;color:#f8fafc;">{_cau_z:+.2f}σ</div>
                  <div class="kpi-label" style="margin-top:10px;">历史分位</div>
                  <div style="font-size:16px;font-weight:600;color:#f8fafc;">{_cau_pct:.1f}%</div>
                  <div style="font-size:11px;color:#475569;margin-top:8px;line-height:1.6;">{_cau_lbl}</div>
                </div>
                """, unsafe_allow_html=True)

            st.caption(
                "• **铜金比↑** → 工业需求强于避险需求，市场预期经济强劲，利率通常随之上行\n"
                "• **铜金比↓** → 避险情绪主导，担忧经济前景，利率通常随之下行\n"
                "• 铜被称为'有 PhD 的金属'（Dr. Copper），因其与全球经济活动高度正相关"
            )
        else:
            st.info("铜金比率需铜（HG=F）和黄金（GC=F）数据同时可用。")

        st.divider()

        # 全球大宗商品价格基准化对比
        _comm_sel = [c for c in ["布伦特原油", "原油WTI", "铜", "黄金", "白银", "天然气"]
                     if c in df.columns]
        if len(_comm_sel) >= 2:
            st.markdown('<div class="section-title">🌾 全球大宗商品价格（基准化=100）</div>',
                        unsafe_allow_html=True)
            _fig_comm = go.Figure()
            for _i, _cnm in enumerate(_comm_sel):
                _s_c = df[_cnm].dropna()
                if _s_c.empty:
                    continue
                _fig_comm.add_trace(go.Scatter(
                    x=_s_c.index,
                    y=(_s_c / _s_c.iloc[0] * 100).values,
                    name=_cnm,
                    line=dict(color=COLORS[_i % len(COLORS)], width=1.8),
                ))
            _fig_comm.add_hline(y=100, line_dash="dot",
                                line_color="#374151", line_width=1)
            _fig_comm.update_layout(**mk_layout(
                f"大宗商品价格对比（起点=100，{period_label}）", h=380))
            st.plotly_chart(_fig_comm, use_container_width=True)
            st.caption(
                "• **原油↑** → 输入型通胀，压缩企业利润率，打压消费信心\n"
                "• **铜与原油同向上涨** → 需求驱动的大宗商品牛市，经济扩张信号\n"
                "• **金银比↑** → 避险情绪占优，白银工业属性被压制；反之则复苏预期升温"
            )

        # 建筑许可（房地产领先指标）
        if "建筑许可" in df.columns:
            st.markdown('<div class="section-title">🏠 建筑许可（房地产周期领先指标）</div>',
                        unsafe_allow_html=True)
            _permit_s = df["建筑许可"].dropna()
            _permit_ma3 = _permit_s.rolling(3).mean()
            _fig_permit = go.Figure()
            _fig_permit.add_trace(go.Scatter(
                x=_permit_s.index, y=_permit_s.values, name="建筑许可(千套)",
                line=dict(color="#f59e0b", width=1.6),
                fill="tozeroy", fillcolor="rgba(245,158,11,0.07)",
            ))
            _fig_permit.add_trace(go.Scatter(
                x=_permit_ma3.index, y=_permit_ma3.values, name="3月均线",
                line=dict(color="#ef4444", width=1.8, dash="dash"),
            ))
            _fig_permit.update_layout(**mk_layout(
                "美国建筑许可（千套/月）— 领先经济周期 6-12 个月", h=280))
            st.plotly_chart(_fig_permit, use_container_width=True)
            st.caption(
                "• 建筑许可是 NBER 和 Conference Board LEI 使用的官方领先指标之一\n"
                "• 领先经济周期约 6-12 个月，持续下滑通常预示经济活动收缩\n"
                "• 利率上升 → 贷款成本增加 → 建筑许可下降，呈现典型的货币政策传导链"
            )
