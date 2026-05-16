"""Tab 9 · Análisis Financiero (la sección crítica)."""
from __future__ import annotations

import plotly.graph_objects as go

from racing import analisis, ui
from racing.formato import fmt_usd
from racing.ui import color_span as cs


def render(ctx: dict) -> None:
    inv, pc, caja = ctx["inv"], ctx["pc"], ctx["caja"]
    caja_usd = caja["usd"]["saldo_actual"]
    a = analisis.analisis_completo(inv, pc, caja_usd)
    base = a["base"]

    ui.html('<div class="rc-h2">Análisis Financiero</div>'
            '<div class="fuente">KPIs derivados del costo de los inversores, '
            'gastos fijos y dinámica del stock.</div>'
            f'<div class="accent-banner"><strong>Premisa clave:</strong> el '
            f'negocio paga <strong>{fmt_usd(base["interes_mensual"])}/mes</strong> '
            f'de intereses sobre <strong>'
            f'{fmt_usd(inv["totales"]["acreedores"])}</strong> de capital '
            f'prestado. Cada decisión tiene que cubrir ese costo antes de '
            f'generar ganancia real.</div>')

    # 1. COSTO FINANCIERO
    cf = a["costo_financiero"]
    ui.html('<div class="rc-h3">1. Costo financiero vs ganancia</div>')
    ui.grid([
        ui.metric_card("Interés mensual",
                       cs(fmt_usd(base["interes_mensual"]), "neg"),
                       f"Sobre {fmt_usd(inv['totales']['acreedores'])} prestados",
                       "dim"),
        ui.metric_card("Ganancia bruta prom/mes",
                       cs(fmt_usd(base["ganancia_prom_mes"]), "pos"),
                       f"Sobre {base['meses_cargados']} meses", "dim"),
        ui.metric_card("% comido por intereses",
                       cs(f'{cf["pct_comido"]:.1f}%',
                          "neg" if cf["pct_comido"] > 30 else "warn"),
                       "Alto" if cf["pct_comido"] > 30 else "Aceptable",
                       "negative" if cf["pct_comido"] > 30 else "warning"),
        ui.metric_card("Ganancia neta real/mes",
                       cs(fmt_usd(cf["ganancia_neta_mes"]),
                          "neg" if cf["ganancia_neta_mes"] < 0 else "pos"),
                       "Bruta - intereses - gastos fijos", "dim"),
    ])
    filas = [[ac["nombre"], fmt_usd(ac["monto_usd"]), f'{ac["interes_pct"]}%',
              cs(fmt_usd(ac["interes_mensual_usd"]), "neg"),
              f'{ac["interes_mensual_usd"]/base["interes_mensual"]*100:.1f}%'
              if base["interes_mensual"] else "—"]
             for ac in cf["acreedores"]]
    filas.append(["<strong>TOTAL</strong>",
                  fmt_usd(cf["total_capital_int"]), "—",
                  cs(fmt_usd(base["interes_mensual"]), "neg"), "100%"])
    ui.html('<div class="rc-h3">Costo financiero mensual por acreedor</div>')
    ui.tabla(["Acreedor", "Capital USD", "Tasa", "Interés/mes USD",
              "% del total"], filas,
             clases_col=["", "num", "num", "num", "num"])

    # 2. PUNTO DE EQUILIBRIO
    pe = a["punto_equilibrio"]
    ui.html('<div class="rc-h3">2. Punto de equilibrio</div>')
    ui.grid([
        ui.metric_card("Costo total mensual",
                       cs(fmt_usd(base["costo_total_mes"]), "neg"),
                       f"Gastos {fmt_usd(base['gastos_fijos'])} + Intereses "
                       f"{fmt_usd(base['interes_mensual'])}", "dim"),
        ui.metric_card("Margen prom. por auto",
                       fmt_usd(base["margen_por_auto"]), None, "dim"),
        ui.metric_card("Autos para empatar",
                       cs(f'{pe["autos_breakeven"]}/mes',
                          "neg" if pe["diff"] < 0 else "pos"),
                       "Para cubrir el costo fijo", "dim"),
        ui.metric_card("Venta prom. actual",
                       cs(f'{pe["autos_actuales"]:.1f}/mes',
                          "pos" if pe["diff"] > 0 else "neg"),
                       (f'+{pe["diff"]:.1f} arriba' if pe["diff"] > 0
                        else f'{pe["diff"]:.1f} por debajo'),
                       "pos" if pe["diff"] > 0 else "negative"),
    ])
    filas = [[f'<strong>{e["label"]}</strong>', str(e["autos"]),
              fmt_usd(e["bruta"]), cs(fmt_usd(-base["costo_total_mes"]), "neg"),
              cs(fmt_usd(e["neta"]), "pos" if e["neta"] >= 0 else "neg")]
             for e in pe["escenarios"]]
    ui.html('<div class="rc-h3">¿Cuántos autos hay que vender por mes?</div>')
    ui.tabla(["Escenario", "Autos/mes", "Ganancia bruta", "- Costos fijos",
              "Ganancia neta"], filas,
             clases_col=["", "num", "num", "num", "num"])

    # 3. TRABADOS
    tr = a["trabados"]
    ui.html('<div class="rc-h3">3. Capital atrapado: vehículos trabados</div>')
    ui.grid([
        ui.metric_card("Capital trabado", cs(fmt_usd(tr["capital"]), "neg"),
                       f'{tr["unidades"]} unidades', "dim"),
        ui.metric_card("% del capital total", f'{tr["pct_capital"]:.1f}%',
                       "Sobre stock + trabados", "dim"),
        ui.metric_card("Costo de oportunidad/mes",
                       cs(fmt_usd(tr["costo_op_mes"]), "neg"),
                       f"Al {analisis.TASA_PROM_ACREEDORES}% mensual", "negative"),
        ui.metric_card("Costo anualizado",
                       cs(fmt_usd(tr["costo_op_anual"]), "neg"),
                       "Si no se destraban", "negative"),
    ])
    filas = [[v["vehiculo"], fmt_usd(v["valor_usd"]),
              cs(fmt_usd(v["costo_mes"]), "neg"),
              cs(fmt_usd(v["costo_anual"]), "neg")] for v in tr["detalle"]]
    filas.append(["<strong>TOTAL</strong>", fmt_usd(tr["capital"]),
                  cs(fmt_usd(tr["costo_op_mes"]), "neg"),
                  cs(fmt_usd(tr["costo_op_anual"]), "neg")])
    ui.tabla(["Vehículo", "Valor USD", "Costo oport./mes", "Costo anual"],
             filas, clases_col=["", "num", "num", "num"])

    # 4. ROTACIÓN
    ro = a["rotacion"]
    ui.html('<div class="rc-h3">4. Rotación de stock</div>')
    ui.grid([
        ui.metric_card("Días promedio en stock",
                       f'{round(ro["dias_prom"])}',
                       f'{len(ro["items"])} vehículos con fecha', "dim"),
        ui.metric_card("Frescos (<60d)", cs(str(len(ro["verdes"])), "pos"),
                       f'{fmt_usd(sum(v["costo"] for v in ro["verdes"]))} costo',
                       "pos"),
        ui.metric_card("Estancados (60-120d)",
                       cs(str(len(ro["amarillos"])), "warn"),
                       f'{fmt_usd(sum(v["costo"] for v in ro["amarillos"]))} '
                       f'costo', "warning"),
        ui.metric_card("Críticos (>120d)", cs(str(len(ro["rojos"])), "neg"),
                       f'{fmt_usd(sum(v["costo"] for v in ro["rojos"]))} '
                       f'inmovilizado', "negative"),
    ])
    filas = []
    for s in ro["items"]:
        emoji = "🔴" if s["dias"] > 120 else "🟡" if s["dias"] > 60 else "🟢"
        clr = "neg" if s["dias"] > 120 else "warn" if s["dias"] > 60 else "pos"
        fi = "/".join(reversed(s["fecha_ingreso"].split("-")))
        filas.append([f'{s["marca"]} {s["modelo"]} {s["anio"] or ""}', fi,
                      cs(str(s["dias"]), clr), fmt_usd(s["costo"]),
                      f'{s["margen_pct"]:.1f}%', emoji])
    ui.tabla(["Vehículo", "Ingreso", "Días", "Costo USD", "Margen %",
              "Estado"], filas,
             clases_col=["", "", "num", "num", "num", ""], scroll=True)

    # 5. DISTRIBUCIÓN CAPITAL
    di = a["distribucion"]
    tot = di["total"] or 1
    ui.html('<div class="rc-h3">5. Distribución de capital</div>')
    ui.grid([
        ui.metric_card("Capital total operativo", fmt_usd(di["total"]),
                       "Stock + trabados + caja USD", "dim"),
        ui.metric_card("Stock productivo",
                       cs(fmt_usd(di["stock_publicado"]), "pos"),
                       f'{di["stock_publicado"]/tot*100:.0f}% · publicado',
                       "pos"),
        ui.metric_card("Stock parado",
                       cs(fmt_usd(di["stock_no_publicado"]), "warn"),
                       f'{di["stock_no_publicado"]/tot*100:.0f}% no publicado',
                       "warning"),
        ui.metric_card("Trabados", cs(fmt_usd(di["trabados"]), "neg"),
                       f'{di["trabados"]/tot*100:.0f}% sin liquidez',
                       "negative"),
    ])
    fig = go.Figure(go.Pie(
        labels=["Stock publicado", "Stock no publicado", "Trabados",
                "Caja USD"],
        values=[di["stock_publicado"], di["stock_no_publicado"],
                di["trabados"], di["caja_usd"]],
        hole=0.55, marker=dict(colors=["#00ff88", "#ffaa00", "#ff4444",
                                       "#888"]),
        textinfo="label+percent", textfont=dict(color="#0a0a0a", size=13),
        hovertemplate="<b>%{label}</b><br>USD %{value:,.0f}<br>%{percent}"
                      "<extra></extra>"))
    fig.update_layout(showlegend=False)
    ui.html('<div class="rc-h3">¿Dónde está la plata?</div>')
    ui.plot(fig, height=360)

    # 6. CALENDARIO NETO USD
    cn = a["calendario_neto"]
    ui.html('<div class="rc-h3">6. Calendario neto: cobros vs pagos '
            '(próximos 6 meses)</div>')
    fig = go.Figure()
    fig.add_bar(x=[d["label"] for d in cn], y=[d["cobros"] for d in cn],
                name="Cobros", marker_color="#00ff88")
    fig.add_bar(x=[d["label"] for d in cn], y=[-d["pagos"] for d in cn],
                name="Pagos", marker_color="#ff4444")
    fig.add_scatter(x=[d["label"] for d in cn], y=[d["neto"] for d in cn],
                    name="Neto", mode="lines+markers",
                    line=dict(color="#ffaa00", width=3))
    fig.update_layout(barmode="relative", hovermode="x unified")
    ui.plot(fig, height=360)
    filas = [[f'<strong>{d["label"]}</strong>', cs(fmt_usd(d["cobros"]), "pos"),
              cs(fmt_usd(d["pagos"]), "neg"),
              cs(fmt_usd(d["neto"]), "pos" if d["neto"] >= 0 else "neg"),
              cs(fmt_usd(d["acumulado"]),
                 "pos" if d["acumulado"] >= 0 else "neg")] for d in cn]
    ui.tabla(["Mes", "Cobros USD", "Pagos USD", "Neto", "Acumulado"], filas,
             clases_col=["", "num", "num", "num", "num"])
    ui.html('<div class="fuente">Pagos = cuotas a proveedores + intereses de '
            'acreedores + gastos fijos del mes.</div>')

    # 7. EVOLUCIÓN DEL STOCK
    ev = a["evolucion"]
    evol, k, et = ev["evolucion"], ev["kpis"], ev["econ_totales"]
    ui.html('<div class="rc-h3">7. Evolución del stock mes a mes</div>'
            '<div class="warning-banner"><strong>Por qué importa:</strong> '
            'aunque la caja USD del mes dé cerca de cero, si entraron autos '
            'vía permutas el patrimonio real creció.</div>')
    ui.grid([
        ui.metric_card("Stock actual", f'{k["stock_actual_cant"]} autos',
                       f'{fmt_usd(k["stock_actual_val"])} a costo', "dim"),
        ui.metric_card("Crecimiento últimos 6m",
                       cs(fmt_usd(k["crec_6m"]),
                          "pos" if k["crec_6m"] >= 0 else "neg"),
                       "Estimación con ventas inferidas", "dim"),
        ui.metric_card("Crecimiento últimos 12m",
                       cs(fmt_usd(k["crec_12m"]),
                          "pos" if k["crec_12m"] >= 0 else "neg"),
                       "Últimos 13 meses", "dim"),
        ui.metric_card("Crecimiento prom/mes",
                       cs(fmt_usd(k["prom_mensual"]),
                          "pos" if k["prom_mensual"] >= 0 else "neg"),
                       "En valor de stock", "dim"),
    ])
    fig = go.Figure()
    fig.add_bar(x=[e["label"] for e in evol], y=[e["cant_est"] for e in evol],
                name="Cant. (estimado)",
                marker_color="rgba(255,170,0,0.6)")
    fig.add_bar(x=[e["label"] for e in evol], y=[e["cant_sup"] for e in evol],
                name="Cant. (superviv.)",
                marker_color="rgba(0,255,136,0.8)")
    fig.add_scatter(x=[e["label"] for e in evol],
                    y=[e["val_est"] for e in evol], name="Valor estimado",
                    mode="lines+markers", yaxis="y2",
                    line=dict(color="#ffaa00", width=3, dash="dot"))
    fig.add_scatter(x=[e["label"] for e in evol],
                    y=[e["val_sup"] for e in evol], name="Valor superviv.",
                    mode="lines+markers", yaxis="y2",
                    line=dict(color="#00ff88", width=3))
    fig.update_layout(
        barmode="overlay", hovermode="x unified",
        yaxis=dict(title="Cantidad de autos", gridcolor="#222"),
        yaxis2=dict(title="Valor USD (costo)", overlaying="y", side="right",
                    gridcolor="#222", tickformat=",.0f"),
        legend=dict(orientation="h", y=-0.2))
    ui.html('<div class="rc-h3">Stock al cierre de cada mes</div>')
    ui.plot(fig, height=400)
    filas = []
    for i, e in enumerate(evol):
        dv = e["delta_val"]
        dcls = "pos" if dv > 0 else "neg" if dv < 0 else "dim"
        dtxt = "—" if i == 0 else fmt_usd(dv)
        filas.append([f'<strong>{e["label"]}</strong>', str(e["cant_sup"]),
                      cs(fmt_usd(e["val_sup"]), "pos"), str(e["cant_est"]),
                      cs(fmt_usd(e["val_est"]), "warn"), cs(dtxt, dcls)])
    ui.tabla(["Mes", "Stock superv.", "Valor superv.", "Stock estimado",
              "Valor estimado", "Δ vs mes anterior"], filas,
             clases_col=["", "num", "num", "num", "num", "num"], scroll=True)

    ui.html('<div class="accent-banner"><strong>Ganancia económica real'
            '</strong> = ganancia cash + Δ valor de stock (al costo). El '
            'verdadero indicador de cómo le fue al negocio.</div>')
    ui.grid([
        ui.metric_card("Ganancia cash acumulada",
                       cs(fmt_usd(et["cash"]), "pos"),
                       f'{len(ev["ganancia_economica"])} meses cargados',
                       "dim"),
        ui.metric_card("Δ valor stock acumulado",
                       cs(fmt_usd(et["delta"]),
                          "pos" if et["delta"] >= 0 else "neg"),
                       "Sumatoria de variaciones", "dim"),
        ui.metric_card("Ganancia económica total",
                       cs(fmt_usd(et["economica"]), "pos"),
                       f'{"+" if et["diff"] >= 0 else ""}{fmt_usd(et["diff"])} '
                       f'vs solo cash',
                       "pos" if et["diff"] >= 0 else "negative"),
        ui.metric_card("% no visible en cash",
                       cs(f'{et["pct_no_visible"]:.0f}%', "warn"),
                       'Ganancia "invisible" en stock', "warning"),
    ])
