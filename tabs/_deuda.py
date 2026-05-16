"""Vista compartida de Cobros/Pagos: KPIs, top, columnas de estado, detalle."""
from __future__ import annotations

from datetime import date

import plotly.graph_objects as go
import streamlit as st

from racing import cuotas, ui
from racing.formato import fmt_ars, fmt_usd


def _card(g: dict, fmt, accent: str) -> str:
    pct = round(g["pagas"] / g["total_cuotas"] * 100) if g["total_cuotas"] else 0
    cat = g["categoria"]
    fill = "#ff4444" if cat == "vencidos" else (
        "#00ff88" if cat == "realizados" else "#ffaa00")
    monto_color = "#00ff88" if cat == "realizados" else accent
    monto = g["pagado"] if cat == "realizados" else g["pendiente"]

    if cat == "vencidos":
        estado = (f'<div class="estado-line"><span class="neg">'
                  f'{g["vencidas"]} vencida{"s" if g["vencidas"] > 1 else ""}'
                  f'</span></div>')
    elif cat == "pendientes" and g["proxima_fecha"]:
        dp = g["dias_proximo"]
        txt = ("HOY" if dp == 0 else "mañana" if dp == 1 else f"en {dp} días")
        cls = "warn" if (dp is not None and dp <= 7) else "dim"
        estado = (f'<div class="estado-line"><span class="dim">Próximo: '
                  f'</span><strong>{g["proxima_fecha"].strftime("%d/%m/%y")}'
                  f'</strong> · <span class="{cls}">{txt}</span></div>')
    else:
        estado = '<div class="estado-line"><span class="pos">Al día</span></div>'

    return (
        f'<div class="deuda-card">'
        f'<div style="display:flex;justify-content:space-between;gap:8px">'
        f'<div><div class="cliente">{g["cliente"]}</div>'
        f'<div class="vehiculo">{g["vehiculo"]}</div></div>'
        f'<div class="monto" style="color:{monto_color}">{fmt(monto)}</div>'
        f'</div>'
        f'<div class="stats">'
        f'<div class="stat"><div class="l">Cuotas</div>'
        f'<div class="v">{g["pagas"]}/{g["total_cuotas"]}</div></div>'
        f'<div class="stat"><div class="l">Pagado</div>'
        f'<div class="v pos">{fmt(g["pagado"])}</div></div>'
        f'<div class="stat"><div class="l">Pendiente</div>'
        f'<div class="v">{fmt(g["pendiente"])}</div></div></div>'
        f'<div class="progress-bar"><div class="progress-fill" '
        f'style="width:{pct}%;background:{fill}"></div></div>'
        f'<div class="progress-label"><span>{pct}% pagado</span></div>'
        f'{estado}</div>'
    )


def _columna(titulo: str, total_txt: str, grupos: list[dict], fmt,
             accent: str) -> str:
    cards = "".join(_card(g, fmt, accent) for g in grupos) or \
        '<div class="dim" style="padding:12px">Sin registros</div>'
    return (f'<div><div class="col-header" style="display:flex;'
            f'justify-content:space-between;padding:10px 14px;border-radius:8px;'
            f'margin-bottom:12px;font-weight:600"><span>{titulo} '
            f'({len(grupos)})</span><span>{total_txt}</span></div>'
            f'<div class="cards-stack" style="display:flex;flex-direction:'
            f'column;gap:12px;max-height:760px;overflow-y:auto">{cards}</div>'
            f'</div>')


def render_deuda(ctx: dict, tipo: str) -> None:
    """tipo: 'cobros' o 'pagos'."""
    pc = ctx["pc"]
    es_cobro = tipo == "cobros"
    quien = "cliente" if es_cobro else "acreedor"
    accent = "#00ff88" if es_cobro else "#ff4444"

    ui.html(f'<div class="rc-h2">{"Cobros" if es_cobro else "Pagos"} '
            f'pendientes</div><div class="fuente">Fuente: planilla '
            f'<code>PLANILLA PAGOS Y COBROS ULTIMO</code></div>')
    moneda = st.radio("Moneda", ["USD", "ARS"], horizontal=True,
                      label_visibility="collapsed", key=f"{tipo}_moneda")
    fmt = fmt_usd if moneda == "USD" else fmt_ars
    d = pc[f"{tipo}_{moneda.lower()}"]

    ui.grid([
        ui.metric_card("Total pendiente", fmt(d["total_pendiente"])),
        ui.metric_card("Ya " + ("cobrado" if es_cobro else "pagado"),
                       fmt(d["total_pagado"])),
        ui.metric_card(f"{quien.capitalize()}s con deuda",
                       str(d["clientes_pendientes"])),
        ui.metric_card("Cuotas pendientes", str(d["cuotas_pendientes"])),
    ])

    top = d["top"]
    if top:
        fig = go.Figure(go.Bar(
            x=[r["pendiente"] for r in top], y=[r["Cliente"] for r in top],
            orientation="h", marker_color=accent,
            text=[fmt(r["pendiente"]) for r in top], textposition="outside",
            hovertemplate="<b>%{y}</b><br>Debe: %{x:,.0f}<extra></extra>"))
        fig.update_yaxes(autorange="reversed")
        fig.update_xaxes(showticklabels=False)
        ui.html(f'<div class="rc-h3">Top {"deudores" if es_cobro else "acreedores"}</div>')
        ui.plot(fig, height=max(360, len(top) * 34))

    g = cuotas.agrupar_deuda(d["detalle"], hoy=date.today())
    ui.html('<div class="rc-h3">Estado de cuentas</div>'
            '<div class="fuente">Agrupado por '
            f'{quien} + vehículo, comparado con hoy.</div>')
    col = (_columna("Vencidos", fmt(g["total_vencidos"]), g["vencidos"], fmt,
                    accent)
           + _columna("En fecha", fmt(g["total_pendientes"]), g["pendientes"],
                      fmt, accent)
           + _columna("Realizados", fmt(g["total_realizados"]),
                      g["realizados"], fmt, accent))
    ui.html(f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;'
            f'gap:16px">{col}</div>')

    q = st.text_input("Buscar", placeholder=f"Buscar {quien} o vehículo",
                      label_visibility="collapsed", key=f"{tipo}_q").lower()
    filas = []
    for c in d["detalle"]:
        txt = f"{c['Cliente']} {c['Veiculo']}".lower()
        if q and q not in txt:
            continue
        filas.append([
            c["Cliente"], c["Veiculo"], str(c["Año"] or ""),
            c["Mes"] or "", str(c["Cuotas"] or ""),
            fmt(c["Cuota Pendiente"]), fmt(c["Cuota Abonada"]),
        ])
    ui.html('<div class="rc-h3">Vista detallada · todas las cuotas</div>')
    ui.tabla([quien.capitalize(), "Vehículo", "Año", "Mes", "Cuotas",
              "Pendiente", "Abonada"], filas,
             clases_col=["", "", "", "", "", "num", "num"], scroll=True)
