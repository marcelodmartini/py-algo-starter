# py-algo-starter

Starter para descargar datos, calcular indicadores/señales, ejecutar un backtest (Backtrader) y publicar un reporte QuantStats. Listo para **cron en Render** y para ejecución **a demanda** desde el web-service hermano (`py-algo-web-service`).

## Ejecutar local

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

export WEB_SERVICE_BASE_URL="https://py-algo-web-service.onrender.com"
export UPLOAD_TOKEN="TU_TOKEN"
export REPORTS_DIR="/tmp/reports"

python -m py_algo_starter.run_backtest --config config.yaml
```

## En Render (Cron Job)

- **Command**: `python -m py_algo_starter.run_backtest`
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **ENV**:
  - `PYTHON_VERSION=3.11.9`
  - `TZ=America/Argentina/Buenos_Aires`
  - `REPORTS_DIR=/tmp/reports`
  - `UPLOAD_TOKEN=...`
  - `WEB_SERVICE_BASE_URL=https://py-algo-web-service.onrender.com`

## Estructura

```
py-algo-starter/
├─ pyproject.toml
├─ requirements.txt
├─ README.md
├─ config.yaml
├─ data/
│  └─ .gitkeep
└─ py_algo_starter/
   ├─ __init__.py
   ├─ env.py
   ├─ run_backtest.py
   ├─ utils.py
   ├─ indicators_pack.py
   ├─ fetch_data.py
   ├─ signal_engine.py
   └─ strategy_bt.py
```

## API Python

```python
from py_algo_starter import run_once
report_path, public_url = run_once("config.yaml")
```

## Notas

- Usa `pandas==2.2.2` y `numpy==1.26.4` para evitar problemas de build en entornos como Render.
- El web-service consume `POST /upload-report` con header `X-Upload-Token` y sirve los HTML en `/reports/...` y `/`.
