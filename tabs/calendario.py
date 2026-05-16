"""Tab Calendario: flujo de cobros vs pagos por mes (cuotas con fecha)."""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from racing import cuotas, ui
from racing.formato import MESES_NOMBRE, fmt_ars, fmt_usd
from racing.ui import color_span as cs


def _anual(filas, fmt) -> None:
    if not filas:
        ui.html('<div class="muted-row">No hay cuotas pendientes con fecha.'
                '</div>')
        return
    labels = [f"{MESES_NOMBRE[f['mes']][:3]} {str(f['anio'])[2:]}"
              for f in filas]
    fig = go.Figure()
    fig.add_bar(x=labels, y=[f["cobros"] for f in filas], name="Cobros",
                marker_color="#00ff88")
    fig.add_bar(x=labels, y=[-f["pagos"] for f in filas], name="Pagos",
                marker_color="#ff4444")
    fig.add_scatter(x=labels, y=[f["acumulado"] for f in filas],
                    name="Saldo acumulado", mode="lines+markers",
                    line=dict(color="#4dabf7", width=3))
    fig.update_layout(barmode="relative", hovermode="x unified")
    ui.html('<div class="rc-h3">Flujo mensual proyectado</div>'
            '<div class="fuente">Barras: cobros (verde) y pagos (rojo). '
            'Línea: saldo acumulado del flujo.</div>')
    ui.plot(fig, height=380)

    body = []
    for f in filas:
        body.append([
            f"{MESES_NOMBRE[f['mes']]} {f['anio']}",
            cs(fmt(f["cobros"]), "pos"), cs(fmt(f["pagos"]), "neg"),
            cs(fmt(f["neto"]), "pos" if f["neto"] >= 0 else "neg"),
            cs(fmt(f["acumulado"]),
               "pos" if f["acumulado"] >= 0 else "neg"),
        ])
    ui.html('<div class="rc-h3">Detalle mes a mes</div>')
    ui.tabla(["Mes", "Cobros", "Pagos", "Neto", "Saldo acumulado"], body,
             clases_col=["", "num", "num", "num", "num"], scroll=True)


def _mensual(cobros_det, pagos_det, filas, fmt) -> None:
    if not filas:
        return
    opciones = {f"{MESES_NOMBRE[f['mes']]} {f['anio']}": (f["anio"], f["mes"])
                for f in filas}
    sel = st.selectbox("Mes", list(opciones.keys()), key="cal_mes")
    anio, mes = opciones[sel]
    ev = cuotas.eventos_del_mes(cobros_det, pagos_det, anio, mes)
    if not ev:
        ui.html('<div class="muted-row">Sin eventos este mes.</div>')
        return

    dias = sorted({e["dia"] for e in ev})
    cob = [sum(e["monto"] for e in ev if e["dia"] == d and e["tipo"] == "Cobro")
           for d in dias]
    pag = [sum(e["monto"] for e in ev if e["dia"] == d and e["tipo"] == "Pago")
           for d in dias]
    fig = go.Figure()
    fig.add_bar(x=dias, y=cob, name="Cobros", marker_color="#00ff88")
    fig.add_bar(x=dias, y=[-p for p in pag], name="Pagos",
                marker_color="#ff4444")
    fig.update_layout(barmode="relative", hovermode="x unified")
    ui.html(f'<div class="rc-h3">Flujo diario · {sel}</div>')
    ui.plot(fig, height=340)

    body = [[
        str(e["dia"]),
        cs(e["tipo"], "pos" if e["tipo"] == "Cobro" else "neg"),
        e["nombre"], e["vehiculo"], str(e["cuota"]),
        cs(fmt(e["monto"]), "pos" if e["tipo"] == "Cobro" else "neg"),
    ] for e in ev]
    ui.html('<div class="rc-h3">Eventos del mes</div>')
    ui.tabla(["Día", "Tipo", "Cliente / Acreedor", "Vehículo", "Cuota",
              "Monto"], body, clases_col=["", "", "", "", "", "num"],
             scroll=True)


def render(ctx: dict) -> None:
    pc = ctx["pc"]
    ui.html('<div class="rc-h2">Calendario de pagos y cobros</div>'
            '<div class="fuente">Solo cuotas pendientes con fecha. No incluye '
            'gastos operativos ni intereses de inversores.</div>')
    c1, c2 = st.columns(2)
    with c1:
        moneda = st.radio("Moneda", ["USD", "ARS"], horizontal=True,
                          key="cal_moneda")
    with c2:
        vista = st.radio("Vista", ["Anual", "Mes a mes"], horizontal=True,
                         key="cal_vista")
    m = moneda.lower()
    fmt = fmt_usd if m == "usd" else fmt_ars
    cobros_det = pc[f"cobros_{m}"]["detalle"]
    pagos_det = pc[f"pagos_{m}"]["detalle"]
    filas = cuotas.flujo_por_mes(cobros_det, pagos_det)

    if filas:
        ultimo = filas[-1]["acumulado"]
        ui.grid([
            ui.metric_card("Meses con movimiento", str(len(filas))),
            ui.metric_card("Total a cobrar",
                           cs(fmt(sum(f["cobros"] for f in filas)), "pos")),
            ui.metric_card("Total a pagar",
                           cs(fmt(sum(f["pagos"] for f in filas)), "neg")),
            ui.metric_card("Saldo final proyectado",
                           cs(fmt(ultimo), "pos" if ultimo >= 0 else "neg")),
        ])

    if vista == "Anual":
        _anual(filas, fmt)
    else:
        _mensual(cobros_det, pagos_det, filas, fmt)
