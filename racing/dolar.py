"""
Dolar blue en vivo desde argentinadatos.com (misma fuente que el dashboard
de finanzas). Serie historica para convertir movimientos ARS->USD a la
cotizacion del dia, mas el valor actual.
"""
from __future__ import annotations

import bisect

import requests
import streamlit as st

API_SERIE = "https://api.argentinadatos.com/v1/cotizaciones/dolares/blue"


@st.cache_data(ttl=3600, show_spinner=False)
def cargar_serie_blue() -> dict:
    """
    {'YYYY-MM-DD': {'compra': float, 'venta': float}}, mas metadatos.
    Cache 1h. Si la API falla devuelve serie vacia (la UI lo avisa).
    """
    try:
        r = requests.get(API_SERIE, timeout=12)
        r.raise_for_status()
        arr = r.json()
        serie = {}
        for row in arr:
            f = row.get("fecha")
            if f:
                serie[f] = {"compra": row.get("compra"), "venta": row.get("venta")}
        fechas = sorted(serie.keys())
        ultimo = serie[fechas[-1]] if fechas else None
        return {
            "ok": True,
            "serie": serie,
            "fechas": fechas,
            "ultimo": ultimo,
            "ultima_fecha": fechas[-1] if fechas else None,
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "serie": {}, "fechas": [],
                "ultimo": None, "ultima_fecha": None}


def cotiz_blue(fecha_iso: str) -> dict | None:
    """Cotizacion exacta de `fecha_iso` (YYYY-MM-DD) o la anterior mas cercana."""
    data = cargar_serie_blue()
    serie, fechas = data["serie"], data["fechas"]
    if not serie:
        return None
    if fecha_iso in serie:
        return serie[fecha_iso]
    i = bisect.bisect_right(fechas, fecha_iso)
    if i == 0:
        return None
    return serie[fechas[i - 1]]


def convertir_ars_a_usd(monto_ars: float, fecha_iso: str) -> dict | None:
    """{'usd': monto/venta, 'blue': venta} o None si no hay cotizacion."""
    cot = cotiz_blue(fecha_iso)
    if not cot or not cot.get("venta"):
        return None
    return {"usd": monto_ars / cot["venta"], "blue": cot["venta"]}


def blue_actual() -> float | None:
    u = cargar_serie_blue()["ultimo"]
    return u["venta"] if u else None
