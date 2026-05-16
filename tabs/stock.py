"""Tab Stock & Ventas: stock activo, trabados, ventas históricas."""
from __future__ import annotations

from datetime import date

import plotly.graph_objects as go
import streamlit as st

from racing import ui
from racing.formato import fmt_usd
from racing.ui import color_span as cs


def _semaforo(dias: int) -> tuple[str, str]:
    if dias <= 30:
        return "#00ff88", "#000"
    if dias <= 60:
        return "#88dd44", "#000"
    if dias <= 90:
        return "#ffcc00", "#000"
    if dias <= 150:
        return "#ff8800", "#000"
    return "#ff4444", "#fff"


def _stock_activo(inv: dict) -> None:
    t = inv["totales"]
    ui.grid([
        ui.metric_card("Vehículos en stock", str(t["stock_count"])),
        ui.metric_card("Costo total", fmt_usd(t["stock_costo"])),
        ui.metric_card("Valor liquidación", cs(fmt_usd(t["stock_liqui"]), "pos")),
        ui.metric_card("Ganancia esperada",
                       cs(fmt_usd(t["stock_liqui"] - t["stock_costo"]), "pos")),
    ])
    c1, c2 = st.columns([2, 1])
    with c1:
        q = st.text_input("Buscar", placeholder="Buscar marca / modelo",
                          label_visibility="collapsed", key="stock_q").lower()
    with c2:
        orden = st.selectbox("Orden", [
            "Orden planilla", "Más viejos primero", "Más nuevos primero",
            "Costo mayor primero", "Costo menor primero",
            "Precio venta mayor", "Ganancia mayor primero"],
            label_visibility="collapsed", key="stock_sort")

    hoy = date.today()
    rows = []
    for v in inv["stock_activo"]:
        if q and q not in f"{v['marca']} {v['modelo']}".lower():
            continue
        dias = None
        if v["fecha_ingreso"]:
            y, m, d = map(int, v["fecha_ingreso"].split("-"))
            dias = (hoy - date(y, m, d)).days
        rows.append({**v, "dias": dias})

    def k_dias(r, default):
        return r["dias"] if r["dias"] is not None else default
    if orden == "Más viejos primero":
        rows.sort(key=lambda r: k_dias(r, -1), reverse=True)
    elif orden == "Más nuevos primero":
        rows.sort(key=lambda r: k_dias(r, 10**9))
    elif orden == "Costo mayor primero":
        rows.sort(key=lambda r: r["costo"], reverse=True)
    elif orden == "Costo menor primero":
        rows.sort(key=lambda r: r["costo"])
    elif orden == "Precio venta mayor":
        rows.sort(key=lambda r: r["venta"], reverse=True)
    elif orden == "Ganancia mayor primero":
        rows.sort(key=lambda r: r["liqui"] - r["costo"], reverse=True)

    filas = []
    for v in rows:
        if v["dias"] is None:
            ing = '<span class="dim">—</span>'
        else:
            bg, fg = _semaforo(v["dias"])
            fi = "/".join(reversed(v["fecha_ingreso"].split("-")))
            ing = (f'{fi} <span style="background:{bg};color:{fg};padding:1px '
                   f'6px;border-radius:3px;font-size:0.72rem;font-weight:600">'
                   f'{v["dias"]}d</span>')
        filas.append([
            v["marca"] or "—", str(v["anio"] or "—"), v["modelo"] or "—", ing,
            fmt_usd(v["costo"]), fmt_usd(v["venta"]), fmt_usd(v["liqui"]),
            cs(fmt_usd(v["liqui"] - v["costo"]), "pos"),
            "Sí" if v["publi"] else '<span class="dim">—</span>',
        ])
    ui.html('<div class="muted-row">Semáforo: 🟢 ≤60 días · 🟡 60-150 · '
            '🔴 &gt;150</div>')
    ui.tabla(["Marca", "Año", "Modelo", "Ingreso", "Costo", "Venta",
              "Precio liqui", "Ganancia esp.", "Publicado"], filas,
             clases_col=["", "", "", "", "num", "num", "num", "num", ""],
             scroll=True)


