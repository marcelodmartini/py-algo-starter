PATCH: py-algo-starter
----------------------
Qué incluye:
- pyproject.toml (convierte el repo en paquete Python instalable)
- src/py_algo_starter/run_backtest.py (con run_once())

Cómo aplicar:
1) Copiá/mergeá esta estructura dentro del repo py-algo-starter.
2) Asegurate que los módulos usados por run_backtest.py (utils.py, indicators_pack.py,
   fetch_data.py, signal_engine.py, strategy_bt.py, etc.) estén dentro de `src/py_algo_starter/`
   o ajustá imports a `.utils`, `.signal_engine`, etc. (lo ideal).
3) Commit & push.
4) En Render (cron), usá: `python -m py_algo_starter.run_backtest`.
