"""
Genera las TABS ESTRUCTURADAS de la planilla 'inversion' a partir del
snapshot del prototipo (tools/snapshot_inversion.json).

Uso:

  # 1) Solo generar el xlsx local (para desarrollo, sin tocar Drive):
  python tools/seed_inversion.py

  # 2) Subir las tabs a la planilla 'inversion' de Google Sheets:
  #    requiere service_account.json con permiso de EDICION sobre la planilla.
  python tools/seed_inversion.py --upload --sa service_account.json \
      --sheet <ID_DE_LA_PLANILLA_INVERSION>

Las tabs quedan con datos precargados (snapshot al 11/05/2026). Kevin/Bruno
las editan a mano en Sheets cuando cambian; el dashboard las lee en vivo.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = Path(__file__).resolve().parent / "snapshot_inversion.json"

# Debe coincidir con racing.data_inversion.PREFIJO
PREFIJO = "Dash_"


def _si_no(b) -> str:
    return "SI" if b else "NO"


def construir_tabs(inv: dict) -> dict[str, pd.DataFrame]:
    acre = pd.DataFrame([{
        "nombre": a["nombre"], "monto_usd": a["monto_usd"],
        "interes_pct": a["interes_pct"],
        "interes_mensual_usd": a["interes_mensual_usd"],
        "ultima_fecha_pago": a.get("ultima_fecha_pago") or "",
    } for a in inv["acreedores"]])

    gastos = pd.DataFrame([{"concepto": g["concepto"],
                            "monto_usd": g["monto_usd"]}
                           for g in inv["gastos_fijos"]])

    trab = pd.DataFrame([{"vehiculo": v["vehiculo"],
                          "valor_usd": v["valor_usd"]}
                         for v in inv["vehiculos_trabados"]])

    stock = pd.DataFrame([{
        "marca": s["marca"], "anio": s["anio"], "modelo": s["modelo"],
        "costo": s["costo"], "venta": s["venta"], "liqui": s["liqui"],
        "publi": _si_no(s["publi"]), "fecha_ingreso": s.get("fecha_ingreso") or "",
    } for s in inv["stock_activo"]])

    ventas = pd.DataFrame([{
        "mes": v["mes"], "anio": v["anio"], "cantidad": v["cantidad"],
        "ganancia_usd": v["ganancia_usd"],
        "ganancia_cargada": _si_no(v["ganancia_cargada"]),
    } for v in inv["ventas_historicas"]])

    comis = pd.DataFrame(
        [{"persona": "santi", "concepto": c["concepto"], "monto": c["monto"]}
         for c in inv["comisiones_santi"]] +
        [{"persona": "jose", "concepto": c["concepto"], "monto": c["monto"]}
         for c in inv["comisiones_jose"]]
    )

    retiros = pd.DataFrame([{
        "descripcion": r["descripcion"], "fecha": r.get("fecha") or "",
        "monto_usd": r["monto_usd"],
    } for r in inv["retiros"]])

    return {
        f"{PREFIJO}Acreedores": acre, f"{PREFIJO}GastosFijos": gastos,
        f"{PREFIJO}Trabados": trab, f"{PREFIJO}Stock": stock,
        f"{PREFIJO}Ventas": ventas, f"{PREFIJO}Comisiones": comis,
        f"{PREFIJO}Retiros": retiros,
    }


def escribir_xlsx(tabs: dict[str, pd.DataFrame], destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(destino, engine="openpyxl") as xl:
        for nombre, df in tabs.items():
            df.to_excel(xl, sheet_name=nombre, index=False)
    print(f"OK  xlsx local -> {destino}")


def subir_a_sheets(tabs: dict[str, pd.DataFrame], sa_path: str,
                   sheet_key: str) -> None:
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file(
        sa_path, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_key)
    existentes = {ws.title: ws for ws in sh.worksheets()}

    for nombre, df in tabs.items():
        valores = [list(df.columns)] + df.astype(object).where(
            pd.notna(df), "").values.tolist()
        if nombre in existentes:
            ws = existentes[nombre]
            ws.clear()
        else:
            ws = sh.add_worksheet(title=nombre, rows=max(len(df) + 10, 20),
                                  cols=max(len(df.columns) + 2, 6))
        ws.update(valores, value_input_option="USER_ENTERED")
        print(f"OK  tab subida -> {nombre} ({len(df)} filas)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload", action="store_true",
                    help="subir las tabs a la planilla de Google Sheets")
    ap.add_argument("--sa", default="service_account.json",
                    help="ruta al JSON del service account (con permiso edicion)")
    ap.add_argument("--sheet", help="ID de la planilla 'inversion'")
    args = ap.parse_args()

    inv = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    tabs = construir_tabs(inv)
    escribir_xlsx(tabs, ROOT / "data" / "inversion.xlsx")

    if args.upload:
        if not args.sheet:
            ap.error("--upload requiere --sheet <ID de la planilla inversion>")
        subir_a_sheets(tabs, args.sa, args.sheet)


if __name__ == "__main__":
    main()
