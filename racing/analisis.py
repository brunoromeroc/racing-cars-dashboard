"""
Logica del tab 9 (Analisis Financiero). Port fiel del renderAnalisisFinanciero
del prototipo HTML, como funciones puras que devuelven datos (la UI los pinta).

Las fechas son dinamicas (date.today()), no hardcodeadas como en el prototipo
estatico: "dias en stock" y los "proximos 6 meses" siempre relativos a hoy.
"""
from __future__ import annotations

from datetime import date
from dateutil.relativedelta import relativedelta

from .formato import MESES_NOMBRE, mes_a_numero

TASA_PROM_ACREEDORES = 1.5  # % mensual ponderado de acreedores con interes


def _fecha(iso: str) -> date | None:
    if not iso:
        return None
    try:
        y, m, d = map(int, iso.split("-"))
        return date(y, m, d)
    except (ValueError, AttributeError):
        return None


def metricas_base(inv: dict) -> dict:
    t = inv["totales"]
    ventas = inv["ventas_historicas"]
    cargadas = [v for v in ventas if v["ganancia_cargada"] and v["ganancia_usd"]]

    gan_prom_mes = (sum(v["ganancia_usd"] for v in cargadas) / len(cargadas)
                    if cargadas else 0.0)
    grandes = [v for v in ventas if v["cantidad"] >= 5]
    ventas_prom_mes = (sum(v["cantidad"] for v in grandes) / len(grandes)
                       if grandes else 0.0)
    cant_prom_cargadas = (sum(v["cantidad"] for v in cargadas) / len(cargadas)
                          if cargadas else 0.0)
    margen_por_auto = (gan_prom_mes / cant_prom_cargadas
                       if cant_prom_cargadas else 0.0)

    return {
        "interes_mensual": t["interes_mensual"],
        "gastos_fijos": t["gastos_fijos"],
        "costo_total_mes": t["interes_mensual"] + t["gastos_fijos"],
        "ganancia_prom_mes": gan_prom_mes,
        "ventas_prom_mes": ventas_prom_mes,
        "margen_por_auto": margen_por_auto,
        "meses_cargados": len(cargadas),
    }


def costo_financiero(inv: dict, base: dict) -> dict:
    im = base["interes_mensual"]
    gp = base["ganancia_prom_mes"]
    acre = sorted(
        [a for a in inv["acreedores"] if a["interes_mensual_usd"] > 0],
        key=lambda a: a["interes_mensual_usd"], reverse=True,
    )
    return {
        "pct_comido": (im / gp * 100) if gp else 0.0,
        "ganancia_neta_mes": gp - im - base["gastos_fijos"],
        "acreedores": acre,
        "total_capital_int": sum(a["monto_usd"] for a in acre),
    }


