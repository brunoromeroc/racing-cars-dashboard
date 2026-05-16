"""
Parser de la planilla 'inversion'. La planilla cruda es inparseable, asi que
Racing Cars mantiene en ella TABS ESTRUCTURADAS con columnas fijas (las crea
tools/seed_inversion.py). Esquema:

  Acreedores  : nombre | monto_usd | interes_pct | interes_mensual_usd | ultima_fecha_pago
  GastosFijos : concepto | monto_usd
  Trabados    : vehiculo | valor_usd
  Stock       : marca | anio | modelo | costo | venta | liqui | publi | fecha_ingreso
  Ventas      : mes | anio | cantidad | ganancia_usd | ganancia_cargada
  Comisiones  : persona | concepto | monto         (persona = santi|jose)
  Retiros     : descripcion | fecha | monto_usd

Devuelve un dict con la forma del DATA.inv del prototipo (claves ASCII).
"""
from __future__ import annotations

import pandas as pd

from . import sheets
from .formato import mes_a_numero

# Prefijo de las tabs del dashboard, para no colisionar con las hojas crudas
# de la planilla (STOCK, VENTAS, etc.) ni confundir a quien la edita.
PREFIJO = "Dash_"
TABS = ["Acreedores", "GastosFijos", "Trabados", "Stock", "Ventas",
        "Comisiones", "Retiros"]

_VERDADERO = {"true", "verdadero", "si", "sí", "x", "1", "1.0", "yes"}


def _tab(nombre: str) -> pd.DataFrame:
    df = sheets.read_tabla("inversion", PREFIJO + nombre, header_row=0)
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df.dropna(how="all")


def _num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0.0)


def _bool(v) -> bool:
    return str(v).strip().lower() in _VERDADERO


def _fecha_iso(v):
    d = pd.to_datetime(v, errors="coerce", dayfirst=True)
    return None if pd.isna(d) else d.strftime("%Y-%m-%d")


def cargar_inversion() -> dict:
    inv = {"acreedores": [], "gastos_fijos": [], "vehiculos_trabados": [],
           "stock_activo": [], "ventas_historicas": [], "retiros": [],
           "comisiones_santi": [], "comisiones_jose": [], "errores": []}
    tablas = {}
    for t in TABS:
        try:
            tablas[t] = _tab(t)
        except Exception as e:  # noqa: BLE001  (tab faltante = setup pendiente)
            tablas[t] = pd.DataFrame()
            inv["errores"].append(f"{t}: {e}")

    a = tablas["Acreedores"]
    if len(a):
        a["monto_usd"] = _num(a.get("monto_usd"))
        a["interes_pct"] = _num(a.get("interes_pct"))
        a["interes_mensual_usd"] = _num(a.get("interes_mensual_usd"))
        for _, r in a.iterrows():
            if not str(r.get("nombre", "")).strip():
                continue
            inv["acreedores"].append({
                "nombre": str(r["nombre"]).strip(),
                "monto_usd": float(r["monto_usd"]),
                "interes_pct": float(r["interes_pct"]),
                "interes_mensual_usd": float(r["interes_mensual_usd"]),
                "ultima_fecha_pago": _fecha_iso(r.get("ultima_fecha_pago")),
            })

    g = tablas["GastosFijos"]
    if len(g):
        g["monto_usd"] = _num(g.get("monto_usd"))
        for _, r in g.iterrows():
            if str(r.get("concepto", "")).strip():
                inv["gastos_fijos"].append({
                    "concepto": str(r["concepto"]).strip(),
                    "monto_usd": float(r["monto_usd"]),
                })

    tr = tablas["Trabados"]
    if len(tr):
        tr["valor_usd"] = _num(tr.get("valor_usd"))
        for _, r in tr.iterrows():
            if str(r.get("vehiculo", "")).strip():
                inv["vehiculos_trabados"].append({
                    "vehiculo": str(r["vehiculo"]).strip(),
                    "valor_usd": float(r["valor_usd"]),
                })

    s = tablas["Stock"]
    if len(s):
        for c in ["anio", "costo", "venta", "liqui"]:
            s[c] = _num(s.get(c))
        for _, r in s.iterrows():
            if not str(r.get("modelo", "")).strip() and not str(r.get("marca", "")).strip():
                continue
            inv["stock_activo"].append({
                "marca": str(r.get("marca", "")).strip(),
                "anio": int(r["anio"]) if r["anio"] else None,
                "modelo": str(r.get("modelo", "")).strip(),
                "costo": float(r["costo"]),
                "venta": float(r["venta"]),
                "liqui": float(r["liqui"]),
                "publi": _bool(r.get("publi")),
                "fecha_ingreso": _fecha_iso(r.get("fecha_ingreso")),
            })

    v = tablas["Ventas"]
    if len(v):
        v["cantidad"] = _num(v.get("cantidad"))
        v["ganancia_usd"] = _num(v.get("ganancia_usd"))
        for _, r in v.iterrows():
            if not str(r.get("mes", "")).strip():
                continue
            inv["ventas_historicas"].append({
                "mes": str(r["mes"]).strip(),
                "anio": int(pd.to_numeric(r.get("anio"), errors="coerce") or 0),
                "cantidad": int(r["cantidad"]),
                "ganancia_usd": float(r["ganancia_usd"]),
                "ganancia_cargada": _bool(r.get("ganancia_cargada")),
            })

    cm = tablas["Comisiones"]
    if len(cm):
        cm["monto"] = _num(cm.get("monto"))
        for _, r in cm.iterrows():
            persona = str(r.get("persona", "")).strip().lower()
            item = {"concepto": str(r.get("concepto", "")).strip(),
                    "monto": float(r["monto"])}
            if persona == "santi":
                inv["comisiones_santi"].append(item)
            elif persona == "jose":
                inv["comisiones_jose"].append(item)

    rt = tablas["Retiros"]
    if len(rt):
        rt["monto_usd"] = _num(rt.get("monto_usd"))
        for _, r in rt.iterrows():
            if str(r.get("descripcion", "")).strip():
                inv["retiros"].append({
                    "descripcion": str(r["descripcion"]).strip(),
                    "fecha": _fecha_iso(r.get("fecha")),
                    "monto_usd": float(r["monto_usd"]),
                })

    inv["totales"] = _totales(inv)
    return inv


