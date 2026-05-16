"""Design system fintech dark (port del <style> del prototipo) + helpers UI."""
from __future__ import annotations

import html as _html

import streamlit as st

CSS = """
<style>
:root {
  --bg:#0a0a0a; --surface:#141414; --surface2:#1e1e1e;
  --border:#222; --accent:#00ff88; --negative:#ff4444;
  --warning:#ffaa00; --text:#e0e0e0; --dim:#888;
}
.stApp { background: var(--bg); }
#MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; }
.block-container { max-width: 1400px; padding-top: 1.2rem; padding-bottom: 3rem; }
html, body, [class*="css"] { color: var(--text); }

.rc-h1 { font-size: 1.8rem; font-weight: 600; margin: 0; }
.rc-sub { color: var(--dim); margin-top: 4px; font-size: 0.85rem; }
h2, .rc-h2 { font-size: 1.2rem; font-weight: 600; margin: 18px 0 8px; }
h3, .rc-h3 { font-size: 1rem; font-weight: 600; margin: 16px 0 8px; }

.grid { display: grid; gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); margin-bottom: 18px; }
.metric { background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 16px; }
.metric .label { color: var(--dim); font-size: 0.8rem; margin-bottom: 6px; }
.metric .value { font-size: 1.5rem; font-weight: 600; }
.metric .delta { font-size: 0.8rem; margin-top: 4px; color: var(--dim); }
.metric .delta.negative { color: var(--negative); }
.metric .delta.warning { color: var(--warning); }
.metric .delta.pos { color: var(--accent); }

.card { background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px; margin-bottom: 16px; }
.pos { color: var(--accent); } .neg { color: var(--negative); }
.dim { color: var(--dim); } .warn { color: var(--warning); }

table.rc { width: 100%; border-collapse: collapse; margin-top: 8px;
  font-size: 0.85rem; }
table.rc th, table.rc td { text-align: left; padding: 9px 12px;
  border-bottom: 1px solid var(--border); }
table.rc th { color: var(--dim); font-weight: 500; font-size: 0.78rem;
  text-transform: uppercase; letter-spacing: 0.5px; }
table.rc td.num, table.rc th.num { text-align: right;
  font-variant-numeric: tabular-nums; }
table.rc tbody tr:hover { background: var(--surface2); }
.scroll-table { max-height: 480px; overflow-y: auto;
  border: 1px solid var(--border); border-radius: 10px; }

.alert-list { list-style: none; padding: 0; margin: 0; }
.alert-list li { padding: 12px 0; border-bottom: 1px solid var(--border); }
.alert-list li:last-child { border-bottom: none; }
.alert-title { font-weight: 500; }
.alert-detail { color: var(--dim); font-size: 0.85rem; margin-left: 24px; }

.warning-banner { background: rgba(255,170,0,0.1); border: 1px solid var(--warning);
  border-radius: 8px; padding: 12px 16px; margin: 8px 0 16px; font-size: 0.9rem; }
.warning-banner strong { color: var(--warning); }
.accent-banner { background: rgba(0,255,136,0.06); border: 1px solid var(--accent);
  border-radius: 8px; padding: 12px 16px; margin: 8px 0 16px; font-size: 0.9rem; }
.accent-banner strong { color: var(--accent); }
.fuente { color: var(--dim); font-size: 0.75rem; font-style: italic; margin: 6px 0 4px; }
.muted-row { color: var(--dim); font-size: 0.85rem; margin: 8px 0; }

.estado-badge { display: inline-block; padding: 3px 10px; border-radius: 12px;
  font-size: 0.75rem; font-weight: 500; }
.estado-realizado { background: rgba(0,255,136,0.15); color: #00ff88; }
.estado-pendiente { background: rgba(255,170,0,0.15); color: #ffaa00; }
.estado-vencido  { background: rgba(255,68,68,0.15); color: #ff4444; }

.deuda-grid { display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fill, minmax(330px, 1fr)); }
.deuda-card { background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 13px; }
.deuda-card .cliente { font-size: 0.9rem; font-weight: 600; line-height: 1.25; }
.deuda-card .vehiculo { font-size: 0.78rem; color: var(--dim); margin-top: 1px; }
.deuda-card .monto { font-size: 1.02rem; font-weight: 600; text-align: right;
  white-space: nowrap; }
.deuda-card .stats { display: flex; gap: 8px; margin: 10px 0 4px;
  padding: 7px; background: var(--bg); border-radius: 6px; font-size: 0.74rem; }
.deuda-card .stat { flex: 1; text-align: center; }
.deuda-card .stat .l { color: var(--dim); font-size: 0.64rem;
  text-transform: uppercase; }
.deuda-card .stat .v { font-weight: 600; margin-top: 2px; font-size: 0.8rem; }

/* Desplegable de detalle de cuotas dentro de cada card */
.cuotas-det { margin-top: 8px; border-top: 1px solid var(--border);
  padding-top: 6px; }
.cuotas-det > summary { cursor: pointer; list-style: none; font-size: 0.74rem;
  color: var(--dim); user-select: none; padding: 2px 0; }
.cuotas-det > summary::-webkit-details-marker { display: none; }
.cuotas-det > summary::before { content: "\25B8  Ver cuotas"; }
.cuotas-det[open] > summary::before { content: "\25BE  Ocultar cuotas"; }
.cuotas-det > summary:hover { color: var(--accent); }
table.rc-mini { width: 100%; border-collapse: collapse; margin-top: 6px;
  font-size: 0.7rem; }
table.rc-mini th { color: var(--dim); font-weight: 500; text-align: left;
  padding: 4px 6px; border-bottom: 1px solid var(--border);
  text-transform: uppercase; font-size: 0.62rem; letter-spacing: 0.4px; }
table.rc-mini td { padding: 4px 6px; border-bottom: 1px solid var(--border);
  font-variant-numeric: tabular-nums; }
table.rc-mini td.r, table.rc-mini th.r { text-align: right; }
table.rc-mini tr:last-child td { border-bottom: none; }
.progress-bar { height: 8px; background: var(--bg); border-radius: 4px;
  overflow: hidden; border: 1px solid var(--border); margin: 10px 0 4px; }
.progress-fill { height: 100%; }
.progress-label { display: flex; justify-content: space-between;
  font-size: 0.78rem; color: var(--dim); }

.stTabs [data-baseweb="tab-list"] { gap: 4px; background: var(--surface);
  padding: 6px; border-radius: 10px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: var(--dim);
  border-radius: 6px; padding: 8px 14px; }
.stTabs [aria-selected="true"] { background: var(--surface2) !important;
  color: var(--accent) !important; }
div[data-testid="stDataFrame"] { border: 1px solid var(--border);
  border-radius: 10px; }
</style>
"""