def punto_equilibrio(base: dict) -> dict:
    margen = base["margen_por_auto"]
    costo = base["costo_total_mes"]
    autos_be = -(-costo // margen) if margen else 0  # ceil
    autos_be = int(autos_be)
    actual = base["ventas_prom_mes"]
    escenarios = [
        {"label": "Empate", "autos": autos_be},
        {"label": "+20%", "autos": int(-(-(autos_be * 1.2) // 1))},
        {"label": "+50%", "autos": int(-(-(autos_be * 1.5) // 1))},
        {"label": "Actual", "autos": round(actual)},
    ]
    for e in escenarios:
        e["bruta"] = e["autos"] * margen
        e["neta"] = e["bruta"] - costo
    return {
        "autos_breakeven": autos_be,
        "autos_actuales": actual,
        "diff": actual - autos_be,
        "escenarios": escenarios,
    }


def trabados(inv: dict) -> dict:
    t = inv["totales"]
    cap = t["trabados"]
    costo_mes = cap * (TASA_PROM_ACREEDORES / 100)
    base_cap = t["stock_liqui"] + cap
    detalle = [
        {**v, "costo_mes": v["valor_usd"] * (TASA_PROM_ACREEDORES / 100),
         "costo_anual": v["valor_usd"] * (TASA_PROM_ACREEDORES / 100) * 12}
        for v in inv["vehiculos_trabados"]
    ]
    return {
        "capital": cap,
        "unidades": len(inv["vehiculos_trabados"]),
        "pct_capital": (cap / base_cap * 100) if base_cap else 0.0,
        "costo_op_mes": costo_mes,
        "costo_op_anual": costo_mes * 12,
        "detalle": detalle,
    }


def rotacion(inv: dict, hoy: date | None = None) -> dict:
    hoy = hoy or date.today()
    items = []
    for s in inv["stock_activo"]:
        fi = _fecha(s["fecha_ingreso"])
        if not fi:
            continue
        dias = (hoy - fi).days
        margen_pct = ((s["liqui"] - s["costo"]) / s["costo"] * 100
                      if s["costo"] > 0 else 0.0)
        items.append({**s, "dias": dias, "margen_pct": margen_pct})
    items.sort(key=lambda x: x["dias"], reverse=True)
    rojos = [s for s in items if s["dias"] > 120]
    amar = [s for s in items if 60 < s["dias"] <= 120]
    verdes = [s for s in items if s["dias"] <= 60]
    dias_prom = sum(s["dias"] for s in items) / len(items) if items else 0
    return {
        "items": items, "rojos": rojos, "amarillos": amar, "verdes": verdes,
        "dias_prom": dias_prom,
    }


def distribucion_capital(inv: dict, caja_usd: float) -> dict:
    stock = inv["stock_activo"]
    pub = sum(s["costo"] for s in stock if s["publi"])
    nopub = sum(s["costo"] for s in stock if not s["publi"])
    trab = inv["totales"]["trabados"]
    caja = max(caja_usd, 0)
    total = pub + nopub + trab + caja
    return {
        "stock_publicado": pub, "stock_no_publicado": nopub,
        "trabados": trab, "caja_usd": caja, "total": total,
    }


def calendario_neto(inv: dict, pc: dict, base: dict,
                     hoy: date | None = None) -> list[dict]:
    hoy = hoy or date.today()

    def por_mes(detalle):
        m = {}
        for c in detalle:
            if c["Cuota Pendiente"] > 0:
                num = mes_a_numero(c["Mes"])
                if not num or not c["Año"]:
                    continue
                k = f"{c['Año']}-{num:02d}"
                m[k] = m.get(k, 0) + c["Cuota Pendiente"]
        return m

    cobros = por_mes(pc["cobros_usd"]["detalle"])
    pagos = por_mes(pc["pagos_usd"]["detalle"])
    fijo = base["interes_mensual"] + base["gastos_fijos"]

    out, acum = [], 0.0
    cur = date(hoy.year, hoy.month, 1)
    for _ in range(6):
        k = f"{cur.year}-{cur.month:02d}"
        cob = cobros.get(k, 0)
        pag = pagos.get(k, 0) + fijo
        neto = cob - pag
        acum += neto
        out.append({
            "label": f"{MESES_NOMBRE[cur.month][:3]} {str(cur.year)[2:]}",
            "cobros": cob, "pagos": pag, "neto": neto, "acumulado": acum,
        })
        cur += relativedelta(months=1)
    return out


def evolucion_stock(inv: dict, hoy: date | None = None) -> dict:
    hoy = hoy or date.today()
    stock_cc = [s for s in inv["stock_activo"]
                if s["costo"] > 0 and s["fecha_ingreso"]]
    costo_prom = (sum(s["costo"] for s in stock_cc) / len(stock_cc)
                  if stock_cc else 0.0)

    # 13 meses hasta el mes actual (inclusive)
    periodos = []
    base_mes = date(hoy.year, hoy.month, 1)
    for i in range(12, -1, -1):
        d = base_mes - relativedelta(months=i)
        cierre = (date(d.year, d.month, 1) + relativedelta(months=1)
                  - relativedelta(days=1))
        periodos.append({"anio": d.year, "mes": d.month,
                          "label": f"{MESES_NOMBRE[d.month][:3]} {str(d.year)[2:]}",
                          "cierre": cierre})

    evol = []
    for p in periodos:
        sob = [s for s in stock_cc if _fecha(s["fecha_ingreso"]) <= p["cierre"]]
        cant_sup = len(sob)
        val_sup = sum(s["costo"] for s in sob)
        v_post = 0
        for v in inv["ventas_historicas"]:
            mv = mes_a_numero(v["mes"])
            if not mv:
                continue
            fv = date(v["anio"], mv, 1)
            if fv > p["cierre"]:
                v_post += v["cantidad"]
        cant_est = cant_sup + v_post
        val_est = val_sup + v_post * costo_prom
        evol.append({**p, "cant_sup": cant_sup, "val_sup": val_sup,
                     "cant_est": cant_est, "val_est": val_est})
    for i, e in enumerate(evol):
        e["delta_val"] = 0.0 if i == 0 else e["val_est"] - evol[i - 1]["val_est"]

    ult = evol[-1] if evol else None
    pri = evol[0] if evol else None
    hace6 = evol[-7] if len(evol) >= 7 else (evol[0] if evol else None)
    prom_delta = (sum(e["delta_val"] for e in evol[1:]) / (len(evol) - 1)
                  if len(evol) > 1 else 0.0)

    ganancia_economica = []
    for v in inv["ventas_historicas"]:
        if not (v["ganancia_cargada"] and v["ganancia_usd"]):
            continue
        mv = mes_a_numero(v["mes"])
        if not mv:
            continue
        evo = next((e for e in evol if e["anio"] == v["anio"]
                    and e["mes"] == mv), None)
        if not evo:
            continue
        ganancia_economica.append({
            "label": f"{str(v['mes'])[:3]} {str(v['anio'])[2:]}",
            "cash": v["ganancia_usd"],
            "delta_stock": evo["delta_val"],
            "economica": v["ganancia_usd"] + evo["delta_val"],
        })

    tot_cash = sum(g["cash"] for g in ganancia_economica)
    tot_delta = sum(g["delta_stock"] for g in ganancia_economica)
    return {
        "evolucion": evol,
        "kpis": {
            "stock_actual_cant": ult["cant_sup"] if ult else 0,
            "stock_actual_val": ult["val_sup"] if ult else 0,
            "crec_6m": (ult["val_est"] - hace6["val_est"]) if ult and hace6 else 0,
            "crec_12m": (ult["val_est"] - pri["val_est"]) if ult and pri else 0,
            "prom_mensual": prom_delta,
        },
        "ganancia_economica": ganancia_economica,
        "econ_totales": {
            "cash": tot_cash,
            "delta": tot_delta,
            "economica": tot_cash + tot_delta,
            "diff": tot_delta,
            "pct_no_visible": (tot_delta / tot_cash * 100) if tot_cash > 0 else 0,
        },
    }


def analisis_completo(inv: dict, pc: dict, caja_usd: float) -> dict:
    base = metricas_base(inv)
    return {
        "base": base,
        "costo_financiero": costo_financiero(inv, base),
        "punto_equilibrio": punto_equilibrio(base),
        "trabados": trabados(inv),
        "rotacion": rotacion(inv),
        "distribucion": distribucion_capital(inv, caja_usd),
        "calendario_neto": calendario_neto(inv, pc, base),
        "evolucion": evolucion_stock(inv),
    }
