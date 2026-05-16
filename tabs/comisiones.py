"""Tab Socios & Comisiones: cuentas corrientes de Santi, Jose y retiros."""
from __future__ import annotations

import streamlit as st

from racing import ui
from racing.formato import fmt_fecha, fmt_usd
from racing.ui import color_span as cs


def _cuenta(nombre: str, movs: list[dict], saldo: float) -> None:
    pos = sum(c["monto"] for c in movs if c["monto"] > 0)
    neg = sum(c["monto"] for c in movs if c["monto"] < 0)
    ui.grid([
        ui.metric_card(f"Saldo {nombre}", cs(fmt_usd(saldo),
                       "pos" if saldo > 0 else "neg"),
                       "A pagarle" if saldo > 0 else "En contra",
                       "warning" if saldo > 0 else "negative"),
        ui.metric_card("Comisiones ganadas", fmt_usd(pos)),
        ui.metric_card("Retiros", fmt_usd(abs(neg))),
        ui.metric_card("Movimientos", str(len(movs))),
    ])
    filas = [[c["concepto"],
              cs(fmt_usd(c["monto"]), "neg" if c["monto"] < 0 else "pos")]
             for c in movs]
    filas.append(["<strong>SALDO</strong>",
                  cs(fmt_usd(saldo), "neg" if saldo < 0 else "pos")])
    ui.html(f'<div class="rc-h3">Cuenta corriente {nombre}</div>')
    ui.tabla(["Concepto", "USD"], filas, clases_col=["", "num"], scroll=True)


def _retiros(inv: dict) -> None:
    t = inv["totales"]
    retiros = inv["retiros"]
    n = len(retiros) or 1
    ui.grid([
        ui.metric_card("Total retiros", cs(fmt_usd(t["retiros_total"]), "neg")),
        ui.metric_card("Cantidad de retiros", str(len(retiros))),
        ui.metric_card("Promedio por retiro",
                       fmt_usd(t["retiros_total"] / n)),
    ])
    filas = [[fmt_fecha(r["fecha"]), r["descripcion"],
              cs(fmt_usd(r["monto_usd"]), "neg")] for r in retiros]
    filas.append(["<strong>TOTAL</strong>", "",
                  cs(fmt_usd(t["retiros_total"]), "neg")])
    ui.html('<div class="rc-h3">Retiros de socios (Lucho / Kevin)</div>')
    ui.tabla(["Fecha", "Descripción", "USD"], filas,
             clases_col=["", "", "num"])


def render(ctx: dict) -> None:
    inv = ctx["inv"]
    t = inv["totales"]
    ui.html('<div class="rc-h2">Socios & comisiones</div>')
    s1, s2, s3 = st.tabs(["Santi", "Jose", "Retiros socios"])
    with s1:
        _cuenta("Santi", inv["comisiones_santi"], t["santi_saldo"])
    with s2:
        _cuenta("Jose", inv["comisiones_jose"], t["jose_saldo"])
    with s3:
        _retiros(inv)
