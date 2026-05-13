# 📡 全维度宏观风险监控平台 v2.0

基于 **Python + Streamlit** 构建的零成本全维度宏观风险监控工具，采用 Bloomberg 深色终端风格 UI，实时聚合美股、港股、A 股、大宗商品、利率及 FRED 宏观经济数据。

---

## 功能概览

| 模块 | 内容 |
|------|------|
| 🎯 风险仪表盘 | 三级警报系统（VIX / 利差倒挂 / 美元 / 信用利差）、核心 KPI 卡片、美联储净流动性（WALCL−TGA−RRP） |
| 🌍 全球市场 | 全球股指基准化对比、大宗商品（黄金/原油/铜/白银/天然气）、比特币、黄金 vs TIPS 实际利率、外汇 Z-Score |
| 🔬 万能画布 | 任意指标多选叠加，支持 Z-Score / Min-Max / 原始值三种归一化模式，附历史分位统计摘要 |
| 💰 股债 ERP | A 股沪深300 ERP、美股 ERP 实时估算、TIPS 实际利率 & 盈亏平衡通胀体系、完整收益率曲线形状 |
| 🔗 深度分析 | 宏观指标相关性热力图、美国 & 中国宏观经济数据、滚动波动率 & Z-Score 统计 |

---

## 数据来源

- **yfinance** — 美股指数、利率、外汇、大宗商品、加密货币
- **FRED**（圣路易斯联储）— 美联储资产负债表、通胀、失业率、信用利差、M2 等
- **akshare** — 沪深300、恒生指数、中国国债、中国 CPI / PMI

---

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 FRED API Key（见下方 Secrets 说明）

# 3. 启动应用
streamlit run app.py
```

浏览器访问：http://localhost:8501

---

## 🔑 API Key 配置（Streamlit Secrets）

本项目使用 FRED API（免费注册：https://fred.stlouisfed.org/docs/api/api_key.html）。

**本地运行**，在项目根目录创建 `.streamlit/secrets.toml`：

```toml
# .streamlit/secrets.toml
FRED_API_KEY = "你的FRED_API_KEY"
```

**云端部署**（Streamlit Community Cloud），在项目 Settings → Secrets 中填写：

```toml
FRED_API_KEY = "你的FRED_API_KEY"
```

> ⚠️ 请勿将 `secrets.toml` 提交到 Git 仓库。已在 `.gitignore` 中排除。

---

## 目录结构

```
宏观指标监控/
├── app.py                  # 主应用
├── requirements.txt        # Python 依赖
├── README.md               # 本文件
└── .streamlit/
    └── secrets.toml        # API Key（本地，不提交 Git）
```

---

## 免责声明

本工具仅供学习与研究参考，不构成任何投资建议。市场数据存在延迟，请以官方渠道为准。