def inyectar_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def _esc(s) -> str:
    return _html.escape(str(s), quote=True)


def metric_card(label, value, delta=None, delta_class="", info=None) -> str:
    """value puede traer HTML (spans .pos/.neg). label/delta se escapan."""
    info_ic = (f' <span title="{_esc(info)}" '
               f'style="cursor:help;color:var(--dim)">ⓘ</span>') if info else ""
    h = (f'<div class="metric"><div class="label">{_esc(label)}{info_ic}</div>'
         f'<div class="value">{value}</div>')
    if delta:
        h += f'<div class="delta {delta_class}">{_esc(delta)}</div>'
    return h + "</div>"


def grid(cards: list[str]) -> None:
    st.markdown(f'<div class="grid">{"".join(cards)}</div>',
                unsafe_allow_html=True)


def html(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


def tabla(headers: list, filas: list[list], clases_col: list[str] | None = None,
          scroll: bool = False) -> None:
    """headers: list[str]; filas: list de celdas que pueden traer HTML."""
    th = "".join(
        f'<th class="{(clases_col[i] if clases_col else "")}">{_esc(h)}</th>'
        for i, h in enumerate(headers))
    body = ""
    for fila in filas:
        tds = "".join(
            f'<td class="{(clases_col[i] if clases_col else "")}">{c}</td>'
            for i, c in enumerate(fila))
        body += f"<tr>{tds}</tr>"
    t = f'<table class="rc"><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'
    if scroll:
        t = f'<div class="scroll-table">{t}</div>'
    st.markdown(t, unsafe_allow_html=True)


def color_span(value: str, cls: str) -> str:
    return f'<span class="{cls}">{value}</span>'


PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#888", family="-apple-system, Segoe UI, sans-serif"),
    xaxis=dict(gridcolor="#222", zerolinecolor="#222"),
    yaxis=dict(gridcolor="#222", zerolinecolor="#222"),
    margin=dict(l=40, r=20, t=30, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#888")),
    hoverlabel=dict(bgcolor="#1e1e1e", font=dict(color="#e0e0e0")),
)
PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


def plot(fig, height: int = 340) -> None:
    fig.update_layout(**PLOT_LAYOUT, height=height)
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)
