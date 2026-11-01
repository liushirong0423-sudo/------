"""全局配置：FRED 序列、行情品种清单、时间周期与配色常量"""
import os

import streamlit as st

_DEFAULT_FRED_KEY = "8923281d30974da13834d8350c0d9669"


def _resolve_fred_key() -> str:
    """按 环境变量 → Streamlit secrets → 内置默认值 的顺序取 FRED Key。
    云端（魔搭创空间）没有 secrets.toml 时，st.secrets 会抛异常，必须兜底。"""
    if os.getenv("FRED_API_KEY"):
        return os.environ["FRED_API_KEY"]
    try:
        return st.secrets.get("FRED_API_KEY", _DEFAULT_FRED_KEY)
    except Exception:
        return _DEFAULT_FRED_KEY


FRED_API_KEY = _resolve_fred_key()

YFINANCE_EQUITY = {
    "纳斯达克100": "^NDX",
    "标普500":    "^GSPC",
    "道琼斯":     "^DJI",
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
    "美国CPI同比":     "CPIAUCSL",     # 指数 → 同比% 由 _to_yoy 转换
    "核心PCE同比":     "PCEPILFE",     # 指数 → 同比% 由 _to_yoy 转换
    "10Y盈亏平衡通胀": "T10YIE",
    "5Y5Y远期通胀":    "T5YIFR",
    "TIPS_10Y实际利率": "DFII10",
    "美国失业率":      "UNRATE",
    "美高收益债利差":  "BAMLH0A0HYM2",
    "美投资级债利差":  "BAMLC0A0CM",
    "M1货币供应":      "M1SL",
    "M2货币供应":      "M2SL",
    "密歇根消费信心":  "UMCSENT",
    "联邦基金利率":    "FEDFUNDS",
    # ── 高频领先指标 ──
    "初申请失业金人数": "ICSA",       # 周频，最高频就业先行指标
    "金融条件指数":    "NFCI",        # 芝加哥联储，周频
    "金融压力指数":    "STLFSI4",     # 圣路易斯联储，周频
    "10Y-2Y利差":     "T10Y2Y",      # 日频，收益率曲线斜率
    "10Y-3M利差":     "T10Y3M",      # 日频，NY Fed衰退概率模型核心变量
    "工业生产指数":    "INDPRO",      # 月频，经济周期同步指标
    "建筑许可":        "PERMIT",      # 月频，房地产周期领先6-12月
}

# 需要从指数水平转换为同比%的 FRED 序列
FRED_YOY_SERIES = {"美国CPI同比", "核心PCE同比"}

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
