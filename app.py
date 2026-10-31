"""
全维度宏观风险监控平台 v4.0
Bloomberg 专业风格 | FRED + yfinance + akshare | 深色主题

应用入口：页面配置 → 侧边栏 → 数据加载 → Hero → 7 个 Tab → 数据源状态
具体实现按职责拆分到 macro_monitor/ 包：
    config.py        配置常量（FRED 序列、行情品种、周期、配色）
    theme.py         全局 CSS 样式
    data_sources.py  yfinance / FRED / akshare 数据抓取
    analytics.py     归一化、统计、宏观情景诊断、衰退概率
    charts.py        Plotly 布局工厂
    components.py    KPI 等 HTML 卡片组件
    sidebar.py       侧边栏控制面板
    views/           7 个 Tab 的页面渲染
"""
import warnings
warnings.filterwarnings("ignore")

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# ─── 页面配置（必须是第一个 Streamlit 调用）────────────────────────────────
st.set_page_config(
    page_title="宏观风险监控平台",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 项目内部模块在 set_page_config 之后导入（config 会读取 st.secrets）
from macro_monitor.theme import apply_theme
from macro_monitor.data_sources import load_all
from macro_monitor.sidebar import render_sidebar
from macro_monitor.views import (
    canvas, dashboard, deep_analysis, diagnosis, early_warning, erp, markets,
)

apply_theme()

# ═══════════════════════════════════════════════════════════════════════════
# 侧边栏
# ═══════════════════════════════════════════════════════════════════════════
period_label, days, align_bd, norm_mode, canvas_sel = render_sidebar()

# ═══════════════════════════════════════════════════════════════════════════
# 加载数据
# ═══════════════════════════════════════════════════════════════════════════
with st.spinner("⏳ 正在拉取全球宏观数据，首次加载约 30-60 秒…"):
    df_all, st_meta = load_all(days)

if df_all.empty:
    st.error("❌ 所有数据源均加载失败，请检查网络连接后刷新。")
    st.stop()

cutoff = pd.Timestamp.today() - timedelta(days=days)
df = df_all[df_all.index >= cutoff].copy()
df.index = pd.to_datetime(df.index)
if align_bd:
    df = df[df.index.dayofweek < 5]

# ═══════════════════════════════════════════════════════════════════════════
# Hero
# ═══════════════════════════════════════════════════════════════════════════
ok_n  = sum(1 for v in st_meta.values() if v == "ok")
all_n = len(st_meta)
st.markdown(f"""
<div class="hero-banner">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;">
    <div>
      <div class="hero-title">📡 全维度宏观风险监控平台</div>
      <div class="hero-sub">
        <span class="live-dot"></span>美股 · 港股 · A股 · 大宗商品 · FRED 宏观
        &nbsp;|&nbsp; 更新时间：{datetime.now().strftime("%Y-%m-%d  %H:%M")}
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:20px;font-weight:700;color:#22c55e;">{ok_n}/{all_n}</div>
      <div style="font-size:10px;color:#475569;letter-spacing:0.5px;">数据源在线</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# 7 个主 Tab
# ═══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🎯 风险仪表盘",
    "🌍 全球市场",
    "🔬 万能画布",
    "💰 股债利差 ERP",
    "🔗 深度分析",
    "🧠 综合诊断",
    "🔮 早期预警雷达",
])

with tab1:
    V, CHG, spread_10_2 = dashboard.render(df)

with tab2:
    markets.render(df, period_label)

with tab3:
    canvas.render(df, period_label, norm_mode, canvas_sel)

with tab4:
    erp.render(df)

with tab5:
    deep_analysis.render(df, period_label)

with tab6:
    diagnosis.render(df, V, spread_10_2)

with tab7:
    early_warning.render(df, period_label)

# ═══════════════════════════════════════════════════════════════════════════
# Footer — 数据源状态
# ═══════════════════════════════════════════════════════════════════════════
with st.expander("📡 数据源状态一览", expanded=False):
    ok_rows   = [{"指标": k, "状态": "✅ 正常"} for k, v in st_meta.items() if v == "ok"]
    fail_rows = [{"指标": k, "状态": "❌ 失败"} for k, v in st_meta.items() if v != "ok"]
    _fc1, _fc2  = st.columns(2)
    _fc1.markdown(f"**✅ 正常 ({len(ok_rows)})**")
    _fc1.dataframe(pd.DataFrame(ok_rows), hide_index=True, use_container_width=True)
    if fail_rows:
        _fc2.markdown(f"**❌ 失败 ({len(fail_rows)})**")
        _fc2.dataframe(pd.DataFrame(fail_rows), hide_index=True, use_container_width=True)

st.markdown("""
<div style='text-align:center;padding:16px 0 6px;font-size:11px;color:#1f2937;'>
  宏观风险监控平台 v4.0 &nbsp;·&nbsp;
  数据来源：yfinance · akshare · FRED &nbsp;·&nbsp;
  仅供研究参考，不构成任何投资建议
</div>
""", unsafe_allow_html=True)
