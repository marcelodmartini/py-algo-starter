# main.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI(title="Algo Trading API", version="1.0")


@app.get("/health")
def health_check():
    return JSONResponse(content={"status": "ok", "env": os.getenv("RENDER", "local")})

# ejemplo de endpoint


@app.get("/backtest")
def run_backtest(symbol: str = "BTC/USDT", tf: str = "1h"):
    return {"symbol": symbol, "timeframe": tf, "message": "Backtest executed successfully!"}
