"""Plotly 图表通用布局与坐标轴工具"""
from .config import BG, BG_CARD, BORDER, GRID, TEXT

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
