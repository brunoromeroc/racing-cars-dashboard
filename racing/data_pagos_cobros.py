"""
Parser de 'PLANILLA PAGOS Y COBROS ULTIMO'.

Hojas (header en fila 1): 'Cobros usd (Deudas)', 'Cobros pesos (deuda)',
'Pagos usd (A pagar)', 'Pagos pesos (A pagar)'. El resto se ignora.

Columnas resueltas de forma flexible (tolera 'Año' mal codificado, 'Vehiculo'
vs 'Veiculo', etc.). El detalle conserva los nombres canonicos que usan el
calendario y el analisis financiero.
"""
from __future__ import annotations

import unicodedata

import pandas as pd

from . import sheets

HOJAS = {
    "cobros_usd": "Cobros usd (Deudas)",
    "cobros_ars": "Cobros pesos (deuda)",
    "pagos_usd": "Pagos usd (A pagar)",
    "pagos_ars": "Pagos pesos (A pagar)",
}

CANONICAS = ["Patente", "Veiculo", "Cliente", "Monto Total", "Año", "Mes",
             "Dia", "Cuotas", "Cuota Pendiente", "Cuota Abonada"]


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    s = s.encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


_ALIAS = {
    "patente": "Patente",
    "veiculo": "Veiculo", "vehiculo": "Veiculo",
    "cliente": "Cliente",
    "monto total": "Monto Total", "montototal": "Monto Total",
    "ano": "Año", "anio": "Año",
    "mes": "Mes",
    "dia": "Dia",
    "cuotas": "Cuotas",
    "cuota pendiente": "Cuota Pendiente",
    "cuota abonada": "Cuota Abonada",
}


def _resolver_columnas(header: list) -> dict:
    """{nombre_canonico: indice_columna} segun el header crudo."""
    mapa = {}
    for idx, h in enumerate(header):
        canon = _ALIAS.get(_norm(h))
        if canon and canon not in mapa:
            mapa[canon] = idx
    return mapa


def _int_o_none(v):
    n = pd.to_numeric(v, errors="coerce")
    return None if pd.isna(n) else int(n)


def _parse_hoja(hoja: str) -> dict:
    raw = sheets.read_raw("pagos_cobros", hoja)
    if raw.empty or len(raw) < 2:
        return _vacio()

    header = raw.iloc[0].tolist()
    mapa = _resolver_columnas(header)
    df = raw.iloc[1:].copy().reset_index(drop=True)

    col = {}
    for c in CANONICAS:
        col[c] = df.iloc[:, mapa[c]] if c in mapa else pd.Series([None] * len(df))

    out = pd.DataFrame({c: col[c].values for c in CANONICAS})
    for c in ["Cuota Pendiente", "Cuota Abonada", "Monto Total"]:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0.0)
    out["Cliente"] = out["Cliente"].astype(str).str.strip()
    out["Veiculo"] = out["Veiculo"].astype(str).str.strip()
    out = out[out["Cliente"].notna() & ~out["Cliente"].isin(["", "nan", "None"])]
    out = out.reset_index(drop=True)

    detalle = []
    for _, r in out.iterrows():
        detalle.append({
            "Patente": None if pd.isna(r["Patente"]) else str(r["Patente"]).strip(),
            "Veiculo": r["Veiculo"],
            "Cliente": r["Cliente"],
            "Monto Total": float(r["Monto Total"]),
            "Año": _int_o_none(r["Año"]),
            "Mes": None if pd.isna(r["Mes"]) else str(r["Mes"]).strip(),
            "Dia": _int_o_none(r["Dia"]),
            "Cuotas": None if pd.isna(r["Cuotas"]) else str(r["Cuotas"]).strip(),
            "Cuota Pendiente": float(r["Cuota Pendiente"]),
            "Cuota Abonada": float(r["Cuota Abonada"]),
        })

    total_pendiente = float(out["Cuota Pendiente"].sum())
    total_pagado = float(out["Cuota Abonada"].sum())
    pend = out[out["Cuota Pendiente"] > 0]

    grp = out.groupby("Cliente").agg(
        pendiente=("Cuota Pendiente", "sum"),
        pagado=("Cuota Abonada", "sum"),
    ).reset_index().sort_values("pendiente", ascending=False)
    top = [
        {"Cliente": g["Cliente"], "pendiente": float(g["pendiente"]),
         "pagado": float(g["pagado"])}
        for _, g in grp.head(15).iterrows()
    ]

    return {
        "detalle": detalle,
        "total_pendiente": total_pendiente,
        "total_pagado": total_pagado,
        "clientes_pendientes": int(pend["Cliente"].nunique()),
        "cuotas_pendientes": int(len(pend)),
        "top": top,
    }


def _vacio() -> dict:
    return {"detalle": [], "total_pendiente": 0.0, "total_pagado": 0.0,
            "clientes_pendientes": 0, "cuotas_pendientes": 0, "top": []}


def cargar_pagos_cobros() -> dict:
    """{'cobros_usd':{...},'cobros_ars':{...},'pagos_usd':{...},'pagos_ars':{...}}"""
    out = {}
    for key, hoja in HOJAS.items():
        try:
            out[key] = _parse_hoja(hoja)
        except Exception as e:  # noqa: BLE001
            out[key] = _vacio()
            out[f"error_{key}"] = str(e)
    return out
