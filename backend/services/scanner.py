from .data_fetcher import SECTOR_INDICES, SECTOR_STOCKS, NIFTY_50_TICKERS, fetch_multiple_stocks, fetch_historical_data
from .analyzer import add_indicators, check_buy_signal, check_intraday_signal, check_44sma_signal, check_sma1020_signal
from .ai_sentiment import get_stock_sentiment
import pandas as pd

def check_market_regime(mode="swing"):
    """Checks the overall Nifty 50 Index trend to allow or suppress trades."""
    period = "5d" if mode == "intraday" else "1y"
    interval = "15m" if mode == "intraday" else "1d"
    
    df = fetch_historical_data("^NSEI", period=period, interval=interval)
    if df is None or df.empty:
        return {"status": "Unknown", "allow_longs": True, "message": "Failed to fetch index data."}
        
    df = add_indicators(df, is_intraday=(mode=="intraday"), mode=mode)
    latest = df.iloc[-1]
    
    try:
        close = latest['Close']
        ema50 = latest['EMA_50']
        
        if close > ema50:
            return {"status": "Bullish", "allow_longs": True, "message": "Market is above 50 EMA. Favorable conditions."}
        else:
            return {"status": "Bearish", "allow_longs": False, "message": "Market is below 50 EMA. High Risk! Long trades suppressed."}
    except KeyError:
         return {"status": "Unknown", "allow_longs": True, "message": "Insufficient data to determine market regime."}

def check_sector_trends(mode="swing"):
    """Analyzes the major sector indices to see which ones are trending."""
    sector_health = []
    trending_sectors = []
    
    period = "5d" if mode == "intraday" else "1y"
    interval = "15m" if mode == "intraday" else "1d"
    
    print("Fetching data for Sector Indices...")
    tickers = list(SECTOR_INDICES.values())
    data_dict = fetch_multiple_stocks(tickers, period=period, interval=interval)
    
    for sector_name, ticker in SECTOR_INDICES.items():
        if ticker not in data_dict or data_dict[ticker].empty:
            sector_health.append({"name": sector_name, "status": "Unknown"})
            continue
            
        df = add_indicators(data_dict[ticker], is_intraday=(mode=="intraday"), mode=mode)
        latest = df.iloc[-1]
        
        try:
            close = latest['Close']
            ema50 = latest['EMA_50']
            
            if close > ema50:
                sector_health.append({"name": sector_name, "status": "Bullish"})
                trending_sectors.append(sector_name)
            else:
                sector_health.append({"name": sector_name, "status": "Bearish"})
        except KeyError:
            sector_health.append({"name": sector_name, "status": "Unknown"})
            
    return sector_health, trending_sectors

def get_stock_sector(ticker: str) -> str:
    """Helper to find which sector a stock belongs to."""
    if ticker in ["^NSEI", "^NSEBANK"]: return "Index"
    for sector, stocks in SECTOR_STOCKS.items():
        if ticker in stocks:
            return sector
    return "Broader Market"

def run_scan(mode="swing"):
    """Scans dynamically based on Sector Trends."""
    market_regime = check_market_regime(mode)
    sector_health, trending_sectors = check_sector_trends(mode)
    
    period = "5d" if mode == "intraday" else "1y"
    interval = "15m" if mode == "intraday" else "1d"
    
    if not trending_sectors:
        print("No sectors are trending. Only scanning the broader heavyweights.")
        scan_list = NIFTY_50_TICKERS.copy()
    else:
        scan_list = []
        for sector in trending_sectors:
            scan_list.extend(SECTOR_STOCKS[sector])
            
        heavyweights = ["RELIANCE.NS", "LT.NS", "BAJFINANCE.NS", "ASIANPAINT.NS"]
        scan_list.extend([h for h in heavyweights if h not in scan_list])
        
    scan_list = list(set(scan_list))
    
    if mode == "intraday":
        scan_list.extend(["^NSEI", "^NSEBANK"])
    
    print(f"Fetching data for {len(scan_list)} dynamically selected stocks (Mode: {mode})...")
    data_dict = fetch_multiple_stocks(scan_list, period=period, interval=interval)
    
    results = []
    
    for ticker, df in data_dict.items():
        if df is None or df.empty:
            continue
            
        df = add_indicators(df, is_intraday=(mode=="intraday"), mode=mode)
        
        if mode == "intraday":
            signal_info = check_intraday_signal(df)
        elif mode == "44sma":
            signal_info = check_44sma_signal(df)
        elif mode == "sma1020":
            signal_info = check_sma1020_signal(df)
        else:
            signal_info = check_buy_signal(df)
        
        if signal_info["signal"]:
            sentiment = get_stock_sentiment(ticker)
            
            if sentiment["label"] == "Bearish":
                continue
                
            signal_info["ai_sentiment"] = sentiment
            signal_info["sector"] = get_stock_sector(ticker)
            
            results.append({
                "ticker": ticker,
                "signal_details": signal_info,
                "date": str(df.index[-1])
            })
            
    return {
        "market_regime": market_regime,
        "sector_health": sector_health,
        "results": results,
        "mode": mode
    }

def get_stock_details(ticker: str):
    data_dict = fetch_multiple_stocks([ticker], period="1y", interval="1d")
    if ticker not in data_dict or data_dict[ticker].empty:
        return None
        
    df = add_indicators(data_dict[ticker])
    signal_info = check_buy_signal(df)
    
    if signal_info["signal"]:
         signal_info["ai_sentiment"] = get_stock_sentiment(ticker)
         signal_info["sector"] = get_stock_sector(ticker)
    
    recent_df = df.tail(100).copy()
    recent_df.reset_index(inplace=True)
    
    if 'Date' in recent_df.columns:
        recent_df['Date'] = recent_df['Date'].dt.strftime('%Y-%m-%d')
    elif 'Datetime' in recent_df.columns:
        recent_df['Date'] = recent_df['Datetime'].dt.strftime('%Y-%m-%d')
        
    recent_df = recent_df.replace([float('inf'), float('-inf')], None)
    recent_df = recent_df.where(pd.notnull(recent_df), None)

    chart_data = recent_df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].to_dict('records')
    
    return {
        "ticker": ticker,
        "signal_details": signal_info,
        "current_price": float(df.iloc[-1]['Close']),
        "chart_data": chart_data
    }
