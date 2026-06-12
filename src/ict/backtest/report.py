"""
Multi-timeframe Plotly backtest report (model-agnostic).
========================================================

A model's backtest produces a list of ``TradeViz`` objects — each carries the
candlestick frames for every timeframe used and a flat list of ``Mark`` overlays
(levels, zones, markers) tagged with a legend *group*. ``build_report`` renders
them to a single self-contained HTML page:

  * a dropdown to switch between an Overview (equity curve + stats) and each trade
  * per trade, one stacked candlestick panel per timeframe (zoom/scroll/pan)
  * every overlay grouped into a clickable legend group (click toggles the whole
    group); noisy groups start collapsed to ``legendonly`` so the default view
    stays clean.

The report knows nothing about FVGs or sweeps — models translate their own signal
into ``Mark`` objects (see ``backtests/fvg_sweep_backtest.py`` for the adapter).
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Column widths (left→right) so the execution timeframe (last) gets the most room.
_PANEL_SPANS = {1: [1.0], 2: [0.4, 0.6], 3: [0.25, 0.3, 0.45], 4: [0.2, 0.22, 0.25, 0.33]}


@dataclass
class Mark:
    """A single overlay on one timeframe panel.

    kind:
      'level'  — horizontal line at ``price`` (spans the panel unless t0/t1 set)
      'zone'   — filled rectangle between ``y0``/``y1`` (and t0/t1, default full width)
      'marker' — a point at (``time``, ``price``)
    group: legend group label; clicking it toggles every mark sharing it.
    panel: timeframe key (must match a key in TradeViz.panels).
    default_on: False => the group starts collapsed (legendonly).
    """
    kind: str
    group: str
    panel: str
    label: str = ""
    color: str = "#888888"
    dash: Optional[str] = None
    price: Optional[float] = None
    y0: Optional[float] = None
    y1: Optional[float] = None
    t0: Optional[pd.Timestamp] = None
    t1: Optional[pd.Timestamp] = None
    time: Optional[pd.Timestamp] = None
    symbol: str = "circle"
    default_on: bool = True


@dataclass
class TradeViz:
    """Everything needed to render one trade across its timeframes."""
    label: str                       # dropdown label, e.g. "2025-02-24  SHORT  -$160"
    panels: dict                     # {tf_key: candlestick DataFrame (OHLC, DatetimeIndex)}
    marks: list = field(default_factory=list)
    pnl: float = 0.0


# ──────────────────────────────────────────────────────────────────────────────
# Figure building
# ──────────────────────────────────────────────────────────────────────────────

def _weekend_break():
    return dict(bounds=["sat", "mon"])


def _panel_xrange(df: pd.DataFrame):
    return [df.index.min(), df.index.max()]


def _mark_trace(m: Mark, panels: dict):
    """Return (trace, panel_key) for a Mark, or None if its panel is missing."""
    df = panels.get(m.panel)
    if df is None or len(df) == 0:
        return None
    x0, x1 = _panel_xrange(df)

    if m.kind == "level":
        t0 = m.t0 if m.t0 is not None else x0
        t1 = m.t1 if m.t1 is not None else x1
        return go.Scatter(
            x=[t0, t1], y=[m.price, m.price], mode="lines",
            line=dict(color=m.color, width=1.4, dash=m.dash),
            name=m.label, legendgroup=m.group,
            hovertemplate=f"{html.escape(m.label)}: {m.price:.2f}<extra></extra>",
        ), m.panel

    if m.kind == "zone":
        t0 = m.t0 if m.t0 is not None else x0
        t1 = m.t1 if m.t1 is not None else x1
        return go.Scatter(
            x=[t0, t1, t1, t0, t0],
            y=[m.y0, m.y0, m.y1, m.y1, m.y0],
            fill="toself", mode="lines",
            line=dict(color=m.color, width=0),
            fillcolor=m.color, opacity=0.18,
            name=m.label, legendgroup=m.group,
            hoverinfo="skip",
        ), m.panel

    if m.kind == "marker":
        return go.Scatter(
            x=[m.time], y=[m.price], mode="markers",
            marker=dict(color=m.color, size=11, symbol=m.symbol,
                        line=dict(color="white", width=1)),
            name=m.label, legendgroup=m.group,
            hovertemplate=f"{html.escape(m.label)}: {m.price:.2f}<br>%{{x}}<extra></extra>",
        ), m.panel

    return None


def _trade_figure(tv: TradeViz, panel_order: list) -> go.Figure:
    panels = [p for p in panel_order if p in tv.panels and len(tv.panels[p])]
    n = len(panels)
    widths = _PANEL_SPANS.get(n, [1.0 / n] * n)
    fig = make_subplots(
        rows=1, cols=n, shared_yaxes=False, horizontal_spacing=0.035,
        column_widths=widths,
        subplot_titles=[f"{p} — {tv.label}" for p in panels],
    )

    # Candlesticks (always on, never in the legend)
    for i, p in enumerate(panels, start=1):
        df = tv.panels[p]
        fig.add_trace(
            go.Candlestick(
                x=df.index, open=df["open"], high=df["high"],
                low=df["low"], close=df["close"],
                name=p, showlegend=False,
                increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
            ),
            row=1, col=i,
        )

    # Overlays — one legend entry per group; group decides default visibility
    seen_groups = set()
    group_default_on = {}
    for m in tv.marks:
        group_default_on.setdefault(m.group, m.default_on)

    panel_col = {p: i for i, p in enumerate(panels, start=1)}
    for m in tv.marks:
        built = _mark_trace(m, tv.panels)
        if built is None:
            continue
        trace, pkey = built
        col = panel_col.get(pkey)
        if col is None:
            continue
        first = m.group not in seen_groups
        trace.update(
            showlegend=first,
            legendgroup=m.group,
            legendgrouptitle_text=m.group if first else None,
            visible=True if group_default_on.get(m.group, True) else "legendonly",
        )
        seen_groups.add(m.group)
        fig.add_trace(trace, row=1, col=col)

    # TradingView-style crosshair: spike lines that follow the cursor on both axes.
    spike = dict(showspikes=True, spikemode="across", spikesnap="cursor",
                 spikethickness=1, spikedash="dot", spikecolor="#5b6b7b")
    for i, p in enumerate(panels, start=1):
        fig.update_xaxes(rangeslider_visible=False, rangebreaks=[_weekend_break()],
                         hoverformat="%a %b %-d %Y  %H:%M", row=1, col=i, **spike)
        # Exact price (no SI abbreviation) on the axis and in the hover readout.
        fig.update_yaxes(tickformat=",.2f", hoverformat=",.2f", row=1, col=i, **spike)

    fig.update_layout(
        height=760,
        margin=dict(l=62, r=20, t=46, b=30),
        legend=dict(groupclick="togglegroup", orientation="v",
                    yanchor="top", y=1, xanchor="left", x=1.01,
                    font=dict(size=11)),
        template="plotly_white",
        hovermode="x unified",
        dragmode="pan",          # drag pans like TradingView; scroll-wheel zooms
        spikedistance=-1,        # always draw the crosshair, not only near a point
        hoverdistance=-1,
    )
    return fig


def _overview_figure(equity: Optional[pd.Series]) -> Optional[go.Figure]:
    if equity is None or len(equity) == 0:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(equity) + 1)), y=equity.values,
        mode="lines+markers", line=dict(color="#1f77b4", width=2),
        name="Equity",
        hovertemplate="trade %{x}: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="black", line_width=0.8)
    fig.update_layout(
        title="Cumulative P&L (USD)", template="plotly_white",
        height=420, margin=dict(l=55, r=20, t=50, b=40),
        xaxis_title="Trade #", yaxis_title="Cumulative P&L ($)",
    )
    return fig


# ──────────────────────────────────────────────────────────────────────────────
# HTML assembly
# ──────────────────────────────────────────────────────────────────────────────

_PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"

_PAGE = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
<script src="{cdn}"></script>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; background:#fafafa; color:#222; }}
  header {{ position: sticky; top:0; z-index:10; background:#fff; border-bottom:1px solid #e3e3e3;
           padding:10px 18px; display:flex; align-items:center; gap:14px; box-shadow:0 1px 3px rgba(0,0,0,.05); }}
  header h1 {{ font-size:15px; margin:0; font-weight:600; }}
  select {{ font-size:14px; padding:5px 8px; border:1px solid #ccc; border-radius:6px; min-width:280px; }}
  .pnl-pos {{ color:#1a8a4a; font-weight:600; }}
  .pnl-neg {{ color:#c0392b; font-weight:600; }}
  .view {{ display:none; padding:6px 12px 40px; }}
  .view.active {{ display:block; }}
  table.stats {{ border-collapse:collapse; margin:14px 0; font-size:13px; }}
  table.stats td {{ border:1px solid #e3e3e3; padding:5px 12px; }}
  table.stats td.k {{ background:#f4f4f4; font-weight:600; }}
</style>
</head><body>
<header>
  <h1>{title}</h1>
  <select id="sel" onchange="showView(this.value)">{options}</select>
  <span id="hint" style="font-size:12px;color:#888">scroll to zoom · drag to pan · double-click to reset · crosshair follows cursor</span>
</header>
{views}
<script>
function showView(id) {{
  document.querySelectorAll('.view').forEach(function(v) {{ v.classList.remove('active'); }});
  var el = document.getElementById(id);
  el.classList.add('active');
  el.querySelectorAll('.js-plotly-plot').forEach(function(gd) {{ Plotly.Plots.resize(gd); }});
}}
document.addEventListener('DOMContentLoaded', function() {{ showView('view-0'); }});
</script>
</body></html>"""


