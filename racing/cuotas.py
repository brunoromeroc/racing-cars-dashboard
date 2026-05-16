"""
Logica de cuotas compartida entre Cobros, Pagos y Calendario.
Port de parseFechaCuota / renderDeudaCards / flujo del prototipo.
"""
from __future__ import annotations

from datetime import date

from .formato import mes_a_numero


def parse_fecha_cuota(c: dict) -> date | None:
    anio = c.get("Año")
    mes = mes_a_numero(c.get("Mes"))
    if not anio or not mes:
        return None
    dia = c.get("Dia") or 1
    try:
        return date(int(anio), int(mes), int(dia))
    except (ValueError, TypeError):
        try:
            return date(int(anio), int(mes), 1)
        except (ValueError, TypeError):
            return None


def agrupar_deuda(detalle: list[dict], hoy: date | None = None) -> dict:
    """
    Agrupa por Cliente+Vehiculo y clasifica en vencidos / pendientes /
    realizados (misma logica que las cards del prototipo).
    """
    hoy = hoy or date.today()
    grupos: dict[str, dict] = {}
    for r in detalle:
        cliente = (r.get("Cliente") or "").strip()
        if not cliente:
            continue
        veh = (r.get("Veiculo") or "").strip() or "(sin vehículo)"
        k = f"{cliente}||{veh}"
        grupos.setdefault(k, {"cliente": cliente, "vehiculo": veh, "cuotas": []})
        grupos[k]["cuotas"].append(r)

    out = []
    for g in grupos.values():
        cuotas = g["cuotas"]
        pendiente = sum(c.get("Cuota Pendiente", 0) or 0 for c in cuotas)
        pagado = sum(c.get("Cuota Abonada", 0) or 0 for c in cuotas)
        pagas = sum(1 for c in cuotas
                    if (c.get("Cuota Abonada", 0) or 0) > 0
                    and (c.get("Cuota Pendiente", 0) or 0) == 0)
        pendientes = [c for c in cuotas if (c.get("Cuota Pendiente", 0) or 0) > 0]
        vencidas, prox_fecha = 0, None
        for c in pendientes:
            f = parse_fecha_cuota(c)
            if f:
                if f < hoy:
                    vencidas += 1
                if prox_fecha is None or f < prox_fecha:
                    prox_fecha = f
        if not pendientes:
            categoria = "realizados"
        elif vencidas > 0:
            categoria = "vencidos"
        else:
            categoria = "pendientes"
        dias_prox = ((prox_fecha - hoy).days
                     if categoria == "pendientes" and prox_fecha else None)
        out.append({
            **g, "pendiente": pendiente, "pagado": pagado, "pagas": pagas,
            "pend_count": len(pendientes), "vencidas": vencidas,
            "total_cuotas": len(cuotas), "categoria": categoria,
            "proxima_fecha": prox_fecha, "dias_proximo": dias_prox,
        })

    def _ord(gs):
        return sorted(gs, key=lambda x: (x["pagado"] if x["categoria"]
                      == "realizados" else x["pendiente"]), reverse=True)

    venc = _ord([g for g in out if g["categoria"] == "vencidos"])
    pend = _ord([g for g in out if g["categoria"] == "pendientes"])
    real = _ord([g for g in out if g["categoria"] == "realizados"])
    return {
        "vencidos": venc, "pendientes": pend, "realizados": real,
        "total_vencidos": sum(g["pendiente"] for g in venc),
        "total_pendientes": sum(g["pendiente"] for g in pend),
        "total_realizados": sum(g["pagado"] for g in real),
    }


def flujo_por_mes(cobros_det: list[dict], pagos_det: list[dict]) -> list[dict]:
    """
    Cuotas pendientes con fecha, agrupadas por (anio, mes). Devuelve filas
    ordenadas con cobros, pagos, neto y acumulado. No suma gastos/intereses.
    """
    meses: dict[tuple, dict] = {}

    def add(det, campo):
        for c in det:
            if (c.get("Cuota Pendiente", 0) or 0) <= 0:
                continue
            f = parse_fecha_cuota(c)
            if not f:
                continue
            k = (f.year, f.month)
            meses.setdefault(k, {"cobros": 0.0, "pagos": 0.0})
            meses[k][campo] += c["Cuota Pendiente"]

    add(cobros_det, "cobros")
    add(pagos_det, "pagos")

    filas, acum = [], 0.0
    for (y, m) in sorted(meses):
        cob = meses[(y, m)]["cobros"]
        pag = meses[(y, m)]["pagos"]
        neto = cob - pag
        acum += neto
        filas.append({"anio": y, "mes": m, "cobros": cob, "pagos": pag,
                      "neto": neto, "acumulado": acum})
    return filas


def eventos_del_mes(cobros_det, pagos_det, anio: int, mes: int) -> list[dict]:
    ev = []
    for det, tipo in ((cobros_det, "Cobro"), (pagos_det, "Pago")):
        for c in det:
            if (c.get("Cuota Pendiente", 0) or 0) <= 0:
                continue
            f = parse_fecha_cuota(c)
            if not f or f.year != anio or f.month != mes:
                continue
            ev.append({
                "dia": f.day, "tipo": tipo,
                "nombre": (c.get("Cliente") or "").strip(),
                "vehiculo": (c.get("Veiculo") or "").strip(),
                "cuota": c.get("Cuotas") or "",
                "monto": c["Cuota Pendiente"],
            })
    return sorted(ev, key=lambda e: e["dia"])
