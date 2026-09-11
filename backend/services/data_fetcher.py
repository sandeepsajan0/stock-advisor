import yfinance as yf
import pandas as pd
from typing import List, Optional

SECTOR_INDICES = {
    "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT",
    "Nifty Auto": "^CNXAUTO",
    "Nifty Pharma": "^CNXPHARMA",
    "Nifty FMCG": "^CNXFMCG",
    "Nifty Metal": "^CNXMETAL",
    "Nifty Energy": "^CNXENERGY",
    "Nifty PSE": "^CNXPSE"
}

SECTOR_STOCKS = {
    "Nifty Bank": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "INDUSINDBK.NS", "PNB.NS", "BANKBARODA.NS"],
    "Nifty IT": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS"],
    "Nifty Auto": ["TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "TVSMOTOR.NS", "ASHOKLEY.NS"],
    "Nifty Pharma": ["SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "LUPIN.NS", "AUROPHARMA.NS", "BIOCON.NS"],
    "Nifty FMCG": ["ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", "DABUR.NS", "GODREJCP.NS", "MARICO.NS"],
    "Nifty Metal": ["TATASTEEL.NS", "JSWSTEEL.NS", "HINDALCO.NS", "COALINDIA.NS", "VEDL.NS", "NMDC.NS", "SAIL.NS", "JINDALSTEL.NS"],
    "Nifty Energy": ["NTPC.NS", "ONGC.NS", "POWERGRID.NS", "BPCL.NS", "IOC.NS", "GAIL.NS", "TATAPOWER.NS"],
    "Nifty PSE": ["PFC.NS", "RECLTD.NS", "BEL.NS", "BHEL.NS", "HAL.NS", "IRFC.NS", "NHPC.NS", "SJVN.NS"]
}

# Aggregate all sector stocks + other heavyweights to form our broader scanning universe
NIFTY_50_TICKERS = [stock for stocks in SECTOR_STOCKS.values() for stock in stocks] + [
    "RELIANCE.NS", "LT.NS", "BAJFINANCE.NS", "ASIANPAINT.NS", "TITAN.NS", 
    "ULTRACEMCO.NS", "BAJAJFINSV.NS", "ADANIENT.NS", "ADANIPORTS.NS", "GRASIM.NS", "HDFCLIFE.NS", "SBILIFE.NS"
]

def fetch_historical_data(ticker: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
    """Fetches historical stock data using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None

def fetch_multiple_stocks(tickers: List[str], period: str = "1y", interval: str = "1d") -> dict:
    """Fetches data for multiple stocks simultaneously using threads."""
    data = {}
    if not tickers:
        return data
    
    try:
        # Disable threads to avoid overwhelming Render's limited CPU, and set a timeout so it doesn't hang
        tickers_str = " ".join(tickers)
        df_batch = yf.download(tickers_str, period=period, interval=interval, group_by="ticker", threads=False, progress=False, timeout=10)
        
        if len(tickers) == 1:
            data[tickers[0]] = df_batch
            return data
            
        for ticker in tickers:
            if ticker in df_batch.columns.levels[0]:
                df_ticker = df_batch[ticker].dropna()
                if not df_ticker.empty:
                    data[ticker] = df_ticker
    except Exception as e:
        print(f"Error in batch fetch: {e}")
    return data