def _totales(inv: dict) -> dict:
    acreedores = sum(a["monto_usd"] for a in inv["acreedores"])
    interes_mensual = sum(a["interes_mensual_usd"] for a in inv["acreedores"])
    gastos_fijos = sum(x["monto_usd"] for x in inv["gastos_fijos"])
    trabados = sum(x["valor_usd"] for x in inv["vehiculos_trabados"])
    stock = inv["stock_activo"]
    ventas = inv["ventas_historicas"]

    cargadas = [v for v in ventas if v["ganancia_cargada"]]
    sin_cargar = [
        f"{v['mes']} {v['anio']}"
        for v in ventas if v["cantidad"] > 0 and not v["ganancia_cargada"]
    ]
    santi = sum(c["monto"] for c in inv["comisiones_santi"])
    jose = sum(c["monto"] for c in inv["comisiones_jose"])

    return {
        "acreedores": acreedores,
        "interes_mensual": interes_mensual,
        "gastos_fijos": gastos_fijos,
        "trabados": trabados,
        "stock_costo": sum(s["costo"] for s in stock),
        "stock_venta": sum(s["venta"] for s in stock),
        "stock_liqui": sum(s["liqui"] for s in stock),
        "stock_count": len(stock),
        "ventas_cantidad_total": sum(v["cantidad"] for v in ventas),
        "ventas_ganancia_total_cargada": sum(v["ganancia_usd"] for v in cargadas),
        "ventas_cantidad_cargada": sum(v["cantidad"] for v in cargadas),
        "ventas_meses_cargados": len(cargadas),
        "ventas_meses_sin_cargar": sin_cargar,
        "retiros_total": sum(r["monto_usd"] for r in inv["retiros"]),
        "santi_saldo": santi,
        "jose_saldo": jose,
    }


def hay_datos(inv: dict) -> bool:
    return bool(inv["acreedores"] or inv["stock_activo"] or inv["ventas_historicas"])
