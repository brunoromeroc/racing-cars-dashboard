"""
Racing Cars · Dashboard financiero (Streamlit, lectura en vivo de Google Sheets).
Negocio de compraventa de autos de Kevin. Deploy publico en Streamlit Cloud.
"""
from __future__ import annotations

import streamlit as st

from racing import (data_caja, data_inversion, data_pagos_cobros, dolar,
                     sheets, ui)
from tabs import (analisis as t_analisis, caja as t_caja, calendario as t_cal,
                  cobros as t_cobros, comisiones as t_com, inversores as t_inv,
                  pagos as t_pagos, resumen as t_resumen, stock as t_stock)

st.set_page_config(page_title="Racing Cars · Dashboard", page_icon="🏁",
                   layout="wide", initial_sidebar_state="auto")
ui.inyectar_css()
ui.inyectar_pwa()


@st.cache_data(ttl=600, show_spinner="Cargando datos de Drive...")
def _cargar():
    return (data_caja.cargar_caja(),
            data_pagos_cobros.cargar_pagos_cobros(),
            data_inversion.cargar_inversion())


def main() -> None:
    modo = sheets.modo()
    serie = dolar.cargar_serie_blue()
    blue = serie.get("ultimo")

    with st.sidebar:
        st.markdown("### Racing Cars")
        if modo == "vivo":
            st.success("Conectado en vivo a Google Sheets")
        else:
            st.warning("Modo local (xlsx en ./data). Sin service account.")
        if blue:
            ui.html(f'<div class="metric"><div class="label">Dólar blue '
                    f'(venta)</div><div class="value pos">$ '
                    f'{blue["venta"]:,.0f}</div><div class="delta">'
                    f'{serie.get("ultima_fecha", "")} · argentinadatos.com'
                    f'</div></div>'.replace(",", "."))
        else:
            st.error("No se pudo leer el dólar blue (argentinadatos.com).")
        st.markdown("")
        if st.button("Refrescar datos", use_container_width=True):
            sheets.invalidar_cache()
            st.cache_data.clear()
            st.rerun()
        st.caption("Los datos se cachean 10 min. El botón fuerza la "
                   "relectura de las planillas.")

    try:
        caja, pc, inv = _cargar()
    except Exception as e:  # noqa: BLE001
        st.error(f"No pude cargar los datos: {e}")
        if modo == "local":
            st.info("En modo local, poné los xlsx en ./data o configurá el "
                    "service account (ver RUNBOOK.md).")
        st.stop()

    dolar_m = ""
    if blue:
        dolar_m = (f'<div class="rc-dolar-m">Dólar blue (venta) '
                   f'<strong>$ {blue["venta"]:,.0f}</strong>'
                   f'<span>{serie.get("ultima_fecha", "")} · '
                   f'argentinadatos.com</span></div>').replace(",", ".")
    ui.html('<div class="rc-h1">Racing Cars · Dashboard</div>'
            f'<div class="rc-sub">Salud financiera del negocio · fuente: '
            f'Google Sheets {"(en vivo)" if modo == "vivo" else "(local)"}'
            f'</div>{dolar_m}')

    if not data_inversion.hay_datos(inv):
        ui.html('<div class="warning-banner"><strong>Falta setup de '
                'inversión:</strong> la planilla «inversion» todavía no tiene '
                'las tabs estructuradas (Acreedores, Stock, Ventas, etc.). '
                'Inversores, Socios y Análisis Financiero van a salir vacíos '
                'hasta correr <code>tools/seed_inversion.py --upload</code> '
                '(ver RUNBOOK.md).</div>')

    ctx = {"caja": caja, "pc": pc, "inv": inv, "blue": blue, "serie": serie}

    tabs = st.tabs(["Resumen", "Caja", "Cobros", "Pagos", "Calendario",
                    "Stock & Ventas", "Inversores", "Socios & Comisiones",
                    "Análisis Financiero"])
    with tabs[0]:
        t_resumen.render(ctx)
    with tabs[1]:
        t_caja.render(ctx)
    with tabs[2]:
        t_cobros.render(ctx)
    with tabs[3]:
        t_pagos.render(ctx)
    with tabs[4]:
        t_cal.render(ctx)
    with tabs[5]:
        t_stock.render(ctx)
    with tabs[6]:
        t_inv.render(ctx)
    with tabs[7]:
        t_com.render(ctx)
    with tabs[8]:
        t_analisis.render(ctx)


if __name__ == "__main__":
    main()
