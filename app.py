"""
全维度宏观风险监控平台 v2.0
Bloomberg 专业风格 | FRED + yfinance + akshare | 深色主题
"""
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests

# ─── 页面配置（必须是第一个 Streamlit 调用）────────────────────────────────
st.set_page_config(
    page_title="宏观风险监控平台",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# 全局样式 — Bloomberg 深色金融风格
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif !important; }
.stApp { background: #080c14; color: #d1d5db; }

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1321 0%, #0a0f1e 100%);
    border-right: 1px solid #1e2a3a;
}

/* Hero 顶部 */
.hero-banner {
    background: linear-gradient(135deg, #0d1321 0%, #0f1f3d 50%, #0d1321 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #1e40af, #3b82f6, #06b6d4, #3b82f6, #1e40af);
}
.hero-title { font-size: 24px; font-weight: 700; color: #f8fafc; letter-spacing: -0.3px; margin: 0; }
.hero-sub   { font-size: 13px; color: #64748b; margin: 4px 0 0; }
.live-dot {
    display: inline-block; width: 7px; height: 7px;
    background: #22c55e; border-radius: 50%; margin-right: 6px;
    animation: pulse 2s infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* 警报卡片 */
.alert-card { border-radius: 8px; padding: 14px 16px; margin: 4px 0; border-left: 3px solid; }
.alert-red    { background: rgba(220,38,38,0.1);  border-color: #ef4444; }
.alert-green  { background: rgba(34,197,94,0.1);  border-color: #22c55e; }
.alert-yellow { background: rgba(234,179,8,0.1);  border-color: #eab308; }
.alert-blue   { background: rgba(59,130,246,0.1); border-color: #3b82f6; }
.alert-title  { font-size: 13px; font-weight: 600; color: #f8fafc; }
.alert-desc   { font-size: 11px; color: #94a3b8; margin-top: 2px; }

/* KPI 卡片 */
.kpi-card {
    background: linear-gradient(135deg, #0d1321, #111827);
    border: 1px solid #1e2a3a;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
    transition: border-color 0.2s;
}
.kpi-card:hover { border-color: #3b82f6; }
.kpi-label { font-size: 10px; font-weight: 500; color: #64748b; text-transform: uppercase; letter-spacing: 0.8px; }
.kpi-value { font-size: 20px; font-weight: 700; color: #f8fafc; margin: 4px 0 2px; font-variant-numeric: tabular-nums; }
.kpi-up    { color: #22c55e !important; }
.kpi-down  { color: #ef4444 !important; }
.kpi-na    { color: #475569 !important; }
.kpi-change{ font-size: 11px; font-weight: 500; }

/* Section 标题 */
.section-title {
    font-size: 11px; font-weight: 600; color: #475569;
    text-transform: uppercase; letter-spacing: 1.2px;
    margin: 16px 0 10px; padding-bottom: 6px;
    border-bottom: 1px solid #1e2a3a;
}

/* Tab */
.stTabs [data-baseweb="tab-list"] { background: #0d1321; border-bottom: 1px solid #1e2a3a; gap: 0; }
.stTabs [data-baseweb="tab"]       { background: transparent; color: #64748b; font-size: 13px; font-weight: 500; padding: 10px 18px; border-bottom: 2px solid transparent; }
.stTabs [aria-selected="true"]     { color: #3b82f6 !important; border-bottom: 2px solid #3b82f6 !important; background: transparent !important; }

hr { border-color: #1e2a3a !important; margin: 12px 0 !important; }

/* 侧边栏按钮 */
.stButton > button {
    background: linear-gradient(135deg, #1e40af, #1d4ed8);
    color: #f8fafc; border: none; border-radius: 6px;
    font-weight: 500; font-size: 13px; width: 100%;
}
.stButton > button:hover { background: linear-gradient(135deg, #2563eb, #3b82f6); }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════════════════════════════
FRED_API_KEY = st.secrets.get("FRED_API_KEY", "8923281d30974da13834d8350c0d9669")

YFINANCE_EQUITY = {
    "纳斯达克100": "^NDX",
    "标普500":    "^GSPC",
    "道琼斯":     "^DJI",
    "罗素2000":   "^RUT",
    "MSCI新兴市场": "EEM",
    "日经225":    "^N225",
    "德国DAX":    "^GDAXI",
    "英国富时100": "^FTSE",
}
YFINANCE_RATES = {
    "2Y美债":  "^IRX",
    "5Y美债":  "^FVX",
    "10Y美债": "^TNX",
    "30Y美债": "^TYX",
}
YFINANCE_RISK = {
    "VIX": "^VIX",
}
YFINANCE_FX = {
    "美元指数":   "DX-Y.NYB",
    "欧元/美元": "EURUSD=X",
    "美元/日元": "JPY=X",
    "美元/人民币":"CNY=X",
}
YFINANCE_COMMODITY = {
    "黄金":     "GC=F",
    "原油WTI":  "CL=F",
    "布伦特原油": "BZ=F",
    "铜":       "HG=F",
    "白银":     "SI=F",
    "天然气":   "NG=F",
    "小麦":     "ZW=F",
    "玉米":     "ZC=F",
}
YFINANCE_VOLATILITY = {
    "VVIX":    "^VVIX",   # Volatility of VIX — 市场对市场的波动性
    "SKEW指数": "^SKEW",  # CBOE Skew — 尾部风险溢价
}
YFINANCE_CRYPTO = {
    "比特币": "BTC-USD",
}

ALL_YFINANCE = {
    **YFINANCE_EQUITY, **YFINANCE_RATES, **YFINANCE_RISK,
    **YFINANCE_FX, **YFINANCE_COMMODITY, **YFINANCE_VOLATILITY, **YFINANCE_CRYPTO,
}

# FRED序列配置：{显示名: FRED series_id}
FRED_SERIES = {
    "美联储总资产":    "WALCL",
    "财政部TGA":       "WTREGEN",
    "隔夜逆回购RRP":   "RRPONTSYD",
    "美国CPI同比":     "CPIAUCSL",
    "核心PCE同比":     "PCEPILFE",
    "10Y盈亏平衡通胀": "T10YIE",
    "5Y5Y远期通胀":    "T5YIFR",
    "TIPS_10Y实际利率": "DFII10",
    "美国失业率":      "UNRATE",
    "美高收益债利差":  "BAMLH0A0HYM2",
    "美投资级债利差":  "BAMLC0A0CM",
    "M2货币供应":      "M2SL",
    "密歇根消费信心":  "UMCSENT",
    "联邦基金利率":    "FEDFUNDS",
    # ── 高频领先指标 ──
    "初申请失业金人数": "ICSA",       # 周频，最高频就业先行指标
    "金融条件指数":    "NFCI",        # 芝加哥联储，周频
    "金融压力指数":    "STLFSI4",     # 圣路易斯联储，周频
    "10Y-3M利差":     "T10Y3M",      # 日频，NY Fed衰退概率模型核心变量
    "工业生产指数":    "INDPRO",      # 月频，经济周期同步指标
    "建筑许可":        "PERMIT",      # 月频，房地产周期领先6-12月
}

PERIOD_MAP = {"1Y": 365, "3Y": 1095, "5Y": 1825, "Max": 3650}

COLORS = [
    "#3b82f6","#ef4444","#22c55e","#a855f7",
    "#f59e0b","#06b6d4","#f97316","#84cc16",
    "#ec4899","#14b8a6","#8b5cf6","#fb923c",
]

BG      = "#080c14"
BG_CARD = "#0d1321"
BORDER  = "#1e2a3a"
GRID    = "#131c2e"
TEXT    = "#d1d5db"

# ═══════════════════════════════════════════════════════════════════════════
# Plotly 通用布局工厂
# ═══════════════════════════════════════════════════════════════════════════
def mk_layout(title="", h=460, l=60, r=40, t=48, b=40,
              show_legend=True, hovermode="x unified"):
    return dict(
        title=dict(text=title, font=dict(color="#94a3b8", size=13, family="Inter"),
                   x=0, xanchor="left"),
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family="Inter, Arial, sans-serif", size=11),
        height=h,
        margin=dict(l=l, r=r, t=t, b=b),
        legend=dict(
            bgcolor="rgba(13,19,33,0.95)", bordercolor=BORDER, borderwidth=1,
            font=dict(size=11), orientation="h",
            yanchor="bottom", y=1.01, xanchor="left", x=0,
        ) if show_legend else dict(visible=False),
        xaxis=dict(gridcolor=GRID, zerolinecolor=BORDER,
                   tickfont=dict(size=10), linecolor=BORDER, showline=True),
        yaxis=dict(gridcolor=GRID, zerolinecolor=BORDER,
                   tickfont=dict(size=10), linecolor=BORDER, showline=True),
        hovermode=hovermode,
    )

def secondary_y_axis():
    return dict(gridcolor=GRID, tickfont=dict(size=10), side="right",
                showgrid=False, linecolor=BORDER, showline=True)

# ═══════════════════════════════════════════════════════════════════════════
# 数据获取层
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_yf_batch(days: int) -> dict:
    """批量拉取 yfinance 数据，失败则逐个降级"""
    try:
        import yfinance as yf
    except ImportError:
        return {}

    end   = datetime.today()
    start = end - timedelta(days=days + 10)
    result = {}

    # 先尝试批量
    try:
        tickers_str = " ".join(ALL_YFINANCE.values())
        raw = yf.download(tickers_str, start=start, end=end,
                          auto_adjust=True, progress=False, group_by="ticker")
        for name, ticker in ALL_YFINANCE.items():
            try:
                if isinstance(raw.columns, pd.MultiIndex):
                    s = raw["Close"][ticker].dropna()
                else:
                    s = raw["Close"].dropna()
                s.index = pd.to_datetime(s.index).tz_localize(None)
                s.name  = name
                if not s.empty:
                    result[name] = s
            except Exception:
                pass
        if result:
            return result
    except Exception:
        pass

    # 逐个降级
    for name, ticker in ALL_YFINANCE.items():
        try:
            df = yf.download(ticker, start=start, end=end,
                             auto_adjust=True, progress=False)
            if df.empty:
                continue
            s = df["Close"].iloc[:, 0] if isinstance(df.columns, pd.MultiIndex) else df["Close"]
            s.index = pd.to_datetime(s.index).tz_localize(None)
            s.name  = name
            result[name] = s.dropna()
        except Exception:
            pass
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred_one(series_id: str, days: int) -> pd.Series:
    """拉取单条 FRED 序列"""
    try:
        end   = datetime.today().strftime("%Y-%m-%d")
        start = (datetime.today() - timedelta(days=days + 10)).strftime("%Y-%m-%d")
        url   = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id={series_id}&api_key={FRED_API_KEY}"
            f"&observation_start={start}&observation_end={end}&file_type=json"
        )
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        obs  = resp.json().get("observations", [])
        data = {pd.Timestamp(o["date"]): float(o["value"])
                for o in obs if o["value"] not in (".", "")}
        s = pd.Series(data, name=series_id)
        return s.sort_index()
    except Exception:
        return pd.Series(dtype=float, name=series_id)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred_all(days: int) -> dict:
    result = {}
    for name, sid in FRED_SERIES.items():
        s = fetch_fred_one(sid, days)
        if not s.empty:
            s.name   = name
            result[name] = s
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cn_bond(days: int) -> pd.Series:
    try:
        import akshare as ak
        df = ak.bond_zh_us_rate(start_date="20150101")
        col = next((c for c in df.columns if "中国" in c and "10" in c), None)
        if col is None:
            col = next((c for c in df.columns if "10" in c and c != "日期"), None)
        if col is None:
            return pd.Series(dtype=float)
        date_col = "日期" if "日期" in df.columns else df.columns[0]
        df.index = pd.to_datetime(df[date_col])
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        s.name = "中国10Y国债"
        return s[s.index >= pd.Timestamp(datetime.today() - timedelta(days=days + 10))]
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_csi300(days: int) -> tuple:
    cutoff = pd.Timestamp(datetime.today() - timedelta(days=days + 10))
    try:
        import akshare as ak
        df    = ak.stock_zh_index_daily(symbol="sh000300")
        df.index = pd.to_datetime(df["date"])
        price = pd.to_numeric(df["close"], errors="coerce").dropna()
        price.name = "沪深300"
        price = price[price.index >= cutoff]

        pe = pd.Series(dtype=float)
        try:
            pe_df = ak.index_value_name_fundation(symbol="沪深300")
            if pe_df is not None and not pe_df.empty:
                pe_df.index = pd.to_datetime(pe_df.iloc[:, 0])
                pe_col = next(
                    (c for c in pe_df.columns if "pe" in c.lower() or "市盈" in c), None
                )
                if pe_col:
                    pe = pd.to_numeric(pe_df[pe_col], errors="coerce").dropna()
                    pe.name = "沪深300_PE"
                    pe = pe[pe.index >= cutoff]
        except Exception:
            pass
        return price, pe
    except Exception:
        return pd.Series(dtype=float), pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_hsi(days: int) -> pd.Series:
    try:
        import akshare as ak
        df = ak.stock_hk_index_daily_em(symbol="恒生指数")
        df.index = pd.to_datetime(df["date"])
        s = pd.to_numeric(df["close"], errors="coerce").dropna()
        s.name = "恒生指数"
        return s[s.index >= pd.Timestamp(datetime.today() - timedelta(days=days + 10))]
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cn_macro(days: int) -> dict:
    result = {}
    cutoff = pd.Timestamp(datetime.today() - timedelta(days=days + 10))
    try:
        import akshare as ak
        # 中国CPI
        try:
            cpi = ak.macro_china_cpi_yearly()
            if cpi is not None and not cpi.empty:
                cpi.index = pd.to_datetime(cpi.iloc[:, 0])
                vc = next((c for c in cpi.columns if "今值" in c or c == cpi.columns[1]), None)
                if vc:
                    s = pd.to_numeric(cpi[vc], errors="coerce").dropna()
                    s.name = "中国CPI同比"
                    result["中国CPI同比"] = s[s.index >= cutoff]
        except Exception:
            pass
        # 中国PMI制造业
        try:
            pmi = ak.macro_china_pmi_yearly()
            if pmi is not None and not pmi.empty:
                pmi.index = pd.to_datetime(pmi.iloc[:, 0])
                vc = next((c for c in pmi.columns if "今值" in c or c == pmi.columns[1]), None)
                if vc:
                    s = pd.to_numeric(pmi[vc], errors="coerce").dropna()
                    s.name = "中国PMI制造业"
                    result["中国PMI制造业"] = s[s.index >= cutoff]
        except Exception:
            pass
    except Exception:
        pass
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cn_indices(days: int) -> dict:
    """获取中国A股主要指数（akshare）"""
    result = {}
    cutoff = pd.Timestamp(datetime.today() - timedelta(days=days + 10))
    try:
        import akshare as ak
        index_map = {
            "上证综指": "sh000001",
            "创业板指": "sz399006",
            "中证500":  "sh000905",
            "科创50":   "sh000688",
        }
        for name, symbol in index_map.items():
            try:
                df_idx = ak.stock_zh_index_daily(symbol=symbol)
                df_idx.index = pd.to_datetime(df_idx["date"])
                s = pd.to_numeric(df_idx["close"], errors="coerce").dropna()
                s.name = name
                s = s[s.index >= cutoff]
                if not s.empty:
                    result[name] = s
            except Exception:
                pass
    except Exception:
        pass
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_cn_macro_extended(days: int) -> dict:
    """获取中国扩展宏观数据：PPI、财新PMI、M2同比"""
    result = {}
    cutoff = pd.Timestamp(datetime.today() - timedelta(days=days + 10))
    try:
        import akshare as ak
        # 中国PPI同比
        try:
            ppi = ak.macro_china_ppi_yearly()
            if ppi is not None and not ppi.empty:
                ppi.index = pd.to_datetime(ppi.iloc[:, 0])
                vc = next((c for c in ppi.columns if "今值" in c or c == ppi.columns[1]), None)
                if vc:
                    s = pd.to_numeric(ppi[vc], errors="coerce").dropna()
                    s.name = "中国PPI同比"
                    result["中国PPI同比"] = s[s.index >= cutoff]
        except Exception:
            pass
        # 财新PMI制造业
        try:
            pmi_cx = ak.macro_china_caixin_pmi_yearly()
            if pmi_cx is not None and not pmi_cx.empty:
                pmi_cx.index = pd.to_datetime(pmi_cx.iloc[:, 0])
                vc = next((c for c in pmi_cx.columns if "今值" in c or c == pmi_cx.columns[1]), None)
                if vc:
                    s = pd.to_numeric(pmi_cx[vc], errors="coerce").dropna()
                    s.name = "财新PMI制造业"
                    result["财新PMI制造业"] = s[s.index >= cutoff]
        except Exception:
            pass
        # 中国M2同比
        try:
            m2 = ak.macro_china_m2_yearly()
            if m2 is not None and not m2.empty:
                m2.index = pd.to_datetime(m2.iloc[:, 0])
                vc = next((c for c in m2.columns if "今值" in c or c == m2.columns[1]), None)
                if vc:
                    s = pd.to_numeric(m2[vc], errors="coerce").dropna()
                    s.name = "中国M2同比"
                    result["中国M2同比"] = s[s.index >= cutoff]
        except Exception:
            pass
    except Exception:
        pass
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def load_all(days: int):
    """汇总所有数据源 → 宽表 DataFrame + 状态字典"""
    data, status = {}, {}

    # yfinance
    yf_data = fetch_yf_batch(days)
    for nm, s in yf_data.items():
        data[nm]   = s
        status[nm] = "ok"
    for nm in ALL_YFINANCE:
        if nm not in status:
            status[nm] = "failed"

    # FRED 基础序列
    fred_data = fetch_fred_all(days)
    for nm, s in fred_data.items():
        data[nm]   = s
        status[nm] = "ok"

    # 美联储净流动性
    walcl = fetch_fred_one("WALCL",     days)
    tga   = fetch_fred_one("WTREGEN",   days)
    rrp   = fetch_fred_one("RRPONTSYD", days)
    if not walcl.empty:
        tmp = pd.concat([walcl, tga, rrp], axis=1, join="outer")
        tmp.columns = ["WALCL", "TGA", "RRP"]
        tmp = tmp.interpolate(method="linear", limit_direction="both").ffill().bfill()
        net = (tmp["WALCL"] - tmp["TGA"]) / 1000 - tmp["RRP"]
        net.name = "美联储净流动性"
        data["美联储净流动性"]   = net.dropna()
        status["美联储净流动性"] = "ok"

    # akshare 中国数据
    for nm, s in [
        ("中国10Y国债", fetch_cn_bond(days)),
        ("恒生指数",    fetch_hsi(days)),
    ]:
        if not s.empty:
            data[nm]   = s
            status[nm] = "ok"
        else:
            status[nm] = "failed"

    csi_price, csi_pe = fetch_csi300(days)
    if not csi_price.empty:
        data["沪深300"]   = csi_price
        status["沪深300"] = "ok"
    if not csi_pe.empty:
        data["沪深300_PE"]   = csi_pe
        status["沪深300_PE"] = "ok"

    for nm, s in fetch_cn_macro(days).items():
        data[nm]   = s
        status[nm] = "ok"

    # 中国A股主要指数
    for nm, s in fetch_cn_indices(days).items():
        data[nm]   = s
        status[nm] = "ok"

    # 中国扩展宏观数据（PPI、财新PMI、M2同比）
    for nm, s in fetch_cn_macro_extended(days).items():
        data[nm]   = s
        status[nm] = "ok"

    # 中美利差（美国10Y − 中国10Y，日频对齐）
    _us10 = data.get("10Y美债")
    _cn10 = data.get("中国10Y国债")
    if _us10 is not None and _cn10 is not None:
        _idx = _us10.index.intersection(_cn10.index)
        if len(_idx) > 20:
            _sp = _us10.loc[_idx] - _cn10.loc[_idx]
            _sp.name = "中美利差(10Y)"
            data["中美利差(10Y)"]   = _sp.dropna()
            status["中美利差(10Y)"] = "ok"

    # 铜金比率（全球经济健康信号：上升=风险偏好/增长预期强；下降=避险/衰退担忧）
    _cu = data.get("铜")
    _au = data.get("黄金")
    if _cu is not None and _au is not None:
        _idx_ca = _cu.index.intersection(_au.index)
        if len(_idx_ca) > 20:
            _ca = (_cu.loc[_idx_ca] / _au.loc[_idx_ca] * 1000).dropna()
            _ca.name = "铜金比率"
            data["铜金比率"]   = _ca
            status["铜金比率"] = "ok"

    # Sahm规则指标（月频失业率衍生，≥0.5pp自动触发衰退信号）
    _ur = data.get("美国失业率")
    if _ur is not None:
        _ur_clean = _ur.dropna()
        if len(_ur_clean) >= 14:
            _u3m   = _ur_clean.rolling(3).mean()
            _u12mn = _ur_clean.rolling(12).min()
            _sahm  = (_u3m - _u12mn).dropna()
            _sahm.name = "Sahm规则指标"
            data["Sahm规则指标"]   = _sahm
            status["Sahm规则指标"] = "ok"

    if not data:
        return pd.DataFrame(), status

    wide = pd.concat(list(data.values()), axis=1, join="outer")
    wide.columns = list(data.keys())
    wide.index = pd.to_datetime(wide.index)
    wide.sort_index(inplace=True)
    wide = wide.interpolate(method="linear", limit_direction="both").ffill().bfill()
    return wide, status


# ═══════════════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════════════
def hex_to_rgba(hex_color: str, alpha: float = 0.08) -> str:
    """Convert #rrggbb to rgba(r,g,b,alpha)"""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def zscore(s: pd.Series) -> pd.Series:
    std = s.std()
    return (s - s.mean()) / std if std > 0 else s * 0

def minmax(s: pd.Series) -> pd.Series:
    mn, mx = s.min(), s.max()
    return (s - mn) / (mx - mn) if mx > mn else s * 0

def safe_val(df, col):
    if col not in df.columns:
        return None
    s = df[col].dropna()
    return float(s.iloc[-1]) if not s.empty else None

def daily_chg(df, col):
    if col not in df.columns:
        return None
    s = df[col].dropna()
    if len(s) < 2:
        return None
    return (s.iloc[-1] / s.iloc[-2] - 1) * 100

def add_bands(fig, s: pd.Series, row=1, col=1):
    mean, std = s.mean(), s.std()
    for n, alpha in [(2, 0.07), (1, 0.14)]:
        fig.add_trace(go.Scatter(
            x=list(s.index) + list(s.index[::-1]),
            y=[mean + n*std]*len(s) + [mean - n*std]*len(s),
            fill="toself",
            fillcolor=f"rgba(59,130,246,{alpha})",
            line=dict(color="rgba(0,0,0,0)"),
            name=f"±{n}σ通道", showlegend=True, hoverinfo="skip",
        ), row=row, col=col)
    fig.add_hline(
        y=mean, line_dash="dash", line_color="#374151", line_width=1,
        annotation_text=f"μ={mean:.2f}",
        annotation_font=dict(color="#475569", size=9),
        row=row, col=col,
    )


# ═══════════════════════════════════════════════════════════════════════════
# 宏观情景诊断引擎
# ═══════════════════════════════════════════════════════════════════════════
def build_macro_regime(df_: pd.DataFrame, V_: dict, spread_102_) -> dict:
    """
    分析宏观指标，返回：
    regime, regime_color, regime_desc, regime_assets,
    signals, watch_list, anomalies
    """
    signals    = {}   # key → (icon, value_str, description)
    watch_list = []   # [(indicator, reason)]

    # ── 通胀 ──
    cpi  = V_.get("美国CPI同比")
    be10 = safe_val(df_, "10Y盈亏平衡通胀")
    if cpi is not None:
        if cpi > 4:
            signals["通胀"] = ("🔴", f"CPI {cpi:.1f}%", "高通胀：远超2%目标，货币政策收紧压力大")
            watch_list.append(("美国CPI同比", f"当前{cpi:.1f}%，远超2%目标，警惕加息预期持续抬升"))
        elif cpi > 2.5:
            signals["通胀"] = ("🟡", f"CPI {cpi:.1f}%", "通胀偏高：高于目标，粘性风险需关注")
            watch_list.append(("美国CPI同比", f"当前{cpi:.1f}%，通胀粘性，关注降息路径"))
        else:
            signals["通胀"] = ("🟢", f"CPI {cpi:.1f}%", "通胀受控：接近或低于2%目标")
    if be10 is not None and be10 > 2.5:
        watch_list.append(("10Y盈亏平衡通胀", f"市场通胀预期{be10:.2f}%，高于美联储目标，警惕脱锚"))

    # ── 就业/增长 ──
    unrate = V_.get("美国失业率")
    if unrate is not None:
        if unrate > 5.5:
            signals["就业"] = ("🔴", f"失业率 {unrate:.1f}%", "就业明显恶化：衰退信号确认")
            watch_list.append(("美国失业率", f"升至{unrate:.1f}%，衰退概率大幅上升"))
        elif unrate > 4.5:
            signals["就业"] = ("🟡", f"失业率 {unrate:.1f}%", "就业放缓：劳动市场降温，关注趋势")
            watch_list.append(("美国失业率", f"{unrate:.1f}%，关注就业趋势是否持续恶化"))
        else:
            signals["就业"] = ("🟢", f"失业率 {unrate:.1f}%", "就业健康：劳动市场依然强劲")

    # ── 收益率曲线 ──
    if spread_102_ is not None:
        if spread_102_ < -0.5:
            signals["收益率曲线"] = ("🔴", f"10Y-2Y={spread_102_:+.2f}%", "深度倒挂：历史预测衰退准确率极高，滞后12-18月")
            watch_list.append(("10Y-2Y利差", f"深度倒挂{spread_102_:+.2f}%，衰退风险极高"))
        elif spread_102_ < 0:
            signals["收益率曲线"] = ("🟡", f"10Y-2Y={spread_102_:+.2f}%", "轻度倒挂：衰退信号，需结合其他指标确认")
            watch_list.append(("10Y-2Y利差", f"倒挂{spread_102_:+.2f}%，保持持续关注"))
        elif spread_102_ < 0.5:
            signals["收益率曲线"] = ("🟡", f"10Y-2Y={spread_102_:+.2f}%", "曲线平坦：期限溢价偏低，市场预期增长放缓")
        else:
            signals["收益率曲线"] = ("🟢", f"10Y-2Y={spread_102_:+.2f}%", "曲线正常：期限溢价健康，经济预期良好")

    # ── 信用风险 ──
    hy = V_.get("美高收益债利差")
    if hy is not None:
        if hy > 600:
            signals["信用风险"] = ("🔴", f"HY={hy:.0f}bps", "信用极度压力：系统性风险高企，危机水平")
            watch_list.append(("美高收益债利差", f"HY利差{hy:.0f}bps，已达信用危机信号"))
        elif hy > 400:
            signals["信用风险"] = ("🟡", f"HY={hy:.0f}bps", "信用利差走阔：风险偏好下降，关注违约率")
            watch_list.append(("美高收益债利差", f"{hy:.0f}bps超400bps警戒线，需持续跟踪"))
        else:
            signals["信用风险"] = ("🟢", f"HY={hy:.0f}bps", "信用市场平稳：违约风险可控")

    # ── 市场波动率 ──
    vix = V_.get("VIX")
    if vix is not None:
        if vix > 35:
            signals["波动率"] = ("🔴", f"VIX={vix:.1f}", "极度恐慌：历史大底往往在此区间出现，短期风险极高")
            watch_list.append(("VIX恐慌指数", f"VIX={vix:.1f}，市场极度恐慌，系统性事件信号"))
        elif vix > 25:
            signals["波动率"] = ("🟡", f"VIX={vix:.1f}", "市场恐慌升温：突破25警戒线，注意风险敞口")
            watch_list.append(("VIX恐慌指数", f"突破25警戒线（当前{vix:.1f}），注意仓位管理"))
        elif vix > 18:
            signals["波动率"] = ("🟡", f"VIX={vix:.1f}", "波动率偏高：市场不确定性上升，注意节奏")
        else:
            signals["波动率"] = ("🟢", f"VIX={vix:.1f}", "低波动：市场情绪平稳，警惕自满情绪")

    # ── 美元 ──
    dxy = V_.get("美元指数")
    if dxy is not None:
        if dxy > 108:
            signals["美元"] = ("🔴", f"DXY={dxy:.1f}", "美元极强：新兴市场面临资本外流和债务压力")
            watch_list.append(("美元指数", f"DXY={dxy:.1f}，强美元压制新兴市场、大宗商品及人民币"))
        elif dxy > 104:
            signals["美元"] = ("🟡", f"DXY={dxy:.1f}", "美元偏强：全球流动性相对收紧")
        else:
            signals["美元"] = ("🟢", f"DXY={dxy:.1f}", "美元中性偏弱：有利于新兴市场和大宗商品")

    # ── 美联储流动性 ──
    if "美联储净流动性" in df_.columns:
        fl_s = df_["美联储净流动性"].dropna()
        if len(fl_s) > 1:
            fl_z = float(zscore(fl_s).iloc[-1])
            fl_v = float(fl_s.iloc[-1])
            if fl_z > 0.5:
                signals["流动性"] = ("🟢", f"{fl_v:,.0f}B$", "流动性宽裕：净流动性偏高，利好风险资产")
            elif fl_z < -0.5:
                signals["流动性"] = ("🔴", f"{fl_v:,.0f}B$", "流动性偏紧：净流动性偏低，压制风险资产")
                watch_list.append(("美联储净流动性", f"Z-Score={fl_z:+.2f}σ，流动性偏紧，关注市场承压"))
            else:
                signals["流动性"] = ("🟡", f"{fl_v:,.0f}B$", "流动性中性：关注后续美联储操作动向")

    # ── 中国经济 ──
    cn_pmi = safe_val(df_, "中国PMI制造业")
    if cn_pmi is None:
        cn_pmi = safe_val(df_, "财新PMI制造业")
    if cn_pmi is not None:
        if cn_pmi < 49:
            signals["中国PMI"] = ("🔴", f"PMI={cn_pmi:.1f}", "中国制造业萎缩：全球需求下行压力，大宗商品承压")
            watch_list.append(("中国PMI制造业", f"PMI={cn_pmi:.1f}，低于荣枯线，关注中国经济走弱的全球传导"))
        elif cn_pmi < 50.5:
            signals["中国PMI"] = ("🟡", f"PMI={cn_pmi:.1f}", "中国制造业接近荣枯线：经济动能偏弱，政策窗口期")
            watch_list.append(("中国PMI制造业", f"PMI={cn_pmi:.1f}，接近荣枯线，关注政策刺激力度"))
        else:
            signals["中国PMI"] = ("🟢", f"PMI={cn_pmi:.1f}", "中国制造业扩张：有利于大宗商品和全球需求")

    # ── 中美利差 ──
    cn_us_sp = safe_val(df_, "中美利差(10Y)")
    if cn_us_sp is not None:
        if cn_us_sp < -1.0:
            signals["中美利差"] = ("🔴", f"中美={cn_us_sp:+.2f}%", "美国相对中国利差大幅为正：资金明显流向美国，人民币承压")
            watch_list.append(("中美利差(10Y)", f"利差{cn_us_sp:+.2f}%，资金流出压力大，关注人民币汇率"))
        elif cn_us_sp < 0:
            signals["中美利差"] = ("🟡", f"中美={cn_us_sp:+.2f}%", "美国利率高于中国：资本流出压力存在")
        else:
            signals["中美利差"] = ("🟢", f"中美={cn_us_sp:+.2f}%", "中国利率高于美国：利差支撑人民币和A股外资流入")

    # ── Sahm 规则 ──
    sahm = safe_val(df_, "Sahm规则指标")
    if sahm is not None:
        if sahm >= 0.5:
            signals["Sahm规则"] = ("🔴", f"Sahm={sahm:.2f}", "已触发衰退：历史准确率接近100%，经济进入或即将进入衰退")
            watch_list.append(("Sahm规则指标", f"Sahm={sahm:.2f}≥0.5触发线，历史上每次衰退均被捕获"))
        elif sahm >= 0.3:
            signals["Sahm规则"] = ("🟡", f"Sahm={sahm:.2f}", "接近触发线：就业市场持续恶化，衰退前期信号增强")
            watch_list.append(("Sahm规则指标", f"Sahm={sahm:.2f}接近0.5触发线，就业趋势值得警惕"))
        else:
            signals["Sahm规则"] = ("🟢", f"Sahm={sahm:.2f}", "未触发：就业市场暂无衰退信号，Sahm < 0.3阈值")

    # ── 金融条件 (NFCI) ──
    nfci = safe_val(df_, "金融条件指数")
    if nfci is not None:
        if nfci > 0.3:
            signals["金融条件"] = ("🔴", f"NFCI={nfci:.3f}", "金融条件大幅收紧：信贷/股票/影子银行系统均承压")
            watch_list.append(("金融条件指数NFCI", f"={nfci:.3f}>0.3，金融条件显著偏紧，历史对应市场压力期"))
        elif nfci > 0:
            signals["金融条件"] = ("🟡", f"NFCI={nfci:.3f}", "金融条件偏紧：高于历史均值（0），信贷环境有压力")
        else:
            signals["金融条件"] = ("🟢", f"NFCI={nfci:.3f}", "金融条件宽松：低于历史均值，有利于信贷扩张")

    # ── 宏观情景四象限判断 ──
    growth_ok   = signals.get("就业",      ("🟢",))[0] == "🟢"
    infla_high  = signals.get("通胀",      ("🟢",))[0] in ("🔴", "🟡")
    be10_high   = be10 > 2.5 if be10 is not None else False

    if growth_ok and not (infla_high or be10_high):
        regime       = "Goldilocks · 金发女孩"
        regime_color = "#22c55e"
        regime_desc  = ("经济增长健康，通胀受控。历史上最有利于风险资产的宏观组合。"
                        "成长股、科技股、信用债均倾向表现良好，建议适度偏多风险资产。")
        regime_assets = {
            "美股":   "🟢 超配（成长/科技）",
            "A股":    "🟢 超配",
            "港股":   "🟢 超配",
            "黄金":   "🟡 中性",
            "大宗商品": "🟡 中性",
            "长期国债": "🟡 中性",
            "现金":   "🔴 低配",
        }
    elif growth_ok and (infla_high or be10_high):
        regime       = "Reflation · 再通胀"
        regime_color = "#f59e0b"
        regime_desc  = ("经济扩张但通胀压力上升。有利于周期性资产、大宗商品和TIPS，"
                        "名义长债承压，成长股相对价值股劣势。关注货币政策转向时点。")
        regime_assets = {
            "美股":   "🟡 中性（偏周期/价值）",
            "A股":    "🟡 关注政策节奏",
            "港股":   "🟡 中性",
            "黄金":   "🟡 中性（TIPS更优）",
            "大宗商品": "🟢 超配（能源/铜）",
            "长期国债": "🔴 低配",
            "现金":   "🟡 中性",
        }
    elif not growth_ok and (infla_high or be10_high):
        regime       = "Stagflation · 滞胀"
        regime_color = "#ef4444"
        regime_desc  = ("经济放缓但通胀高企，是最难应对的宏观环境。黄金、能源类大宗商品和"
                        "短久期债券相对抗跌，股票（尤其成长股）和长债均承压，建议提高防御性。")
        regime_assets = {
            "美股":   "🔴 低配（防御为主）",
            "A股":    "🔴 谨慎",
            "港股":   "🔴 谨慎",
            "黄金":   "🟢 超配",
            "大宗商品": "🟢 超配（能源）",
            "长期国债": "🔴 低配",
            "现金":   "🟢 超配",
        }
    else:
        regime       = "Deflation · 通缩/衰退"
        regime_color = "#3b82f6"
        regime_desc  = ("经济萎缩，通胀下行。长期国债、黄金和防御性股票通常有较好表现，"
                        "高收益债和周期股承压。等待政策宽松信号（降息/QE）再布局风险资产。")
        regime_assets = {
            "美股":   "🟡 防御板块为主",
            "A股":    "🟡 政策刺激预期",
            "港股":   "🟡 谨慎",
            "黄金":   "🟢 超配",
            "大宗商品": "🔴 低配",
            "长期国债": "🟢 超配",
            "现金":   "🟢 超配",
        }

    # ── 异常偏离检测（Z-Score绝对值最大的8个指标）──
    anomalies = []
    for col in df_.columns:
        s = df_[col].dropna()
        if len(s) < 30 or col.endswith("_PE"):
            continue
        zs = float(zscore(s).iloc[-1])
        if abs(zs) > 1.5:
            anomalies.append((col, zs, float(s.iloc[-1])))
    anomalies.sort(key=lambda x: abs(x[1]), reverse=True)
    anomalies = anomalies[:8]

    # ── 综合风险评分（满分15分）──
    risk_score = 0
    for key, thr_r, thr_y in [
        ("通胀",       2, 1), ("就业",    2, 1), ("收益率曲线", 2, 1),
        ("信用风险",   2, 1), ("波动率",  2, 1), ("流动性",    1, 0),
        ("Sahm规则",   2, 1), ("金融条件", 1, 0),
    ]:
        icon = signals.get(key, ("🟢",))[0]
        risk_score += thr_r if icon == "🔴" else (thr_y if icon == "🟡" else 0)

    return {
        "regime":        regime,
        "regime_color":  regime_color,
        "regime_desc":   regime_desc,
        "regime_assets": regime_assets,
        "signals":       signals,
        "watch_list":    watch_list[:10],
        "anomalies":     anomalies,
        "risk_score":    risk_score,
    }


def recession_probability(spread_10y_3m) -> float:
    """
    基于纽约联储 Probit 模型估算未来 12 个月衰退概率 (0–100%)。
    参考: Estrella & Mishkin (1998), NY Fed yield curve research。
    模型：P = Φ(α + β·spread), α=-0.5779, β=-0.8045
    当 10Y-3M < 0（倒挂）时概率明显升高。
    """
    if spread_10y_3m is None:
        return 0.0
    import math
    z = -0.5779 + (-0.8045) * float(spread_10y_3m)
    return float((1.0 + math.erf(z / math.sqrt(2.0))) / 2.0 * 100.0)


# ═══════════════════════════════════════════════════════════════════════════
# 侧边栏
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
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
        list(YFINANCE_VOLATILITY.keys()) +
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
# 5 个主 Tab
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

# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — 风险仪表盘
# ══════════════════════════════════════════════════════════════════════════
with tab1:
    # 取值
    V = {k: safe_val(df, k) for k in [
        "纳斯达克100","标普500","VIX","10Y美债","2Y美债",
        "美元指数","黄金","原油WTI","中国10Y国债","恒生指数",
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

    def kpi(label, val, chg_val=None, unit="", fmt=","):
        if val is None:
            v_html = '<div class="kpi-value kpi-na">N/A</div>'
            c_html = '<div class="kpi-change" style="color:#374151">—</div>'
        else:
            try:
                v_str = f"{val:{fmt}.1f}{unit}"
            except Exception:
                v_str = f"{val:.2f}{unit}"
            v_html = f'<div class="kpi-value">{v_str}</div>'
            if chg_val is not None:
                cls   = "kpi-up" if chg_val >= 0 else "kpi-down"
                arrow = "▲" if chg_val >= 0 else "▼"
                c_html = f'<div class="kpi-change {cls}">{arrow} {abs(chg_val):.2f}%</div>'
            else:
                c_html = '<div class="kpi-change" style="color:#374151">—</div>'
        return (f'<div class="kpi-card">'
                f'<div class="kpi-label">{label}</div>'
                f'{v_html}{c_html}</div>')

    r1 = st.columns(5)
    r1[0].markdown(kpi("纳斯达克100", V["纳斯达克100"], CHG["纳斯达克100"]),        unsafe_allow_html=True)
    r1[1].markdown(kpi("标普500",     V["标普500"],     CHG["标普500"]),            unsafe_allow_html=True)
    r1[2].markdown(kpi("恒生指数",    V["恒生指数"],    CHG["恒生指数"]),           unsafe_allow_html=True)
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


# ══════════════════════════════════════════════════════════════════════════
# TAB 2 — 全球市场
# ══════════════════════════════════════════════════════════════════════════
with tab2:

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


# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — 万能画布
# ══════════════════════════════════════════════════════════════════════════
with tab3:
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


# ══════════════════════════════════════════════════════════════════════════
# TAB 4 — 股债利差 ERP
# ══════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-title">💰 股权风险溢价 (ERP) — 股票相对债券的吸引力</div>',
                unsafe_allow_html=True)
    st.caption("ERP = 盈利收益率 (100/PE) − 10Y国债收益率（%）。ERP↑ → 股票性价比提升")

    etabs = st.tabs(["A股 ERP", "美股 ERP", "实际利率体系", "完整收益率曲线", "🌏 中美利差"])

    # A股 ERP
    with etabs[0]:
        if "沪深300_PE" in df.columns and "中国10Y国债" in df.columns:
            pe_s   = df["沪深300_PE"].dropna()
            bond_s = df["中国10Y国债"].dropna()
            idx    = pe_s.index.intersection(bond_s.index)
            if len(idx) > 20:
                erp_a  = (100 / pe_s.loc[idx]) - bond_s.loc[idx]
                erp_a.name = "A股ERP"
                cl, cr = st.columns([3, 1])
                with cl:
                    fig_ea = go.Figure()
                    fig_ea.add_trace(go.Scatter(
                        x=erp_a.index, y=erp_a.values, name="A股ERP",
                        line=dict(color="#22c55e", width=2),
                        fill="tozeroy", fillcolor="rgba(34,197,94,0.07)",
                        hovertemplate="A股ERP: %{y:.2f}%<extra></extra>",
                    ))
                    add_bands(fig_ea, erp_a)
                    fig_ea.update_layout(**mk_layout(
                        "沪深300 ERP = (100/PE) − 中国10Y国债收益率", h=380))
                    st.plotly_chart(fig_ea, use_container_width=True)
                with cr:
                    cur_erp = float(erp_a.iloc[-1])
                    z_erp   = float(zscore(erp_a).iloc[-1])
                    pct_erp = (erp_a < cur_erp).mean() * 100
                    color_e = "#22c55e" if cur_erp > erp_a.mean() else "#ef4444"
                    lbl_e   = "🟢 高吸引力" if z_erp > 0.5 else ("🔴 低吸引力" if z_erp < -0.5 else "➡️ 中性")
                    st.markdown(f"""
                    <div class="kpi-card" style="padding:20px;margin-top:20px;">
                      <div class="kpi-label">A股 ERP 当前值</div>
                      <div class="kpi-value" style="color:{color_e};">{cur_erp:.2f}%</div>
                      <div class="kpi-label" style="margin-top:10px;">Z-Score</div>
                      <div style="font-size:18px;font-weight:600;color:#f8fafc;">{z_erp:+.2f}σ</div>
                      <div class="kpi-label" style="margin-top:10px;">历史分位数</div>
                      <div style="font-size:16px;font-weight:600;color:#f8fafc;">{pct_erp:.1f}%</div>
                      <div style="font-size:11px;color:#475569;margin-top:8px;">{lbl_e}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("沪深300 PE 与中国国债数据交集不足（需 >20 个公共日期），请刷新数据。")
        else:
            st.warning("缺少沪深300 PE 或中国10Y国债数据，akshare 加载中请稍候。")

    # 美股 ERP
    with etabs[1]:
        tnx_cur = safe_val(df, "10Y美债")
        sp_pe   = None
        try:
            import yfinance as yf
            info = yf.Ticker("^GSPC").info
            sp_pe = info.get("trailingPE") or info.get("forwardPE")
        except Exception:
            pass

        if sp_pe and tnx_cur:
            ey   = 100 / sp_pe
            erp  = ey - tnx_cur
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("标普500 当前PE", f"{sp_pe:.1f}×")
            c2.metric("盈利收益率 (EY)", f"{ey:.2f}%")
            c3.metric("10Y美债收益率",   f"{tnx_cur:.2f}%")
            c4.metric("美股实时 ERP",    f"{erp:.2f}%",
                      delta=f"{'高于' if erp>0 else '低于'}无风险利率")
            st.caption(
                "注：美股 PE 历史序列需要 Shiller CAPE 数据（FRED series: MKTGDP 或 Quandl MULTPL）。"
                "当前展示实时 PE 估算值；如需历史 ERP 曲线，可接入 Shiller CAPE Excel 文件。"
            )
        else:
            st.info("标普500 PE 或10Y美债数据暂不可用，请稍后刷新。")

    # 实际利率体系
    with etabs[2]:
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
    with etabs[3]:
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
    with etabs[4]:
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


# ══════════════════════════════════════════════════════════════════════════
# TAB 5 — 深度分析
# ══════════════════════════════════════════════════════════════════════════
with tab5:
    sub1, sub2, sub3 = st.tabs(["🔗 相关性矩阵","📉 宏观经济","📊 滚动统计"])

    # ── 相关性矩阵 ──────────────────────────────────────────────────────
    with sub1:
        st.markdown('<div class="section-title">🔗 宏观指标相关性热力图</div>',
                    unsafe_allow_html=True)
        heat_cols = [
            c for c in df.columns
            if not c.endswith("_PE")
            and df[c].dropna().shape[0] > 60
        ]
        if len(heat_cols) < 3:
            st.warning("有效序列不足，请刷新后重试。")
        else:
            df_ret  = df[heat_cols].pct_change().dropna(how="all")
            # ── 关键修复：过滤月度/低频FRED序列 ──────────────────────
            # 月度数据（CPI、PMI、M2等）在日度DataFrame中密度仅约4-5%，
            # 与日频数据混算会导致相关性严重失真（样本量不匹配）。
            # 通过密度筛选确保只有日/周频数据参与相关性计算。
            ret_density   = df_ret.notna().mean()
            high_freq_cols = ret_density[ret_density > 0.10].index.tolist()
            df_ret  = df_ret[high_freq_cols]
            df_ret  = df_ret.dropna(axis=1, thresh=int(len(df_ret) * 0.4))
            heat_cols = list(df_ret.columns)
            corr    = df_ret.corr(method="pearson")
            # 截断过长标签
            labels  = [c[:9] if len(c) > 9 else c for c in corr.columns]

            fig_hm = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=labels, y=labels,
                colorscale=[
                    [0.0, "#0c2d6b"],[0.35, "#1d4ed8"],
                    [0.5,  "#0d1321"],
                    [0.65, "#9f1239"],[1.0, "#dc2626"],
                ],
                zmin=-1, zmax=1,
                text=np.round(corr.values, 2),
                texttemplate="%{text}",
                textfont=dict(size=9, color="#d1d5db"),
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
                height=560,
                margin=dict(l=80, r=60, t=44, b=80),
                title=dict(
                    text=f"宏观指标日收益率相关性  |  {period_label}",
                    font=dict(color="#94a3b8", size=13), x=0, xanchor="left",
                ),
                xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
                yaxis=dict(tickfont=dict(size=10)),
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


# ══════════════════════════════════════════════════════════════════════════
# TAB 6 — 综合诊断
# ══════════════════════════════════════════════════════════════════════════
with tab6:
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

    _col_r1, _col_r2, _col_r3 = st.columns([2, 1, 3])
    with _col_r1:
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,#0d1321,{_reg_col}18);
                    border:1px solid {_reg_col}55;border-radius:12px;padding:24px;">
          <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1px;font-weight:600;">当前宏观情景</div>
          <div style="font-size:22px;font-weight:700;color:{_reg_col};margin:10px 0 8px;">{mc['regime']}</div>
          <div style="font-size:12px;color:#94a3b8;line-height:1.7;">{mc['regime_desc']}</div>
        </div>
        """, unsafe_allow_html=True)
    with _col_r2:
        st.markdown(f"""
        <div style="background:#0d1321;border:1px solid {_rs_color}55;border-radius:12px;
                    padding:24px;text-align:center;height:100%;">
          <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1px;font-weight:600;">综合风险评分</div>
          <div style="font-size:42px;font-weight:800;color:{_rs_color};margin:8px 0;">{_rs}</div>
          <div style="font-size:13px;color:{_rs_color};font-weight:600;">/ 15 · {_rs_label}</div>
          <div style="font-size:10px;color:#475569;margin-top:8px;line-height:1.5;">
            通胀/就业/Sahm/曲线<br>信用/波动率/流动性/NFCI
          </div>
        </div>
        """, unsafe_allow_html=True)
    with _col_r3:
        st.markdown("**各类资产配置参考信号**")
        _asset_rows = []
        for _asset, _sig in mc["regime_assets"].items():
            _ac = ("#22c55e" if "超配" in _sig else
                   "#ef4444" if any(x in _sig for x in ["低配","谨慎"]) else
                   "#f59e0b")
            _asset_rows.append({"资产类别": _asset, "配置信号": _sig, "颜色参考": _ac})
        _df_a = pd.DataFrame(_asset_rows)[["资产类别","配置信号"]]
        st.dataframe(_df_a, use_container_width=True, hide_index=True)

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



# ══════════════════════════════════════════════════════════════════════════
# TAB 7 — 早期预警雷达
# ══════════════════════════════════════════════════════════════════════════
with tab7:
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

        # VVIX & SKEW
        _vv_avail = [c for c in ["VVIX", "SKEW指数"] if c in df.columns]
        if _vv_avail:
            st.markdown('<div class="section-title">🎲 波动率市场结构 (VVIX / SKEW 指数)</div>',
                        unsafe_allow_html=True)
            _fig_vv = go.Figure()
            for _i, _cnm in enumerate(_vv_avail):
                _sv = df[_cnm].dropna()
                if _sv.empty:
                    continue
                _fig_vv.add_trace(go.Scatter(
                    x=_sv.index, y=zscore(_sv).values,
                    name=_cnm, line=dict(color=COLORS[_i], width=1.8),
                ))
            _fig_vv.add_hline(y=0, line_color="#374151", line_width=1)
            for _lv, _lc in [(2, "#ef4444"), (1, "#f59e0b"), (-1, "#f59e0b"), (-2, "#ef4444")]:
                _fig_vv.add_hline(y=_lv, line_dash="dash", line_color=_lc, line_width=0.7)
            _fig_vv.update_layout(**mk_layout(
                "VVIX（VIX的波动率）& SKEW指数 — Z-Score 标准化", h=300))
            st.plotly_chart(_fig_vv, use_container_width=True)
            st.caption(
                "• **VVIX↑** → VIX本身的波动加剧，市场对短期尾部风险定价的不确定性上升，"
                "历史上往往出现在市场转折前\n"
                "• **SKEW↑** → 市场购买更多下行保险（OTM Put），隐含尾部事件预期上升；"
                "SKEW > 140 通常预警黑天鹅事件担忧"
            )

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
        _comm_sel = [c for c in ["布伦特原油", "原油WTI", "铜", "黄金", "小麦", "玉米", "白银"]
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
                "• **小麦/玉米↑** → 粮食通胀压力上升，对新兴市场影响尤大\n"
                "• **布伦特/WTI↑** → 输入型通胀，压缩企业利润率，打压消费信心\n"
                "• **铜与原油同向上涨** → 需求驱动的大宗商品牛市，经济扩张信号"
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