def _stats_table(stats: dict) -> str:
    if not stats:
        return ""
    rows = "".join(
        f"<tr><td class='k'>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>"
        for k, v in stats.items()
    )
    return f"<table class='stats'>{rows}</table>"


def _fig_div(fig: go.Figure, div_id: str) -> str:
    return fig.to_html(
        full_html=False, include_plotlyjs=False, div_id=div_id,
        config={"responsive": True, "scrollZoom": True, "displaylogo": False},
    )


def build_report(
    trades: list,
    panel_order: list,
    out_path: str,
    title: str = "Backtest Report",
    equity: Optional[pd.Series] = None,
    stats: Optional[dict] = None,
) -> str:
    """Render trades to a single self-contained HTML file. Returns out_path."""
    options = []
    views = []

    # View 0 — Overview
    ov_parts = [f"<h2 style='font-size:16px'>{html.escape(title)}</h2>", _stats_table(stats or {})]
    ov_fig = _overview_figure(equity)
    if ov_fig is not None:
        ov_parts.append(_fig_div(ov_fig, "fig-overview"))
    views.append(f"<div class='view active' id='view-0'>{''.join(ov_parts)}</div>")
    options.append("<option value='view-0'>Overview — equity &amp; stats</option>")

    # One view per trade
    for i, tv in enumerate(trades, start=1):
        vid = f"view-{i}"
        div = _fig_div(_trade_figure(tv, panel_order), f"fig-{i}")
        views.append(f"<div class='view' id='{vid}'>{div}</div>")
        options.append(f"<option value='{vid}'>{html.escape(tv.label)}</option>")

    page = _PAGE.format(
        title=html.escape(title), cdn=_PLOTLY_CDN,
        options="".join(options), views="\n".join(views),
    )
    with open(out_path, "w") as f:
        f.write(page)
    return out_path
