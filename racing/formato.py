"""Formato argentino: pesos $X.XXX, dolares US$ X.XXX, fechas DD/MM/YYYY."""
from __future__ import annotations

from datetime import date, datetime

import pandas as pd

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}
MESES_NOMBRE = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre",
    12: "Diciembre",
}


def _es_nulo(v) -> bool:
    try:
        return v is None or pd.isna(v)
    except (TypeError, ValueError):
        return v is None


def fmt_ars(value) -> str:
    """$ 1.010.000  (miles con punto, sin decimales)."""
    if _es_nulo(value):
        return "—"
    return f"$ {value:,.0f}".replace(",", ".")


def fmt_usd(value) -> str:
    """US$ 6.021 si |x|>=1000; US$ 12,50 para montos chicos (coma decimal)."""
    if _es_nulo(value):
        return "—"
    if abs(value) >= 1000:
        return f"US$ {value:,.0f}".replace(",", ".")
    return f"US$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(value, dec: int = 1) -> str:
    if _es_nulo(value):
        return "—"
    return f"{value:.{dec}f}%"


def fmt_fecha(value) -> str:
    """Cualquier fecha/Timestamp -> DD/MM/YYYY. '—' si no hay."""
    if _es_nulo(value):
        return "—"
    if isinstance(value, str):
        value = pd.to_datetime(value, errors="coerce", dayfirst=True)
        if _es_nulo(value):
            return "—"
    if isinstance(value, (datetime, date, pd.Timestamp)):
        return value.strftime("%d/%m/%Y")
    return str(value)


def mes_a_numero(nombre) -> int | None:
    if nombre is None:
        return None
    return MESES.get(str(nombre).strip().lower())
