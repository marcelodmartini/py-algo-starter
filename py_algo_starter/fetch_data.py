import os
import pandas as pd

def auto_fetch_to_csv(cfg: dict) -> str:
    # Placeholder: respeta csv_path y retorna ese path
    csv_path = cfg["data"]["csv_path"]
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    if not os.path.exists(csv_path):
        # crear CSV mínimo si no existe
        df = pd.DataFrame({
            "datetime": pd.date_range("2024-01-01", periods=200, freq="H"),
            "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 1_000
        })
        df.to_csv(csv_path, index=False)
    return csv_path
