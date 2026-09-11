from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from services.scanner import run_scan, get_stock_details
from services.data_fetcher import NIFTY_50_TICKERS
from services.backtester import run_backtest
from typing import Optional

app = FastAPI(title="Smart Stock Advisor API v5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Remove the root route so it doesn't conflict with StaticFiles
# @app.get("/")
# def read_root():
#     return {"status": "ok", "message": "Smart Stock Advisor API is running."}

@app.get("/api/scan")
def scan_market(mode: Optional[str] = "swing"):
    """Scans the market for buy signals with Market Regime & AI filter."""
    scan_data = run_scan(mode)
    return scan_data

@app.get("/api/stocks/{ticker}")
def get_stock(ticker: str):
    """Gets detailed info and chart data for a specific stock."""
    if not ticker.endswith(".NS") and not ticker.endswith(".BO") and not ticker.startswith("^"):
        ticker = f"{ticker}.NS"
        
    details = get_stock_details(ticker)
    if not details:
        return {"error": "Stock not found or data unavailable."}
    return details

@app.get("/api/backtest/{ticker}")
def backtest_stock(ticker: str, mode: Optional[str] = "swing", initial_capital: Optional[float] = 100000.0, period: Optional[str] = None):
    """Runs a historical backtest for a specific stock against the given strategy mode."""
    if not ticker.endswith(".NS") and not ticker.endswith(".BO") and not ticker.startswith("^"):
        ticker = f"{ticker}.NS"
        
    results = run_backtest(ticker, mode, initial_capital, period)
    return results

# Serve static files from the Next.js export directory
frontend_out = os.path.join(os.path.dirname(__file__), "..", "frontend", "out")
if os.path.exists(frontend_out):
    app.mount("/", StaticFiles(directory=frontend_out, html=True), name="static")
