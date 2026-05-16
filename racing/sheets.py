"""
Capa de acceso a datos. Modo dual:

  - VIVO (produccion / Streamlit Cloud): descarga cada planilla en vivo via
    Google Drive API usando un service account (st.secrets). Funciona tanto
    para Google Sheets nativos (export a xlsx) como para archivos .xlsx
    subidos a Drive (descarga directa) -- la planilla de pagos/cobros es un
    .xlsx subido, que la API de Sheets NO puede leer.
  - LOCAL (desarrollo): si no hay service account, lee los .xlsx de ./data.

Toda hoja se devuelve como DataFrame POSICIONAL (header=None): mismas
columnas y valores que pd.read_excel, sea cual sea la fuente. Asi el
parsing es identico contra Drive o contra los xlsx locales.

Cache de 10 minutos. El boton "Refrescar datos" hace st.cache_data.clear().
"""
from __future__ import annotations

import io
import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

LOCAL_FILES = {
    "caja": "caja racing cars.xlsx",
    "pagos_cobros": "PLANILLA PAGOS Y COBROS ULTIMO.xlsx",
    "inversion": "inversion.xlsx",
}

DEFAULT_DATA_PATH = os.getenv("RACING_DATA_PATH", "./data")

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
GS_MIME = "application/vnd.google-apps.spreadsheet"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DRIVE = "https://www.googleapis.com/drive/v3/files"


def _tiene_service_account() -> bool:
    try:
        return "gcp_service_account" in st.secrets
    except Exception:
        return False


def modo() -> str:
    """'vivo' si hay service account configurado, sino 'local'."""
    return "vivo" if _tiene_service_account() else "local"


@st.cache_resource(show_spinner=False)
def _credenciales():
    from google.oauth2.service_account import Credentials
    info = dict(st.secrets["gcp_service_account"])
    return Credentials.from_service_account_info(info, scopes=SCOPES)


def _token() -> str:
    from google.auth.transport.requests import Request
    creds = _credenciales()
    if not creds.valid:
        creds.refresh(Request())
    return creds.token


def _spreadsheet_id(fuente: str) -> str:
    return st.secrets["sheets"][fuente]


@st.cache_data(ttl=600, show_spinner=False)
def _descargar_xlsx(fuente: str) -> bytes:
    """Baja la planilla como bytes xlsx via Drive API (Sheet nativo o xlsx)."""
    sid = _spreadsheet_id(fuente)
    headers = {"Authorization": f"Bearer {_token()}"}
    meta = requests.get(f"{DRIVE}/{sid}", headers=headers, timeout=30,
                        params={"fields": "mimeType",
                                "supportsAllDrives": "true"})
    meta.raise_for_status()
    if meta.json().get("mimeType") == GS_MIME:
        url, params = f"{DRIVE}/{sid}/export", {"mimeType": XLSX_MIME}
    else:
        url, params = f"{DRIVE}/{sid}", {"alt": "media",
                                         "supportsAllDrives": "true"}
    r = requests.get(url, headers=headers, params=params, timeout=90)
    r.raise_for_status()
    return r.content


def _excel(fuente: str):
    if modo() == "vivo":
        return pd.ExcelFile(io.BytesIO(_descargar_xlsx(fuente)),
                            engine="openpyxl")
    path = Path(DEFAULT_DATA_PATH) / LOCAL_FILES[fuente]
    if not path.exists():
        raise FileNotFoundError(
            f"No encuentro {path}. En modo local pone los xlsx en "
            f"{DEFAULT_DATA_PATH} o configura el service account.")
    return pd.ExcelFile(path, engine="openpyxl")


@st.cache_data(ttl=600, show_spinner=False)
def listar_hojas(fuente: str) -> list[str]:
    try:
        return _excel(fuente).sheet_names
    except Exception:
        return []


@st.cache_data(ttl=600, show_spinner=False)
def read_raw(fuente: str, hoja: str) -> pd.DataFrame:
    """Hoja como DataFrame posicional (sin header, columnas 0..n)."""
    return pd.read_excel(_excel(fuente), sheet_name=hoja, header=None,
                         engine="openpyxl")


def read_tabla(fuente: str, hoja: str, header_row: int = 0) -> pd.DataFrame:
    """Lee usando `header_row` (0-based) como fila de encabezados."""
    raw = read_raw(fuente, hoja)
    if raw.empty or len(raw) <= header_row:
        return pd.DataFrame()
    cols = [str(c).strip() for c in raw.iloc[header_row].tolist()]
    df = raw.iloc[header_row + 1:].copy()
    df.columns = cols
    return df.reset_index(drop=True)


def invalidar_cache() -> None:
    st.cache_data.clear()
