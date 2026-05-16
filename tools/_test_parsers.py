"""Validacion rapida de los parsers contra los datos reales (modo local)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from racing import data_caja, data_pagos_cobros, data_inversion  # noqa: E402

print("== CAJA ==")
caja = data_caja.cargar_caja()
for k in ("pesos", "usd"):
    d = caja[k]
    print(f"{k}: cant={d['cantidad']} saldo={d['saldo_actual']:.2f} "
          f"ing={d['total_ingresos']:.0f} sal={d['total_salidas']:.0f} "
          f"err={caja.get('error_'+k,'-')}")

print("\n== PAGOS/COBROS ==")
pc = data_pagos_cobros.cargar_pagos_cobros()
for k in ("cobros_usd", "cobros_ars", "pagos_usd", "pagos_ars"):
    d = pc[k]
    print(f"{k}: detalle={len(d['detalle'])} pend={d['total_pendiente']:.2f} "
          f"pag={d['total_pagado']:.2f} cli_pend={d['clientes_pendientes']} "
          f"cuotas_pend={d['cuotas_pendientes']} top={len(d['top'])}")

print("\n== INVERSION ==")
inv = data_inversion.cargar_inversion()
print("counts:", {k: len(v) for k, v in inv.items()
                   if isinstance(v, list) and k != "errores"})
print("errores:", inv["errores"])
t = inv["totales"]
for k in ("acreedores", "interes_mensual", "gastos_fijos", "trabados",
          "stock_costo", "stock_count", "ventas_cantidad_total",
          "ventas_meses_cargados", "santi_saldo", "jose_saldo"):
    print(f"  {k} = {t[k]}")
print("ventas_meses_sin_cargar:", t["ventas_meses_sin_cargar"])

print("\n== sample stock ==", inv["stock_activo"][0] if inv["stock_activo"] else None)
print("== sample cobro ==", pc["cobros_usd"]["detalle"][0]
      if pc["cobros_usd"]["detalle"] else None)
