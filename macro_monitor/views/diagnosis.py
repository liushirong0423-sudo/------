"TAB 6 — 综合诊断：宏观情景引擎、信号清单与异常提示"
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ..analytics import build_macro_regime
from ..charts import mk_layout



def render(df, V, spread_10_2):
    # 复用 Tab1 计算结果（Python with块不创建新作用域，V/spread_10_2 仍在域内）
    mc = build_macro_regime(df, V, spread_10_2)

    # ── 宏观情景总览 ────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🎯 宏观情景总判断</div>', unsafe_allow_html=True)
    _reg_col = mc["regime_color"]
    _rs = mc["risk_score"]
    _rs_color = ("#ef4444" if _rs >= 11 else
                 "#f59e0b" if _rs >= 7 else
                 "#3b82f6" if _rs >= 4 else "#22c55e")
    _rs_label = ("极高风险" if _rs >= 11 else
                 "高风险"   if _rs >= 7 else
                 "中等风险" if _rs >= 4 else "低风险")

    # 信号计数（先于列块计算）
    _n_red = sum(1 for v in mc["signals"].values() if v[0]=="🔴")
    _n_yel = sum(1 for v in mc["signals"].values() if v[0]=="🟡")
    _n_grn = sum(1 for v in mc["signals"].values() if v[0]=="🟢")
    _pct_bar = min(100, _rs / 15 * 100)

    _col_r1, _col_r2, _col_r3 = st.columns([2, 1, 3])
    with _col_r1:
        _wl_html = "".join([
            f'<div style="font-size:11px;color:#94a3b8;margin-bottom:5px;">'
            f'• <span style="color:#f8fafc;font-weight:600;">{wk[0]}</span>'
            f'：{wk[1][:42]}{"\u2026" if len(wk[1])>42 else ""}</div>'
            for wk in mc["watch_list"][:4]
        ]) or '<div style="font-size:11px;color:#22c55e;">暂无触发预警的指标</div>'
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0d1321,{_reg_col}18);
                    border:1px solid {_reg_col}55;border-radius:12px;padding:24px;">
          <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1px;font-weight:600;">当前宏观情景</div>
          <div style="font-size:22px;font-weight:700;color:{_reg_col};margin:10px 0 8px;">{mc['regime']}</div>
          <div style="font-size:12px;color:#94a3b8;line-height:1.7;margin-bottom:14px;">{mc['regime_desc']}</div>
          <div style="display:flex;gap:7px;flex-wrap:wrap;margin-bottom:14px;">
            <span style="background:#ef444420;color:#ef4444;border:1px solid #ef444440;
                         border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600;">异常 {_n_red}</span>
            <span style="background:#f59e0b20;color:#f59e0b;border:1px solid #f59e0b40;
                         border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600;">预警 {_n_yel}</span>
            <span style="background:#22c55e20;color:#22c55e;border:1px solid #22c55e40;
                         border-radius:20px;padding:2px 10px;font-size:11px;font-weight:600;">正常 {_n_grn}</span>
          </div>
          <div style="border-top:1px solid {_reg_col}30;padding-top:12px;">
            <div style="font-size:10px;color:#475569;font-weight:600;letter-spacing:0.8px;
                        text-transform:uppercase;margin-bottom:8px;">📌 当前预警项</div>
            {_wl_html}
          </div>
        </div>
        """, unsafe_allow_html=True)
    with _col_r2:
        st.markdown(f"""
        <div style="background:#0d1321;border:1px solid {_rs_color}55;border-radius:12px;
                    padding:24px;text-align:center;">
          <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1px;font-weight:600;">综合风险评分</div>
          <div style="font-size:48px;font-weight:800;color:{_rs_color};margin:8px 0 2px;line-height:1;">{_rs}</div>
          <div style="font-size:13px;color:{_rs_color};font-weight:600;margin-bottom:14px;">/ 15 &nbsp;·&nbsp; {_rs_label}</div>
          <div style="background:#1e2a3a;border-radius:6px;height:8px;overflow:hidden;margin-bottom:14px;">
            <div style="background:linear-gradient(90deg,#22c55e 0%,#f59e0b 50%,#ef4444 100%);
                        width:100%;height:100%;border-radius:6px;position:relative;">
              <div style="position:absolute;right:{100-_pct_bar:.0f}%;top:0;bottom:0;right:0;
                          background:#0d1321;transition:width 0.5s;
                          width:{100-_pct_bar:.0f}%;"></div>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:5px;margin-bottom:14px;">
            <div style="background:#ef444415;border-radius:6px;padding:7px 2px;">
              <div style="font-size:20px;font-weight:700;color:#ef4444;">{_n_red}</div>
              <div style="font-size:9px;color:#475569;">异常</div>
            </div>
            <div style="background:#f59e0b15;border-radius:6px;padding:7px 2px;">
              <div style="font-size:20px;font-weight:700;color:#f59e0b;">{_n_yel}</div>
              <div style="font-size:9px;color:#475569;">预警</div>
            </div>
            <div style="background:#22c55e15;border-radius:6px;padding:7px 2px;">
              <div style="font-size:20px;font-weight:700;color:#22c55e;">{_n_grn}</div>
              <div style="font-size:9px;color:#475569;">正常</div>
            </div>
          </div>
          <div style="font-size:9px;color:#475569;line-height:1.6;
                      border-top:1px solid #1e2a3a;padding-top:10px;text-align:left;">
            评分维度：通胀 / 就业 / Sahm / 曲线<br>
            信用 / 波动率 / 流动性 / NFCI<br>
            铜金比率 / 10Y-3M / 美元 / 中美利差
          </div>
        </div>
        """, unsafe_allow_html=True)
    with _col_r3:
        _rows_html = ""
        for _asset, _sig in mc["regime_assets"].items():
            _ac = ("#22c55e" if "超配" in _sig else
                   "#ef4444" if any(x in _sig for x in ["低配","谨慎"]) else "#f59e0b")
            _dot = ("●" )
            _rows_html += (
                f'<tr style="border-bottom:1px solid #1e2a3a;">'
                f'<td style="padding:8px 14px;color:#94a3b8;font-size:12px;white-space:nowrap;">{_asset}</td>'
                f'<td style="padding:8px 14px;">'
                f'<span style="color:{_ac};font-size:12px;font-weight:600;">{_sig}</span>'
                f'</td></tr>'
            )
        st.markdown(f"""
        <div style="font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:0.8px;
                    font-weight:600;margin-bottom:8px;">📊 各类资产配置参考信号</div>
        <table style="width:100%;border-collapse:collapse;">
          <thead><tr style="background:#0d1321;">
            <th style="padding:7px 14px;color:#374151;font-size:10px;text-align:left;
                       text-transform:uppercase;letter-spacing:0.8px;font-weight:600;
                       border-bottom:1px solid #1e2a3a;">资产类别</th>
            <th style="padding:7px 14px;color:#374151;font-size:10px;text-align:left;
                       text-transform:uppercase;letter-spacing:0.8px;font-weight:600;
                       border-bottom:1px solid #1e2a3a;">配置信号</th>
          </tr></thead>
          <tbody>{_rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

    st.divider()

    # ── 信号面板 ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🔍 宏观指标信号面板</div>', unsafe_allow_html=True)
    _sig_list = list(mc["signals"].items())
    _sig_cols = st.columns(4)
    for _i, (_key, (_icon, _val, _desc)) in enumerate(_sig_list):
        _bc = "#ef4444" if _icon=="🔴" else ("#f59e0b" if _icon=="🟡" else "#22c55e")
        _sig_cols[_i % 4].markdown(f"""
        <div style="background:#0d1321;border:1px solid {_bc}33;
                    border-left:3px solid {_bc};border-radius:8px;
                    padding:12px 14px;margin:4px 0;min-height:90px;">
          <div style="font-size:9px;color:#475569;text-transform:uppercase;
                      letter-spacing:0.8px;font-weight:600;">{_key}</div>
          <div style="font-size:14px;font-weight:700;color:#f8fafc;margin:5px 0 4px;">{_icon} {_val}</div>
          <div style="font-size:10px;color:#94a3b8;line-height:1.5;">{_desc}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    # ── 重点关注指标清单 ─────────────────────────────────────────────────
    if mc["watch_list"]:
        st.markdown('<div class="section-title">📌 重点关注指标清单</div>', unsafe_allow_html=True)
        st.caption("以下指标当前处于异常区域或触发预警阈值，建议重点跟踪并结合基本面研判")
        _wl_cols = st.columns(2)
        for _i, (_ind, _reason) in enumerate(mc["watch_list"]):
            _wl_cols[_i % 2].markdown(
                f'<div class="alert-card alert-yellow" style="margin:4px 0;">'
                f'<div class="alert-title">📍 {_ind}</div>'
                f'<div class="alert-desc">{_reason}</div></div>',
                unsafe_allow_html=True
            )
        st.divider()

    # ── 极端偏离指标 ─────────────────────────────────────────────────────
    if mc["anomalies"]:
        st.markdown('<div class="section-title">⚡ 极端偏离指标（|Z-Score| > 1.5σ）</div>',
                    unsafe_allow_html=True)
        st.caption("当前偏离历史均值最大的指标，可能预示趋势转折或存在均值回归机会")

        _anom_rows = []
        for _col_a, _zs_a, _val_a in mc["anomalies"]:
            _anom_rows.append({
                "指标":     _col_a,
                "当前值":   f"{_val_a:.4g}",
                "Z-Score":  f"{_zs_a:+.2f}σ",
                "偏离方向": ("📈 极端偏高" if _zs_a > 2 else
                             "⬆ 偏高"     if _zs_a > 1.5 else
                             "📉 极端偏低" if _zs_a < -2 else "⬇ 偏低"),
                "解读":     ("历史高位区间，关注均值回归压力" if _zs_a > 2 else
                             "偏高区间，注意风险"           if _zs_a > 1.5 else
                             "历史低位，关注反弹机会"        if _zs_a < -2 else
                             "偏低区间，注意支撑"),
            })
        st.dataframe(pd.DataFrame(_anom_rows), use_container_width=True, hide_index=True)

        # 偏离度条形图
        _names_a = [r[0] for r in mc["anomalies"]]
        _zs_a_v  = [r[1] for r in mc["anomalies"]]
        _clrs_a  = ["#ef4444" if z > 0 else "#3b82f6" for z in _zs_a_v]
        _fig_an = go.Figure(go.Bar(
            y=_names_a, x=_zs_a_v, orientation="h",
            marker_color=_clrs_a,
            text=[f"{z:+.2f}σ" for z in _zs_a_v],
            textposition="outside",
            textfont=dict(size=10, color="#94a3b8"),
        ))
        for _lv, _lc in [(2,"#ef4444"),(1,"#f59e0b"),(-1,"#f59e0b"),(-2,"#ef4444")]:
            _fig_an.add_vline(x=_lv, line_dash="dash", line_color=_lc, line_width=0.8)
        _fig_an.add_vline(x=0, line_color="#374151", line_width=1)
        _lo_an = mk_layout("极端偏离指标 Z-Score（红=偏高 蓝=偏低）",
                           h=max(280, len(_names_a)*38), l=160, r=80, show_legend=False)
        _lo_an["xaxis"]["range"] = [-4.5, 4.5]
        _lo_an["xaxis"]["title"] = "Z-Score (σ)"
        _fig_an.update_layout(**_lo_an)
        st.plotly_chart(_fig_an, use_container_width=True)

    st.divider()

    # ── 综合结论 ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">📋 综合结论与操作参考</div>', unsafe_allow_html=True)
    _red_sigs   = [(k, v[1]) for k, v in mc["signals"].items() if v[0] == "🔴"]
    _yel_sigs   = [(k, v[1]) for k, v in mc["signals"].items() if v[0] == "🟡"]
    _red_str    = "、".join([f"{k}（{v}）" for k, v in _red_sigs]) if _red_sigs else "暂无极端风险信号"
    _yel_str    = "、".join([f"{k}（{v}）" for k, v in _yel_sigs]) if _yel_sigs else "无"

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0d1321,#111827);
                border:1px solid #1e2a3a;border-radius:12px;padding:24px;margin:8px 0;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;">
        <div>
          <div style="font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:1px;">综合风险等级</div>
          <div style="font-size:26px;font-weight:700;color:{_rs_color};margin-top:4px;">
            {_rs}/15 · {_rs_label}
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:11px;color:#475569;text-transform:uppercase;letter-spacing:1px;">宏观情景</div>
          <div style="font-size:16px;font-weight:600;color:{_reg_col};margin-top:4px;">{mc['regime']}</div>
        </div>
      </div>
      <div style="font-size:12px;color:#94a3b8;line-height:1.9;border-top:1px solid #1e2a3a;padding-top:14px;">
        <div style="margin-bottom:8px;">
          <span style="color:#f8fafc;font-weight:600;">📌 情景研判：</span>{mc['regime_desc']}
        </div>
        <div style="margin-bottom:8px;">
          <span style="color:#ef4444;font-weight:600;">🔴 高风险信号：</span>{_red_str}
        </div>
        <div style="margin-bottom:8px;">
          <span style="color:#f59e0b;font-weight:600;">🟡 需关注信号：</span>{_yel_str}
        </div>
        <div style="margin-bottom:8px;">
          <span style="color:#f8fafc;font-weight:600;">💼 配置参考：</span>
          {'、'.join([f"{a}（{s}）" for a, s in mc['regime_assets'].items()])}
        </div>
        <div style="padding-top:10px;border-top:1px solid #1e2a3a;font-size:10px;color:#374151;">
          ⚠ 免责声明：本平台数据仅供学术研究参考，不构成任何投资建议。市场有风险，投资须谨慎。
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
