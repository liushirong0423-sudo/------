"""Bloomberg 深色金融风格全局样式"""
import streamlit as st

CSS = '''
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
'''


def apply_theme():
    """注入全局 CSS（在 set_page_config 之后调用一次）。"""
    st.markdown(CSS, unsafe_allow_html=True)