def _trabados(inv: dict) -> None:
    ui.html('<div class="warning-banner"><strong>Capital trabado</strong>: '
            'vehículos que no rotan y requieren acción para rebolear.</div>')
    filas = [[v["vehiculo"], fmt_usd(v["valor_usd"])]
             for v in inv["vehiculos_trabados"]]
    filas.append(["<strong>TOTAL</strong>",
                  cs(fmt_usd(inv["totales"]["trabados"]), "warn")])
    ui.tabla(["Vehículo", "Valor USD"], filas, clases_col=["", "num"])


def _ventas(inv: dict) -> None:
    t = inv["totales"]
    ventas = inv["ventas_historicas"]
    if t["ventas_meses_sin_cargar"]:
        ui.html('<div class="warning-banner"><strong>Ganancias no cargadas:'
                f'</strong> {", ".join(t["ventas_meses_sin_cargar"])}. Los '
                'gráficos y promedios solo consideran meses con datos.</div>')
    else:
        ui.html('<div class="accent-banner">Todos los meses con ganancia '
                'cargada.</div>')
    meses_c = t["ventas_meses_cargados"] or 1
    ui.grid([
        ui.metric_card(f"Total ventas ({len(ventas)} meses)",
                       str(t["ventas_cantidad_total"])),
        ui.metric_card("Meses cargados",
                       f"{t['ventas_meses_cargados']} / {len(ventas)}"),
        ui.metric_card("Ganancia total cargada",
                       fmt_usd(t["ventas_ganancia_total_cargada"])),
        ui.metric_card("Promedio / mes",
                       fmt_usd(t["ventas_ganancia_total_cargada"] / meses_c)),
    ])
    x = [f"{v['mes']} {v['anio']}" for v in ventas]
    fig1 = go.Figure(go.Bar(
        x=x, y=[v["cantidad"] for v in ventas],
        marker_color=["#00ff88" if v["ganancia_cargada"] else "#666"
                      for v in ventas],
        text=[v["cantidad"] for v in ventas], textposition="outside"))
    ui.html('<div class="rc-h3">Cantidad de ventas por mes</div>')
    ui.plot(fig1, height=300)

    cg = [v for v in ventas if v["ganancia_cargada"]]
    fig2 = go.Figure(go.Bar(
        x=[f"{v['mes']} {v['anio']}" for v in cg],
        y=[v["ganancia_usd"] for v in cg], marker_color="#ffaa00",
        text=[fmt_usd(v["ganancia_usd"]) for v in cg],
        textposition="outside"))
    ui.html('<div class="rc-h3">Ganancia mensual (meses cargados)</div>')
    ui.plot(fig2, height=300)

    filas = []
    for v in ventas:
        if v["ganancia_cargada"]:
            g = fmt_usd(v["ganancia_usd"])
            pu = fmt_usd(v["ganancia_usd"] / v["cantidad"]) if v["cantidad"] else "—"
        else:
            g, pu = '<span class="dim">no cargada</span>', '<span class="dim">—</span>'
        filas.append([v["mes"], str(v["anio"]), str(v["cantidad"]), g, pu])
    ui.tabla(["Mes", "Año", "Cantidad", "Ganancia USD", "$/vehículo"], filas,
             clases_col=["", "", "num", "num", "num"])


def render(ctx: dict) -> None:
    inv = ctx["inv"]
    ui.html('<div class="rc-h2">Stock & ventas</div>'
            '<div class="fuente">Fuente: planilla <code>inversion</code></div>')
    s1, s2, s3 = st.tabs(["Stock activo", "Trabados", "Ventas históricas"])
    with s1:
        _stock_activo(inv)
    with s2:
        _trabados(inv)
    with s3:
        _ventas(inv)
