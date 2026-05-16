"""
Categorizador de movimientos de caja (port del prototipo HTML).
El orden importa: se chequea de arriba hacia abajo, primer match gana.

Overrides manuales: en el HTML se guardaban en localStorage. Aca el
dashboard es publico/multiusuario, asi que viven en st.session_state
(duran la sesion del navegador, no se comparten ni persisten).
"""
from __future__ import annotations

import re

import streamlit as st

CATEGORIAS = [
    {"nombre": "Retiros socios", "emoji": "💵", "color": "#ff6b6b",
     "patterns": [r"retiro.*(kevin|lucho|franco)", r"(kevin|lucho).*retiro",
                  r"lucho.*kevin", r"kevin.*lucho"]},
    {"nombre": "Cuotas inversores", "emoji": "🏦", "color": "#ffaa00",
     "patterns": [r"chingolo", r"\bdan\b", r"priscila", r"\beli\b",
                  r"papa\s*kevin", r"\bandi\b", r"(manuel|tuiti|rivarola)"]},
    {"nombre": "Sueldos/Comisiones", "emoji": "👨‍💼", "color": "#74c0fc",
     "patterns": [r"sueldo", r"comisi", r"\bsanti\b", r"\bjose\b", r"facu",
                  r"aguinaldo"]},
    {"nombre": "Comida", "emoji": "🍴", "color": "#ff8787",
     "patterns": [r"comida", r"\bpan\b", r"chori", r"asado", r"almuerzo",
                  r"cena", r"frigor", r"carnicer", r"\bkfc\b", r"restaur",
                  r"mcdonald", r"burger", r"pizza", r"helado"]},
    {"nombre": "Combustible", "emoji": "⛽", "color": "#ffd43b",
     "patterns": [r"nafta", r"gasoil", r"combustible", r"\bypf\b", r"shell",
                  r"axion", r"peaje", r"\besso\b", r"\bgnc\b"]},
    {"nombre": "Oficina/Servicios", "emoji": "🏢", "color": "#69db7c",
     "patterns": [r"alquiler", r"expensas", r"cochera", r"edenor", r"edesur",
                  r"metrogas", r"\bagua\b", r"internet", r"\bclaro\b",
                  r"movistar", r"personal", r"luz"]},
    {"nombre": "Publicidad", "emoji": "📢", "color": "#da77f2",
     "patterns": [r"publicidad", r"\bads\b", r"marketing", r"\bfotos?\b",
                  r"\bvideos?\b", r"redes", r"instagram", r"facebook",
                  r"meta\s*ads"]},
    {"nombre": "Trámites/Gestoría", "emoji": "📋", "color": "#4dabf7",
     "patterns": [r"gestor", r"transfe", r"patente", r"\bvtv\b", r"dnrpa",
                  r"escribano", r"tramit", r"\b08\b", r"\b12\b"]},
    {"nombre": "Mantenimiento", "emoji": "🔧", "color": "#fcc419",
     "patterns": [r"repuesto", r"reparaci", r"mec[aá]nico", r"taller",
                  r"bater[ií]a", r"neum[aá]tico", r"llanta", r"aceite",
                  r"service", r"lava(do|der)"]},
    {"nombre": "Crosby", "emoji": "🏎️", "color": "#3bc9db",
     "patterns": [r"crosby"]},
    {"nombre": "Cobros de cuotas", "emoji": "💰", "color": "#00ff88",
     "patterns": [r"cobro", r"cuota.*(cobr|client)", r"pago.*cuota"]},
    {"nombre": "Ingreso/Venta", "emoji": "📥", "color": "#51cf66",
     "patterns": [r"ingreso", r"venta", r"se[ñn]a"]},
]

OTROS = {"nombre": "Otros", "emoji": "❓", "color": "#868e96", "patterns": []}

TODAS = CATEGORIAS + [OTROS]

_COMPILADAS = [
    (c, [re.compile(p, re.IGNORECASE) for p in c["patterns"]]) for c in CATEGORIAS
]

_OVERRIDES_KEY = "cat_overrides"


def categorizar(descripcion: str, monto=None) -> dict:
    desc = str(descripcion or "")
    for cat, regs in _COMPILADAS:
        for rg in regs:
            if rg.search(desc):
                return cat
    return OTROS


def mov_key(fecha, descripcion, monto) -> str:
    return f"{fecha or ''}|{str(descripcion or '')[:80]}|{monto or 0}"


def _overrides() -> dict:
    return st.session_state.setdefault(_OVERRIDES_KEY, {})


def get_categoria(fecha, descripcion, monto) -> dict:
    """Categoria efectiva: override manual de la sesion o la automatica."""
    k = mov_key(fecha, descripcion, monto)
    ov = _overrides().get(k)
    if ov:
        cat = next((c for c in TODAS if c["nombre"] == ov), None)
        if cat:
            return {**cat, "override": True}
    return categorizar(descripcion, monto)


def set_override(fecha, descripcion, monto, nombre_categoria: str | None) -> None:
    ov = _overrides()
    k = mov_key(fecha, descripcion, monto)
    if nombre_categoria is None:
        ov.pop(k, None)
    else:
        ov[k] = nombre_categoria
