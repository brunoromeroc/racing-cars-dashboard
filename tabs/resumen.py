"""Tab Resumen: salud financiera, pendientes, flujo, alertas, ventas."""
from __future__ import annotations

import plotly.graph_objects as go

from racing import ui
from racing.formato import fmt_ars, fmt_usd
from racing.ui import color_span as cs


def render(ctx: dict) -> None:
    caja, pc, inv = ctx["caja"], ctx["pc"], ctx["inv"]
    t = inv["totales"]
    saldo_ars = caja["pesos"]["saldo_actual"]
    saldo_usd = caja["usd"]["saldo_actual"]
    deuda_neta = (t["acreedores"] + pc["pagos_usd"]["total_pendiente"]
                  - pc["cobros_usd"]["total_pendiente"])
    deuda_neta_ars = (pc["pagos_ars"]["total_pendiente"]
                      - pc["cobros_ars"]["total_pendiente"])

    ui.html('<div class="rc-h2">Salud financiera</div>')
    ui.grid([
        ui.metric_card("Caja ARS",
                       cs(fmt_ars(saldo_ars), "pos" if saldo_ars >= 0 else "neg"),
                       "al límite" if saldo_ars < 100000 else None, "warning"),
        ui.metric_card("Caja USD",
                       cs(fmt_usd(saldo_usd), "pos" if saldo_usd >= 0 else "neg"),
                       "en rojo" if saldo_usd < 0 else None, "negative"),
        ui.metric_card("Stock activo (liqui)",
                       cs(fmt_usd(t["stock_liqui"]), "pos"),
                       f"Costo {fmt_usd(t['stock_costo'])} · {t['stock_count']} u.",
                       "dim"),
        ui.metric_card("Deuda neta USD",
                       cs(fmt_usd(deuda_neta), "neg" if deuda_neta >= 0 else "pos"),
                       "en contra" if deuda_neta >= 0 else "a favor",
                       "negative" if deuda_neta >= 0 else "dim"),
        ui.metric_card("Deuda neta ARS",
                       cs(fmt_ars(deuda_neta_ars),
                          "neg" if deuda_neta_ars >= 0 else "pos"),
                       "en contra" if deuda_neta_ars >= 0 else "a favor",
                       "negative" if deuda_neta_ars >= 0 else "dim"),
    ])

    ui.html('<div class="rc-h3">Pendientes</div>')
    ui.grid([
        ui.metric_card("Cobrar USD", cs(fmt_usd(pc["cobros_usd"]["total_pendiente"]), "pos")),
        ui.metric_card("Cobrar ARS", cs(fmt_ars(pc["cobros_ars"]["total_pendiente"]), "pos")),
        ui.metric_card("Pagar USD", cs(fmt_usd(pc["pagos_usd"]["total_pendiente"]), "neg")),
        ui.metric_card("Pagar ARS", cs(fmt_ars(pc["pagos_ars"]["total_pendiente"]), "neg")),
    ])

    meses_c = t["ventas_meses_cargados"] or 1
    prom = t["ventas_ganancia_total_cargada"] / meses_c
    flujo = prom - t["gastos_fijos"]
    ui.html('<div class="rc-h3">Flujo mensual</div>')
    ui.grid([
        ui.metric_card("Ganancia prom. mensual", fmt_usd(prom),
                       f"Sobre {t['ventas_meses_cargados']} meses cargados", "dim"),
        ui.metric_card("Gastos fijos mensuales", fmt_usd(t["gastos_fijos"])),
        ui.metric_card("Flujo neto estimado",
                       cs(fmt_usd(flujo), "neg" if flujo < 0 else "pos"),
                       "negativo" if flujo < 0 else None,
                       "negative" if flujo < 0 else ""),
    ])

    alertas = []
    if saldo_ars < 100000:
        alertas.append(("Caja ARS al límite", f"Saldo: {fmt_ars(saldo_ars)}"))
    if saldo_usd < 0:
        alertas.append(("Caja USD en rojo", f"Saldo: {fmt_usd(saldo_usd)}"))
    if t["trabados"] > 100000:
        alertas.append(("Capital trabado",
                         f"{fmt_usd(t['trabados'])} en "
                         f"{len(inv['vehiculos_trabados'])} vehículos"))
    if t["interes_mensual"] > 5000:
        alertas.append(("Costo financiero alto",
                         f"{fmt_usd(t['interes_mensual'])}/mes en intereses"))
    if t["ventas_meses_sin_cargar"]:
        alertas.append(("Ventas con ganancia sin cargar",
                         f"{len(t['ventas_meses_sin_cargar'])} meses: "
                         f"{', '.join(t['ventas_meses_sin_cargar'])}"))
    lis = "".join(
        f'<li><div class="alert-title">{a}</div>'
        f'<div class="alert-detail">{d}</div></li>' for a, d in alertas
    ) or '<li class="dim">Sin alertas activas</li>'
    ui.html(f'<div class="card"><div class="rc-h3">Alertas</div>'
            f'<ul class="alert-list">{lis}</ul></div>')

    ventas = inv["ventas_historicas"]
    if ventas:
        fig = go.Figure(go.Bar(
            x=[f"{v['mes']} {v['anio']}" for v in ventas],
            y=[v["cantidad"] for v in ventas],
            marker_color=["#00ff88" if v["ganancia_cargada"] else "#666"
                          for v in ventas],
            text=[v["cantidad"] for v in ventas], textposition="outside",
            hovertemplate="%{x}<br>%{y} ventas<extra></extra>"))
        ui.html('<div class="rc-h3">Cantidad de ventas mensuales</div>')
        ui.plot(fig, height=320)
        ui.html('<div class="fuente">Verde: mes con ganancia cargada · '
                'Gris: pendiente de cargar</div>')
