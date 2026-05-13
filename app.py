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
    "黄金":   "GC=F",
    "原油WTI": "CL=F",
    "铜":     "HG=F",
    "白银":   "SI=F",
    "天然气": "NG=F",
}
YFINANCE_CRYPTO = {
    "比特币": "BTC-USD",
}

ALL_YFINANCE = {
    **YFINANCE_EQUITY, **YFINANCE_RATES, **YFINANCE_RISK,
    **YFINANCE_FX, **YFINANCE_COMMODITY, **YFINANCE_CRYPTO,
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
# 侧边栏
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding:8px 0 4px;'>
        <div style='font-size:15px;font-weight:700;color:#f8fafc;'>⚙ 控制面板</div>
        <div style='font-size:11px;color:#475569;margin-top:2px;'>全维度宏观监控平台 v2.0</div>
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
        ["中国10Y国债","沪深300","恒生指数","美联储净流动性",
         "美国CPI同比","美高收益债利差","TIPS_10Y实际利率","M2货币供应"]
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
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 风险仪表盘",
    "🌍 全球市场",
    "🔬 万能画布",
    "💰 股债利差 ERP",
    "🔗 深度分析",
])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — 风险仪表盘
# ══════════════════════════════════════════════════════════════════════════
with tab1:
    # 取值
    V = {k: safe_val(df, k) for k in [
        "纳斯达克100","标普500","VIX","10Y美债","2Y美债",
        "美元指数","黄金","原油WTI","中国10Y国债","恒生指数",
        "沪深300","美联储净流动性","美高收益债利差",
        "TIPS_10Y实际利率","美国CPI同比","美国失业率",
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
    eq_cols = [c for c in list(YFINANCE_EQUITY.keys()) + ["沪深300","恒生指数"]
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

    etabs = st.tabs(["A股 ERP", "美股 ERP", "实际利率体系", "完整收益率曲线"])

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
            df_ret  = df_ret.dropna(axis=1, thresh=int(len(df_ret) * 0.4))
            heat_cols = list(df_ret.columns)
            corr    = df_ret.corr()
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
        cn_m_cols = [c for c in ["中国CPI同比","中国PMI制造业"] if c in df.columns]
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

# ═══════════════════════════════════════════════════════════════════════════
# Footer — 数据源状态
# ═══════════════════════════════════════════════════════════════════════════
with st.expander("📡 数据源状态一览", expanded=False):
    ok_rows   = [{"指标": k, "状态": "✅ 正常"} for k, v in st_meta.items() if v == "ok"]
    fail_rows = [{"指标": k, "状态": "❌ 失败"} for k, v in st_meta.items() if v != "ok"]
    mc1, mc2  = st.columns(2)
    mc1.markdown(f"**✅ 正常 ({len(ok_rows)})**")
    mc1.dataframe(pd.DataFrame(ok_rows), hide_index=True, use_container_width=True)
    if fail_rows:
        mc2.markdown(f"**❌ 失败 ({len(fail_rows)})**")
        mc2.dataframe(pd.DataFrame(fail_rows), hide_index=True, use_container_width=True)

st.markdown("""
<div style='text-align:center;padding:16px 0 6px;font-size:11px;color:#1f2937;'>
  宏观风险监控平台 v2.0 &nbsp;·&nbsp;
  数据来源：yfinance · akshare · FRED &nbsp;·&nbsp;
  仅供研究参考，不构成任何投资建议
</div>
""", unsafe_allow_html=True)
