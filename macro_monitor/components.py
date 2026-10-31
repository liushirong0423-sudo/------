"""HTML 卡片组件（KPI 卡片等）"""


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
