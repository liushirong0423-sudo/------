"""侧边栏控制面板：时间范围、归一化模式、画布指标选择"""
from datetime import datetime

import streamlit as st

from .config import (
    PERIOD_MAP, YFINANCE_COMMODITY, YFINANCE_EQUITY, YFINANCE_FX,
    YFINANCE_RATES,
)


def render_sidebar():
    """渲染侧边栏，返回 (period_label, days, align_bd, norm_mode, canvas_sel)。"""
    st.markdown("""
    <div style='padding:8px 0 4px;'>
        <div style='font-size:15px;font-weight:700;color:#f8fafc;'>⚙ 控制面板</div>
        <div style='font-size:11px;color:#475569;margin-top:2px;'>全维度宏观监控平台 v4.0</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    period_label = st.selectbox("📅 时间范围", ["1Y","3Y","5Y","Max"], index=2)
    days = PERIOD_MAP[period_label]

    st.divider()
    align_bd  = st.toggle("🔄 对齐交易日", value=True)
    norm_mode = st.radio("📐 归一化模式",
                         ["Z-Score","Min-Max [0,1]","原始值"], index=0)

    st.divider()
    st.markdown('<div style="font-size:11px;color:#475569;font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">万能画布 — 指标选择</div>',
                unsafe_allow_html=True)
    CANVAS_OPTS = (
        list(YFINANCE_EQUITY.keys()) +
        list(YFINANCE_RATES.keys()) +
        ["VIX"] +
        list(YFINANCE_FX.keys()) +
        list(YFINANCE_COMMODITY.keys()) +
        ["中国10Y国债","沪深300","恒生指数","上证综指","创业板指","中证500","科创50",
         "美联储净流动性","美国CPI同比","美高收益债利差","TIPS_10Y实际利率",
         "M2货币供应","中美利差(10Y)","联邦基金利率",
         "铜金比率","Sahm规则指标","10Y-3M利差","金融条件指数","金融压力指数",
         "初申请失业金人数","工业生产指数","建筑许可"]
    )
    canvas_sel = st.multiselect(
        "叠加指标（多选）", CANVAS_OPTS,
        default=["纳斯达克100","10Y美债","VIX","美联储净流动性"],
    )

    st.divider()
    st.markdown(
        f'<div style="font-size:11px;color:#374151;">'
        f'<span class="live-dot"></span>更新：{datetime.now().strftime("%H:%M")}'
        f'  |  缓存 1h</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("🔄 强制刷新"):
        st.cache_data.clear()
        st.rerun()
    return period_label, days, align_bd, norm_mode, canvas_sel
