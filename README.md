# Racing Cars · Dashboard

Dashboard financiero del negocio de compraventa de autos (Kevin). Streamlit
con lectura **en vivo** de Google Sheets, deploy público en Streamlit Cloud.

Port del prototipo `racing_dashboard.html` con el mismo design system
fintech-dark. 9 tabs: Resumen, Caja, Cobros, Pagos, Calendario,
Stock & Ventas, Inversores, Socios & Comisiones y **Análisis Financiero**.

## Cómo correr local

```bash
pip install -r requirements.txt
streamlit run app.py
```

Hay **dos modos** y se eligen solos:

- **Modo vivo**: si existe `.streamlit/secrets.toml` con el service account,
  lee las 3 planillas de Google Sheets en vivo.
- **Modo local** (desarrollo): si no hay service account, lee los `.xlsx`
  de la carpeta `./data` (no se commitean). Sirve para probar sin Drive.

Para el setup completo de producción (service account, compartir planillas,
crear las tabs de `inversion`, repo y deploy) ver **[RUNBOOK.md](RUNBOOK.md)**.

## Fuentes de datos

| Planilla | Qué aporta | Parsing |
|---|---|---|
| `caja racing cars` | Movimientos diarios ARS / USD | Hojas `caja pesos` / `caja usd`. Solo la tabla con fecha; se ignoran sub-tablas (CUENTA RECAUDADORA, Caja con Jose, etc.). |
| `PLANILLA PAGOS Y COBROS ULTIMO` | Cuotas a cobrar y pagar | Hojas USD/ARS de cobros y pagos. |
| `inversion` | Acreedores, gastos fijos, stock, ventas, comisiones, retiros | **Tabs estructuradas `Dash_*`** creadas con `tools/seed_inversion.py` (la planilla cruda es inparseable). |

En modo vivo todo se baja por la **Google Drive API** (no la de Sheets):
funciona igual para Sheets nativos (caja, inversion) y para `.xlsx` subidos
a Drive (la planilla de pagos/cobros lo es, y la API de Sheets no la puede
leer). El dólar blue sale en vivo de **argentinadatos.com**. Los datos se
cachean 10 minutos; el botón **Refrescar datos** fuerza la relectura.

## Estructura

```
app.py                 entrypoint: sidebar, carga, 9 tabs
racing/                núcleo
  sheets.py            acceso dual gspread / xlsx local + cache
  data_caja.py         parser caja pesos/usd
  data_pagos_cobros.py parser cobros/pagos usd/ars
  data_inversion.py    parser de las tabs estructuradas de inversion
  analisis.py          lógica del tab Análisis Financiero
  cuotas.py            agrupación de deuda y flujo (cobros/pagos/calendario)
  categorias.py        categorizador de gastos de caja
  dolar.py             serie de dólar blue
  formato.py           formato argentino ($X.XXX, US$, DD/MM/YYYY)
  ui.py                design system + helpers
tabs/                  un módulo por tab
tools/
  seed_inversion.py    genera/sube las tabs estructuradas de inversion
  snapshot_inversion.json  datos precargados (snapshot del prototipo)
  _test_parsers.py     valida los parsers contra los datos reales
```

## Notas

- El "saldo actual" de caja es el último saldo de la tabla principal (filas
  con fecha). Esto ignora a propósito las sub-tablas pegadas al final de la
  hoja `caja pesos`, que en el dashboard viejo ensuciaban el saldo.
- Pendiente futuro: tab `Patrimonio_Mensual` en la planilla `inversion`
  (snapshot mensual para tracking patrimonial preciso).
