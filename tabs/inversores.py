"""Tab Inversores & gastos fijos."""
from __future__ import annotations

from datetime import date

import plotly.graph_objects as go

from racing import ui
from racing.formato import fmt_fecha, fmt_usd
from racing.ui import color_span as cs


def _estado_pago(iso: str | None) -> str:
    if not iso:
        return '<span class="dim">Sin registro</span>'
    y, m, d = map(int, iso.split("-"))
    dias = (date.today() - date(y, m, d)).days
    if dias > 35:
        return cs(f"Atrasado ({dias}d)", "neg")
    if dias > 30:
        return cs(f"Por vencer ({dias}d)", "warn")
    return cs(f"Al día ({dias}d)", "pos")


def render(ctx: dict) -> None:
    inv = ctx["inv"]
    t = inv["totales"]
    acre = inv["acreedores"]
    ui.html('<div class="rc-h2">Inversores & gastos fijos</div>'
            '<div class="fuente">Fuente: planilla <code>inversion</code> · '
            'tabs Acreedores y GastosFijos</div>')

    con_int = [a for a in acre if a["interes_pct"] > 0]
    tasa_prom = (sum(a["interes_pct"] for a in con_int) / len(con_int)
                 if con_int else 0)
    ui.grid([
        ui.metric_card("Capital total", fmt_usd(t["acreedores"])),
        ui.metric_card("Interés mensual", cs(fmt_usd(t["interes_mensual"]), "neg")),
        ui.metric_card("Tasa promedio", f"{tasa_prom:.2f}%/mes"),
        ui.metric_card("Inversores activos", str(len(acre))),
    ])

    if acre:
        fig = go.Figure(go.Bar(
            x=[a["monto_usd"] for a in acre],
            y=[a["nombre"] for a in acre], orientation="h",
            marker_color="#00ff88",
            text=[fmt_usd(a["monto_usd"]) for a in acre],
            textposition="outside"))
        fig.update_yaxes(autorange="reversed")
        ui.html('<div class="rc-h3">Capital prestado por inversor</div>')
        ui.plot(fig, height=max(360, len(acre) * 34))

    filas = [[
        a["nombre"], fmt_usd(a["monto_usd"]), f'{a["interes_pct"]:.2f}%',
        fmt_usd(a["interes_mensual_usd"]),
        fmt_fecha(a["ultima_fecha_pago"]),
        _estado_pago(a["ultima_fecha_pago"]),
    ] for a in acre]
    ui.html('<div class="rc-h3">Detalle de inversores</div>')
    ui.tabla(["Inversor", "Capital USD", "% mensual", "Interés USD",
              "Último pago", "Estado"], filas,
             clases_col=["", "num", "num", "num", "", ""])

    g = inv["gastos_fijos"]
    if g:
        ui.html('<div class="rc-h3">Gastos fijos mensuales</div>')
        c1, c2 = __import__("streamlit").columns([1, 1])
        with c1:
            filas = [[x["concepto"], fmt_usd(x["monto_usd"])] for x in g]
            filas.append(["<strong>TOTAL</strong>",
                          cs(fmt_usd(t["gastos_fijos"]), "pos")])
            ui.tabla(["Concepto", "USD"], filas, clases_col=["", "num"])
        with c2:
            fig = go.Figure(go.Bar(
                x=[x["monto_usd"] for x in g], y=[x["concepto"] for x in g],
                orientation="h", marker_color="#ffaa00",
                text=[fmt_usd(x["monto_usd"]) for x in g],
                textposition="outside"))
            fig.update_yaxes(autorange="reversed")
            ui.plot(fig, height=max(360, len(g) * 34))
