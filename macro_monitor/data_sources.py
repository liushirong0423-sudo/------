"""数据获取层：yfinance（海外行情）/ FRED（美国宏观）/ akshare（中国数据）"""
import json
import re
import time
from datetime import datetime, timedelta

import pandas as pd
import requests
import streamlit as st

from .config import ALL_YFINANCE, FRED_API_KEY, FRED_SERIES

def fetch_yf_batch(days: int) -> dict:
    """批量拉取 yfinance 数据；被 Yahoo 限流返回空表时交由降级数据源处理"""
    try:
        import yfinance as yf
    except ImportError:
        return {}

    end   = datetime.today()
    start = end - timedelta(days=days + 10)
    result = {}

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
        # ── 方法1: index_value_name_fundation（中证指数官网）──
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
        # ── 方法2: stock_zh_index_value_csindex（中证官方接口）──
        if pe.empty:
            try:
                pe_df2 = ak.stock_zh_index_value_csindex(symbol="000300")
                if pe_df2 is not None and not pe_df2.empty:
                    date_col = pe_df2.columns[0]
                    pe_df2.index = pd.to_datetime(pe_df2[date_col])
                    pe_col2 = next(
                        (c for c in pe_df2.columns if "pe" in c.lower() or "市盈" in c), None
                    )
                    if pe_col2:
                        pe = pd.to_numeric(pe_df2[pe_col2], errors="coerce").dropna()
                        pe.name = "沪深300_PE"
                        pe = pe[pe.index >= cutoff]
            except Exception:
                pass
        # ── 方法3: index_analysis_cons_em（东方财富接口）──
        if pe.empty:
            try:
                pe_df3 = ak.index_analysis_cons_em(symbol="沪深300", indicator="市盈率")
                if pe_df3 is not None and not pe_df3.empty:
                    date_col3 = pe_df3.columns[0]
                    pe_df3.index = pd.to_datetime(pe_df3[date_col3])
                    val_col3 = pe_df3.columns[-1]
                    pe = pd.to_numeric(pe_df3[val_col3], errors="coerce").dropna()
                    pe.name = "沪深300_PE"
                    pe = pe[pe.index >= cutoff]
            except Exception:
                pass
        return price, pe
    except Exception:
        return pd.Series(dtype=float), pd.Series(dtype=float)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_hsi(days: int) -> pd.Series:
    cutoff = pd.Timestamp(datetime.today() - timedelta(days=days + 10))
    # ── 优先使用 yfinance ^HSI（稳定可靠）──
    try:
        import yfinance as yf
        raw = yf.download("^HSI", period="6y", progress=False, auto_adjust=True)
        if raw is not None and not raw.empty:
            s = raw["Close"].squeeze().dropna()
            s.index = pd.to_datetime(s.index).tz_localize(None)
            s.name = "恒生指数"
            return s[s.index >= cutoff]
    except Exception:
        pass
    # ── akshare / 新浪备用 ──
    try:
        import akshare as ak
        df = ak.stock_hk_index_daily_sina(symbol="HSI")
        s = _sina_series(df, days)
        s.name = "恒生指数"
        if not s.empty:
            return s
    except Exception:
        pass
    # ── 东方财富备用 ──
    try:
        import akshare as ak
        df = ak.stock_hk_index_daily_em(symbol="恒生指数")
        df.index = pd.to_datetime(df["date"])
        s = pd.to_numeric(df["close"], errors="coerce").dropna()
        s.name = "恒生指数"
        return s[s.index >= cutoff]
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


# ─── 降级数据源：yfinance 被 Yahoo 限流时改用新浪 / 东方财富 / FRED ─────────
SINA_US_INDEX = {"纳斯达克100": ".NDX", "标普500": ".INX", "道琼斯": ".DJI"}

SINA_GLOBAL_INDEX = {
    "日经225": "日经225指数",
    "德国DAX": "德国DAX 30种股价指数",
    "英国富时100": "英国富时100指数",
}

SINA_FUTURES = {"黄金": "GC", "白银": "SI", "铜": "HG", "原油WTI": "CL"}

SINA_US_ETF = {"MSCI新兴市场": "EEM"}

# 美元指数按 ICE 权重由 FRED 六种汇率合成（NYB/DXY 同为货币篮子口径）
FRED_DXY_COMPONENTS = ["DEXUSEU", "DEXJPUS", "DEXUSUK",
                       "DEXCAUS", "DEXSZUS", "DEXSDUS"]

EM_SECID = {
    "纳斯达克100": "100.NDX",   "标普500": "100.SPX",    "道琼斯": "100.DJIA",
    "日经225":    "100.N225",   "德国DAX": "100.GDAXI", "英国富时100": "100.FTSE",
    "恒生指数":   "100.HSI",    "美元指数": "100.UDI",
    "黄金":       "101.GC00Y",  "铜": "101.HG00Y",      "白银": "101.SI00Y",
    "原油WTI":    "102.CL00Y",  "天然气": "102.NG00Y",
    "小麦":       "103.ZW00Y",  "玉米": "103.ZC00Y",    "美元/人民币": "133.USDCNH",
}

FRED_FALLBACK = {
    "2Y美债": "DGS2", "5Y美债": "DGS5", "10Y美债": "DGS10", "30Y美债": "DGS30",
    "VIX": "VIXCLS", "欧元/美元": "DEXUSEU", "美元/日元": "DEXJPUS",
    "美元/人民币": "DEXCHUS", "比特币": "CBBTCUSD", "布伦特原油": "DCOILBRENTEU",
    "天然气": "DHHNGSP", "原油WTI": "DCOILWTICO",
}


