"""Tab Caja: saldo, evolución, gastos por categoría, movimientos."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from racing import categorias, ui
from racing.formato import fmt_ars, fmt_usd
from racing.ui import color_span as cs


def render(ctx: dict) -> None:
    caja = ctx["caja"]
    ui.html('<div class="rc-h2">Caja diaria</div>'
            '<div class="fuente">Fuente: planilla <code>caja racing cars</code>'
            '</div>')

    moneda = st.radio("Moneda", ["Pesos (ARS)", "Dólares (USD)"],
                      horizontal=True, label_visibility="collapsed",
                      key="caja_moneda")
    key = "pesos" if moneda.startswith("Pesos") else "usd"
    fmt = fmt_ars if key == "pesos" else fmt_usd
    d = caja[key]

    ui.grid([
        ui.metric_card("Saldo actual",
                       cs(fmt(d["saldo_actual"]),
                          "pos" if d["saldo_actual"] >= 0 else "neg")),
        ui.metric_card("Movimientos", f"{d['cantidad']:,}".replace(",", ".")),
        ui.metric_card("Total ingresos", cs(fmt(d["total_ingresos"]), "pos")),
        ui.metric_card("Total salidas", cs(fmt(d["total_salidas"]), "neg")),
    ])

    movs = d["movimientos"]
    con_fecha = sorted([m for m in movs if m["fecha"]], key=lambda m: m["fecha"])
    if con_fecha:
        fig = go.Figure(go.Scatter(
            x=[m["fecha"] for m in con_fecha],
            y=[m["saldo"] for m in con_fecha],
            mode="lines", line=dict(color="#00ff88", width=2),
            fill="tozeroy", fillcolor="rgba(0,255,136,0.1)",
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
        ui.html(f'<div class="rc-h3">Evolución del saldo · {moneda}</div>')
        ui.plot(fig, height=300)

    salidas = [m for m in movs if (m["monto"] or 0) < 0]
    porcat: dict[str, dict] = {}
    for m in salidas:
        cat = categorias.get_categoria(m["fecha"], m["descripcion"], m["monto"])
        e = porcat.setdefault(cat["nombre"],
                              {**cat, "total": 0.0, "count": 0})
        e["total"] += abs(m["monto"])
        e["count"] += 1
    cats = sorted(porcat.values(), key=lambda x: x["total"], reverse=True)

    if cats:
        ui.html('<div class="rc-h3">Gastos por categoría</div>'
                '<div class="fuente">Categorías detectadas por palabras clave '
                'en la descripción. Solo salidas (montos negativos).</div>')
        c1, c2 = st.columns([1, 1])
        with c1:
            fig = go.Figure(go.Pie(
                labels=[f"{c['emoji']} {c['nombre']}" for c in cats],
                values=[c["total"] for c in cats], hole=0.5,
                marker=dict(colors=[c["color"] for c in cats]),
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>"
                              "%{percent}<extra></extra>"))
            ui.plot(fig, height=330)
        with c2:
            total = sum(c["total"] for c in cats)
            filas = [[
                f'<span style="background:{c["color"]}30;color:{c["color"]};'
                f'padding:2px 8px;border-radius:4px">{c["emoji"]} '
                f'{c["nombre"]}</span>',
                str(c["count"]),
                cs(f'{fmt(c["total"])} <span class="dim">'
                   f'({c["total"]/total*100:.1f}%)</span>', "neg"),
            ] for c in cats]
            filas.append(["<strong>TOTAL</strong>", str(len(salidas)),
                          cs(fmt(total), "neg")])
            ui.tabla(["Categoría", "Cantidad", "Total"], filas,
                     clases_col=["", "num", "num"])

    ui.html('<div class="rc-h3">Movimientos</div>')
    q = st.text_input("Buscar", placeholder="Buscar en descripción",
                      label_visibility="collapsed", key="caja_q").lower()
    filt = [m for m in movs if not q or q in (m["descripcion"] or "").lower()]
    filt = sorted(filt, key=lambda m: m["fecha"] or "", reverse=True)
    st.caption(f"{len(filt):,} movimientos".replace(",", "."))

    df = pd.DataFrame([{
        "Fecha": ("/".join(reversed(m["fecha"].split("-")))
                  if m["fecha"] else "—"),
        "Descripción": m["descripcion"],
        "Categoría": (lambda c: f"{c['emoji']} {c['nombre']}")(
            categorias.get_categoria(m["fecha"], m["descripcion"], m["monto"])),
        "Monto": m["monto"],
        "Saldo": m["saldo"],
    } for m in filt])
    st.dataframe(
        df, width="stretch", hide_index=True, height=460,
        column_config={
            "Monto": st.column_config.NumberColumn(format="%.2f"),
            "Saldo": st.column_config.NumberColumn(format="%.2f"),
        })
