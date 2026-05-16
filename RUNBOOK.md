# RUNBOOK · Deploy de Racing Cars Dashboard

Pasos que tenés que hacer vos (lo que no puedo hacer yo: cuenta de Google
Cloud, compartir planillas, repo y deploy). Hacelos en orden. Tiempo total
estimado: ~30 min.

Los IDs reales de las 3 planillas NO están en este repo (es público; son
datos del negocio). Están en tu `.streamlit/secrets.toml` local y en los
Secrets de Streamlit Cloud. Abajo se referencian como:

- caja racing cars → `ID_PLANILLA_CAJA`
- inversion → `ID_PLANILLA_INVERSION`
- PLANILLA PAGOS Y COBROS ULTIMO → `ID_PLANILLA_PAGOS_Y_COBROS`

---

## 1. Service account de Google Cloud (NUEVO, solo Racing Cars)

1. Entrá a https://console.cloud.google.com → **Crear proyecto** →
   nombre `racing-cars-dashboard`.
2. **APIs y servicios → Biblioteca**: habilitá **Google Sheets API** y
   **Google Drive API**.
3. **IAM y administración → Cuentas de servicio → Crear cuenta de servicio**:
   - Nombre: `racing-dashboard`
   - No hace falta asignarle roles del proyecto. Crear.
4. Entrá a la cuenta creada → pestaña **Claves → Agregar clave → Crear clave
   nueva → JSON**. Se descarga un archivo `.json`. **Guardalo bien, no lo
   subas a GitHub.**
5. Abrí ese JSON y copiá el valor de `client_email`
   (algo tipo `racing-dashboard@racing-cars-xxxx.iam.gserviceaccount.com`).

## 2. Compartir las 3 planillas con el service account

Tenés acceso a las 3 planillas, así que lo hacés vos directo. En cada una
(caja racing cars, inversion, PLANILLA PAGOS Y COBROS ULTIMO):

- Botón **Compartir** → pegá el `client_email` del paso 1.5.
- Permiso **Lector** en `caja racing cars` y `PLANILLA PAGOS Y COBROS`.
- En `inversion` ponelo como **Editor** por ahora (lo bajamos a Lector
  después del paso 3). Destildá "Notificar".

## 3. Crear las tabs estructuradas en la planilla `inversion`

> Este paso ya se ejecutó en el setup inicial: las 7 tabs `Dash_*` ya
> existen en la planilla. Queda documentado por si hay que rehacerlo.
> Nota: `tools/snapshot_inversion.json` NO está en el repo (tiene datos
> reales de Kevin); vive solo en tu PC. Para re-seedear, necesitás ese
> archivo local.

La planilla `inversion` cruda no se puede parsear. El dashboard lee 7 tabs
limpias que se crean una sola vez, precargadas con el snapshot del prototipo.
Desde la carpeta del proyecto, con el JSON del paso 1 a mano:

```bash
pip install -r requirements.txt
python tools/seed_inversion.py --upload \
  --sa "RUTA/AL/service_account.json" \
  --sheet ID_PLANILLA_INVERSION
```

Esto crea/llena en la planilla `inversion` 7 tabs con el prefijo `Dash_`:
**Dash_Acreedores, Dash_GastosFijos, Dash_Trabados, Dash_Stock,
Dash_Ventas, Dash_Comisiones, Dash_Retiros**. El prefijo evita que choquen
con las hojas crudas existentes (STOCK, VENTAS, etc.) y deja claro cuáles
son del dashboard. Las hojas originales de Kevin no se tocan.

- Verificá en Google Sheets que aparecieron las 7 tabs `Dash_*` con datos.
- A partir de ahora, **Kevin/vos editan esas tabs `Dash_*` a mano** cuando
  cambian los datos (respetando los nombres de columna). Lectura en vivo.
- Ya podés bajar el permiso del service account en `inversion` a **Lector**
  (el seed ya terminó, no necesita más escribir).

## 4. Repo en GitHub

El repo ya está iniciado localmente (`git init` + primer commit hechos).
Creá el repo remoto y pusheá:

```bash
# si tenés gh:
gh repo create brunoromeroc/racing-cars-dashboard --private --source . --push

# o a mano:
git remote add origin https://github.com/brunoromeroc/racing-cars-dashboard.git
git branch -M main
git push -u origin main
```

`.gitignore` ya excluye `secrets.toml`, el JSON del service account y los
`.xlsx` locales. Confirmá que NO se subió ninguno de esos.

## 5. Deploy en Streamlit Cloud (público)

1. https://share.streamlit.io → **New app** → elegí el repo
   `brunoromeroc/racing-cars-dashboard`, branch `main`, archivo `app.py`.
2. **Advanced settings → Secrets**: pegá esto (es el formato de
   `.streamlit/secrets.toml.example`), completando con el JSON del paso 1:

   ```toml
   [sheets]
   caja = "ID_PLANILLA_CAJA"
   inversion = "ID_PLANILLA_INVERSION"
   pagos_cobros = "ID_PLANILLA_PAGOS_Y_COBROS"

   [gcp_service_account]
   type = "service_account"
   project_id = "..."
   private_key_id = "..."
   private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
   client_email = "racing-dashboard@....iam.gserviceaccount.com"
   client_id = "..."
   auth_uri = "https://accounts.google.com/o/oauth2/auth"
   token_uri = "https://oauth2.googleapis.com/token"
   auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
   client_x509_cert_url = "..."
   universe_domain = "googleapis.com"
   ```

   Importante: el `private_key` va con los `\n` literales, tal cual viene
   en el JSON.
3. Deploy. Cuando levante, en **Settings → Sharing** dejala **pública**
   (cualquiera con el link, sin login).
4. Probá: el sidebar tiene que decir "Conectado en vivo a Google Sheets" y
   mostrar el dólar blue. Revisá los 9 tabs.

## 6. Compartir con el equipo

Pasá el link de `*.streamlit.app` a Kevin, Lucho, Andi, Santi, Jose y Fede.
Es de solo lectura: no pueden romper nada.

---

## Mantenimiento

- **Datos de caja / cobros / pagos**: se actualizan solos, salen en vivo de
  las planillas. Cache de 10 min o botón "Refrescar datos".
- **Datos de inversión** (acreedores, stock, ventas, comisiones, retiros,
  trabados, gastos): editar a mano las tabs `Dash_*` de la planilla
  `inversion`. No cambiar los nombres de las columnas ni de las tabs.
- **Si cambia la estructura de las planillas crudas** (caja / pagos-cobros):
  avisame y ajusto el parser (`racing/data_caja.py` /
  `racing/data_pagos_cobros.py`).

## Validar parsers localmente

Con los `.xlsx` en `./data`:

```bash
python tools/_test_parsers.py
```

Tiene que mostrar los totales de inversión exactos (acreedores 421224,
interés mensual 6021.48, etc.) y los conteos de cobros/pagos/caja.