def _sina_series(df: pd.DataFrame, days: int) -> pd.Series:
    """把新浪返回的 date/close 表转成按日索引的收盘序列"""
    s = pd.Series(pd.to_numeric(df["close"], errors="coerce").values,
                  index=pd.to_datetime(df["date"]))
    cutoff = pd.Timestamp(datetime.today() - timedelta(days=days + 10))
    return s[s.index >= cutoff].dropna()


def fetch_sina_one(name: str, days: int) -> pd.Series:
    """新浪行情（akshare 封装）：美股指数 / 环球指数 / 港股指数 / 外盘期货"""
    try:
        import akshare as ak
        if name in SINA_US_INDEX:
            return _sina_series(ak.index_us_stock_sina(symbol=SINA_US_INDEX[name]), days)
        if name in SINA_GLOBAL_INDEX:
            return _sina_series(ak.index_global_hist_sina(symbol=SINA_GLOBAL_INDEX[name]), days)
        if name == "恒生指数":
            return _sina_series(ak.stock_hk_index_daily_sina(symbol="HSI"), days)
        if name in SINA_US_ETF:
            return _sina_series(ak.stock_us_daily(symbol=SINA_US_ETF[name]), days)
        if name in SINA_FUTURES:
            text = requests.get(
                "https://stock.finance.sina.com.cn/futures/api/jsonp.php/var%20_=/"
                "GlobalFuturesService.getGlobalFuturesDailyKLine",
                params={"symbol": SINA_FUTURES[name]}, timeout=15,
                headers={"User-Agent": "Mozilla/5.0",
                         "Referer": "https://finance.sina.com.cn/"},
            ).text
            arr = json.loads(re.search(r"=\((\[.*\])\)", text, re.S).group(1))
            return _sina_series(pd.DataFrame(arr), days)
    except Exception:
        pass
    return pd.Series(dtype=float)


def fetch_sina_fallback(names, days: int) -> dict:
    """对 yfinance 缺失的品种逐个走新浪"""
    out = {}
    for nm in names:
        s = fetch_sina_one(nm, days)
        if not s.empty:
            s.name = nm
            out[nm] = s
    return out


def fetch_dxy_from_fred(days: int) -> pd.Series:
    """用 FRED 汇率按 ICE 权重合成美元指数 DXY"""
    comps = {}
    for sid in FRED_DXY_COMPONENTS:
        s = fetch_fred_one(sid, days)
        if not s.empty:
            comps[sid] = s
    if len(comps) < len(FRED_DXY_COMPONENTS):
        return pd.Series(dtype=float)
    d = pd.concat(comps, axis=1, join="inner").dropna()
    dxy = (50.14348112
           * d["DEXUSEU"] ** -0.576 * d["DEXJPUS"] ** 0.136
           * d["DEXUSUK"] ** -0.119 * d["DEXCAUS"] ** 0.091
           * d["DEXSZUS"] ** 0.042 * d["DEXSDUS"] ** 0.036)
    dxy.name = "美元指数"
    return dxy


def fetch_em_one(secid: str, days: int) -> pd.Series:
    """东方财富日线收盘价（全球指数 / 商品 / 外汇）"""
    try:
        r = requests.get(
            "https://push2his.eastmoney.com/api/qt/stock/kline/get",
            params={
                "secid": secid, "fields1": "f1,f2", "fields2": "f51,f53",
                "klt": "101", "fqt": "1", "end": "20500101",
                "lmt": str(max(days + 40, 300)),
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Referer": "https://quote.eastmoney.com/",
            },
            timeout=15,
        )
        klines = r.json()["data"]["klines"]
    except Exception:
        return pd.Series(dtype=float)
    rows = [ln.split(",") for ln in klines if ln and "," in ln]
    rows = [(d, v) for d, v in rows if v not in ("-", "")]
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series([float(v) for _, v in rows],
                  index=pd.to_datetime([d for d, _ in rows]))
    return s.sort_index().dropna()


def fetch_em_fallback(names, days: int) -> dict:
    """对 yfinance 缺失的品种逐个走东方财富（限速 0.3s/次）"""
    out = {}
    for nm in names:
        secid = EM_SECID.get(nm)
        if not secid:
            continue
        s = fetch_em_one(secid, days)
        if not s.empty:
            s.name = nm
            out[nm] = s
        time.sleep(0.3)
    return out


def fetch_fred_fallback(names, days: int) -> dict:
    """东方财富也拿不到时，用 FRED 日频序列兜底"""
    out = {}
    for nm in names:
        sid = FRED_FALLBACK.get(nm)
        if not sid:
            continue
        s = fetch_fred_one(sid, days)
        if not s.empty:
            s.name = nm
            out[nm] = s
    return out


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

    # yfinance 被限流时的降级：新浪 → 东方财富 → FRED 日频序列
    _missing = [nm for nm in ALL_YFINANCE if status.get(nm) != "ok"]
    if _missing:
        for nm, s in fetch_sina_fallback(_missing, days).items():
            data[nm]   = s
            status[nm] = "ok"
        _missing = [nm for nm in ALL_YFINANCE if status.get(nm) != "ok"]
        for nm, s in fetch_em_fallback(_missing, days).items():
            data[nm]   = s
            status[nm] = "ok"
        _missing = [nm for nm in ALL_YFINANCE if status.get(nm) != "ok"]
        for nm, s in fetch_fred_fallback(_missing, days).items():
            data[nm]   = s
            status[nm] = "ok"
        if status.get("美元指数") != "ok":
            s = fetch_dxy_from_fred(days)
            if not s.empty:
                data["美元指数"]   = s
                status["美元指数"] = "ok"

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
