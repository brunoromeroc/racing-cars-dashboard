"""
Parser de 'caja racing cars': hojas 'caja pesos' y 'caja usd'.

Estructura (confirmada contra el xlsx real): la fila 4 (indice 3) es el
encabezado; los datos arrancan en la fila 5. Por posicion:
  col 0 = Descripcion   col 4 = Fecha   col 6 = Monto   col 7 = Saldo
Se ignoran sub-tablas laterales (Caja con Jose, etc.) y la 'Hoja 6'.
"""
from __future__ import annotations

import pandas as pd

from . import sheets

HOJAS = [("caja pesos", "pesos"), ("caja usd", "usd")]
HEADER_ROW = 3
COLS = [0, 4, 6, 7]  # descripcion, fecha, monto, saldo


def _parse_hoja(fuente: str, hoja: str) -> dict:
    raw = sheets.read_raw(fuente, hoja)
    if raw.empty or len(raw) <= HEADER_ROW:
        return _vacio()

    df = raw.iloc[HEADER_ROW + 1:, COLS].copy()
    df.columns = ["descripcion", "fecha", "monto", "saldo"]

    df = df.dropna(subset=["descripcion"])
    df["descripcion"] = df["descripcion"].astype(str).str.strip()

    df["monto"] = pd.to_numeric(df["monto"], errors="coerce")
    df["saldo"] = pd.to_numeric(df["saldo"], errors="coerce")
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce", dayfirst=True)
    # Fechas absurdas fuera de rango -> NaT
    fuera = (df["fecha"] < "2024-01-01") | (df["fecha"] > "2027-12-31")
    df.loc[fuera, "fecha"] = pd.NaT
    # La tabla principal son las filas con fecha valida. Lo que sigue son
    # sub-tablas pegadas (CUENTA RECAUDADORA, Caja con Jose, etc.) que tienen
    # otra estructura y ensucian saldo/totales: se descartan.
    df = df[df["fecha"].notna()].reset_index(drop=True)

    movimientos = []
    for _, r in df.iterrows():
        f = r["fecha"]
        movimientos.append({
            "descripcion": r["descripcion"],
            "fecha": None if pd.isna(f) else f.strftime("%Y-%m-%d"),
            "monto": None if pd.isna(r["monto"]) else float(r["monto"]),
            "saldo": None if pd.isna(r["saldo"]) else float(r["saldo"]),
        })

    montos = df["monto"].dropna()
    # Saldo actual = ultimo valor no nulo de la columna saldo (CAJA REAL)
    s = df["saldo"].dropna()
    saldo_actual = float(s.iloc[-1]) if len(s) else 0.0

    return {
        "movimientos": movimientos,
        "saldo_actual": saldo_actual,
        "total_ingresos": float(montos[montos > 0].sum()),
        "total_salidas": float(montos[montos < 0].sum()),
        "cantidad": int(len(df)),
    }


def _vacio() -> dict:
    return {"movimientos": [], "saldo_actual": 0.0, "total_ingresos": 0.0,
            "total_salidas": 0.0, "cantidad": 0}


def cargar_caja() -> dict:
    """{'pesos': {...}, 'usd': {...}} con la forma del DATA.caja del prototipo."""
    out = {}
    for hoja, key in HOJAS:
        try:
            out[key] = _parse_hoja("caja", hoja)
        except Exception as e:  # noqa: BLE001
            out[key] = _vacio()
            out[f"error_{key}"] = str(e)
    return out
