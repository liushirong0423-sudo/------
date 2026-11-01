---
title: 全维度宏观风险监控平台
emoji: 📡
colorFrom: blue
colorTo: indigo
sdk: streamlit
app_file: app.py
pinned: false
license: apache-2.0
---

# 📡 全维度宏观风险监控平台 v4.0

基于 **Python + Streamlit** 构建的零成本全维度宏观风险监控工具，采用 Bloomberg 深色终端风格 UI，实时聚合美股、港股、A 股、大宗商品、利率及 FRED 宏观经济数据。

代码按职责拆分到 `macro_monitor/` 包，`app.py` 仅作为应用入口。

---

## 功能概览（8 个标签页）

| 模块 | 内容 |
|------|------|
| 🧭 整体研判 | 当前经济环境、资产估值状态、适合投资的资产及理由、一句话结论 |
| 🎯 风险仪表盘 | 三级警报系统（VIX / 利差倒挂 / 美元 / 信用利差）、核心 KPI 卡片、美联储净流动性（WALCL−TGA−RRP） |
| 🌍 全球市场 | 全球股指基准化对比、大宗商品（黄金/原油/铜/白银/天然气）、比特币、黄金 vs TIPS 实际利率、外汇 Z-Score |
| 🔬 万能画布 | 任意指标多选叠加，支持 Z-Score / Min-Max / 原始值三种归一化模式，附历史分位统计摘要 |
| 💰 股债利差 ERP | A 股沪深300 ERP、美股 ERP 实时估算、TIPS 实际利率 & 盈亏平衡通胀体系、完整收益率曲线形状 |
| 🔗 深度分析 | 宏观指标相关性热力图、美国 & 中国宏观经济数据、滚动波动率 & Z-Score 统计 |
| 🧠 综合诊断 | 宏观情景打分、跨市场联动的综合诊断结论 |
| 🔮 早期预警雷达 | 衰退概率仪表、金融压力监测、大宗商品信号、衰退前瞻预判体系 |

---

## 数据来源与降级链

行情数据按优先级自动降级，任一来源受限时自动切换，页面底部「📡 数据源状态一览」可查看每个指标的实际来源状态：

1. **yfinance** — 美股指数、利率、外汇、大宗商品、加密货币（首选）
2. **akshare / 新浪财经** — 美股指数、全球指数、港股、期货备用源
3. **东方财富** — 行情备用源
4. **FRED 日频序列** — 利率、汇率、原油等最终兜底；美元指数由 FRED 六种汇率按 ICE 权重合成
5. **FRED** — 美联储资产负债表、通胀、失业率、信用利差、M2、金融条件指数等
6. **akshare** — 沪深300（含 PE）、恒生指数、中国国债、中国 CPI / PPI / PMI

---

## 目录结构

```
宏观指标监控/
├── app.py                       # 应用入口：页面配置 → 侧边栏 → 数据加载 → 7 个 Tab
├── macro_monitor/
│   ├── config.py                # 配置常量（FRED 序列、行情品种、周期、配色）
│   ├── theme.py                 # Bloomberg 深色主题 CSS
│   ├── data_sources.py          # yfinance / akshare / 东方财富 / FRED 抓取与降级
│   ├── analytics.py             # 归一化、统计、宏观情景诊断、衰退概率
│   ├── charts.py                # Plotly 布局工厂
│   ├── components.py            # KPI 等 HTML 卡片组件
│   ├── sidebar.py               # 侧边栏控制面板
│   └── views/                   # 7 个标签页的渲染逻辑
│       ├── dashboard.py         # 风险仪表盘
│       ├── markets.py           # 全球市场
│       ├── canvas.py            # 万能画布
│       ├── erp.py               # 股债利差 ERP
│       ├── deep_analysis.py     # 深度分析
│       ├── diagnosis.py         # 综合诊断
│       └── early_warning.py     # 早期预警雷达
├── requirements.txt             # Python 依赖
├── README.md                    # 本文件
└── .streamlit/
    └── secrets.toml             # API Key（本地，不提交 Git）
```

---

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 FRED API Key（见下方 Secrets 说明，可选）

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

**云端部署**（魔搭创空间），在「环境变量」中填写（可选，代码已带默认值）：

```toml
FRED_API_KEY = "你的FRED_API_KEY"
```

> ⚠️ 请勿将 `secrets.toml` 提交到 Git 仓库。已在 `.gitignore` 中排除。

---

## ☁️ 部署到魔搭创空间（ModelScope Studio）

国内可直连、免费、无需 GitHub。代码托管在 Gitee，运行在魔搭创空间。

- 仓库根目录的 `ms_deploy.json` 声明了 `sdk_type: streamlit`、`base_image` 与 `resource_configuration`；
- `README.md` 顶部 YAML 声明了 `sdk: streamlit`、`app_file: app.py`；
- `.streamlit/config.toml` 已把服务端口固定为 `0.0.0.0:7860`（平台要求的端口）。

**部署方式**：

1. 登录 https://modelscope.cn ，进入「创空间」→「创建创空间」；
2. 选择 **Streamlit** 类型或「快速部署」模式，上传本项目；
3. 等待构建完成，即可获得形如 `https://modelscope.cn/studios/<用户名>/<空间名>` 的公网地址。

> FRED Key 可通过创空间「环境变量」`FRED_API_KEY` 配置，代码中已带默认值，不配也能跑。

---

## 免责声明

本工具仅供学习与研究参考，不构成任何投资建议。市场数据存在延迟，请以官方渠道为准。
