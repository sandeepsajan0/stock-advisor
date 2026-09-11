import pandas as pd
import pandas_ta as ta

def add_indicators(df: pd.DataFrame, is_intraday: bool = False, mode: str = "swing") -> pd.DataFrame:
    """Adds technical indicators to the DataFrame using pandas_ta."""
    if mode == "sma1020":
        min_length = 30
    elif is_intraday:
        min_length = 50
    else:
        min_length = 200
    
    if df.empty or len(df) < min_length:
        return df
    
    if 'Close' not in df.columns:
        return df
        
    try:
        if mode == "sma1020":
            # SMA 10/20 Internal HA strategy indicators
            # Compute internal Heikin Ashi
            df['HA_Close'] = (df['Open'] + df['High'] + df['Low'] + df['Close']) / 4.0
            ha_open = [(df['Open'].iloc[0] + df['Close'].iloc[0]) / 2.0]
            for i in range(1, len(df)):
                ha_open.append((ha_open[-1] + df['HA_Close'].iloc[i-1]) / 2.0)
            df['HA_Open'] = ha_open
            
            # SMA on HA Close (optimized: fast 5 / slow 20)
            df['SMA_5_HA'] = df['HA_Close'].rolling(window=5).mean()
            df['SMA_20_HA'] = df['HA_Close'].rolling(window=20).mean()
            
            # ATR and ADX on real prices
            df.ta.atr(length=14, append=True)
            df.ta.adx(length=14, append=True)
            
        elif is_intraday:
            # Intraday indicators
            df.ta.ema(length=9, append=True)
            df.ta.ema(length=21, append=True)
            df.ta.ema(length=50, append=True)
            # VWAP requires High, Low, Close, Volume
            if all(col in df.columns for col in ['High', 'Low', 'Close', 'Volume']):
                df.ta.vwap(append=True)
            df.ta.supertrend(length=10, multiplier=3, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.atr(length=14, append=True)
        else:
            # Swing indicators
            df.ta.ema(length=50, append=True)
            df.ta.ema(length=200, append=True)
            df.ta.sma(length=44, append=True) # Custom 44 SMA strategy
            df.ta.rsi(length=14, append=True)
            df.ta.rsi(length=3, append=True)
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.supertrend(length=10, multiplier=3, append=True)
            df.ta.atr(length=14, append=True)
            df['LOW_10'] = df['Low'].rolling(window=10).min()
            
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        
    return df

def check_intraday_signal(df: pd.DataFrame, current_idx: int = -1) -> dict:
    """
    Intraday Engine: Scans for VWAP Crossovers and Intraday SuperTrend.
    Target: Quick 1-2%, Stop Loss: Tight (0.5 - 1%).
    """
    if df.empty or len(df) < 50:
        return {"signal": False}
        
    latest = df.iloc[current_idx]
    prev = df.iloc[current_idx - 1]
    
    try:
        close = latest['Close']
        open_price = latest['Open']
        ema9 = latest['EMA_9']
        ema50 = latest['EMA_50']
        
        # Find VWAP column name (pandas_ta names it like VWAP_D)
        vwap_col = [c for c in df.columns if 'VWAP' in c]
        vwap = latest[vwap_col[0]] if vwap_col else 0
        prev_vwap = prev[vwap_col[0]] if vwap_col else 0
        
        supertrend_dir_latest = latest.get('SUPERTd_10_3.0', 0)
        supertrend_dir_prev = prev.get('SUPERTd_10_3.0', 0)
        
        macd = latest['MACD_12_26_9']
        macds = latest['MACDs_12_26_9']
        atr = latest['ATRr_14']
        
        # Base Filter: Price above 50 EMA on 15m chart
        if close < ema50:
            return {"signal": False}
            
        strategy_triggered = None
        
        # 1. VWAP Crossover Breakout
        if vwap > 0 and (prev['Close'] < prev_vwap) and (close > vwap) and (close > open_price):
            strategy_triggered = "Intraday VWAP Breakout"
            
        # 2. Intraday SuperTrend
        elif supertrend_dir_latest == 1 and supertrend_dir_prev == -1:
            strategy_triggered = "Intraday SuperTrend"
            
        # 3. Momentum Scalp (9 EMA > VWAP + MACD Bullish)
        elif vwap > 0 and (ema9 > vwap) and (macd > 0) and (macd > macds) and (prev['MACD_12_26_9'] <= prev['MACDs_12_26_9']):
            strategy_triggered = "Intraday Momentum Scalp"
            
        if strategy_triggered:
            # Intraday Risk Management (Very Tight)
            stop_loss = close - (1.0 * atr) # Only 1 ATR risk for intraday
            risk_amount = close - stop_loss
            if risk_amount <= 0:
                 return {"signal": False}
                 
            # Quick Intraday Targets: 1:2 and 1:3 Risk:Reward
            target_1 = close + (risk_amount * 2.0)
            target_2 = close + (risk_amount * 3.0)
            
            return {
                "signal": True,
                "type": strategy_triggered,
                "close": float(close),
                "stop_loss": float(stop_loss),
                "target_1": float(target_1),
                "target_2": float(target_2),
                "risk_amount": float(risk_amount),
                "rsi": 50.0, # Default since we removed RSI from intraday for speed
                "macd": float(macd)
            }
            
        return {"signal": False}
    except Exception as e:
        print(f"Intraday signal error: {e}")
        return {"signal": False}

def check_44sma_signal(df: pd.DataFrame, current_idx: int = -1) -> dict:
    """
    Custom 44 SMA Swing Strategy:
    1. 44 SMA is rising (Current SMA > Prev SMA)
    2. Latest candle is bullish (Close > Open)
    3. Price closed above 44 SMA
    """
    if df.empty or len(df) < 50:
        return {"signal": False}
        
    latest = df.iloc[current_idx]
    prev = df.iloc[current_idx - 1]
    
    try:
        sma44_latest = latest['SMA_44']
        sma44_prev = prev['SMA_44']
        
        close = latest['Close']
        open_price = latest['Open']
        
        atr = latest['ATRr_14']
        low_10 = latest['LOW_10']
        
        # Rule 1: 44 SMA must be rising
        sma_rising = sma44_latest > sma44_prev
        
        # Rule 2: Bullish candle (Close > Open)
        bullish_candle = close > open_price
        
        # Rule 3: Close is above 44 SMA
        above_sma = close > sma44_latest
        
        if sma_rising and bullish_candle and above_sma:
            strategy_triggered = "44 SMA Bounce"
            
            # Risk Management
            atr_stop = close - (2.0 * atr)
            stop_loss = min(atr_stop, low_10)
            
            risk_amount = close - stop_loss
            if risk_amount <= 0:
                 return {"signal": False}
                 
            target_1 = close + (risk_amount * 1.5)
            target_2 = close + (risk_amount * 2.5)
            
            return {
                "signal": True,
                "type": strategy_triggered,
                "close": float(close),
                "stop_loss": float(stop_loss),
                "target_1": float(target_1),
                "target_2": float(target_2),
                "risk_amount": float(risk_amount),
                "rsi": float(latest.get('RSI_14', 50)),
                "macd": float(latest.get('MACD_12_26_9', 0))
            }
            
        return {"signal": False}
    except KeyError as e:
        print(f"Missing indicator column for 44 SMA: {e}")
        return {"signal": False}

def check_buy_signal(df: pd.DataFrame, current_idx: int = -1) -> dict:
    """
    Swing Multi-Strategy Engine: Scans for SuperTrend, Connors RSI, and MACD Zero-Line Bounce.
    """
    if df.empty or len(df) < 200:
        return {"signal": False}
        
    latest = df.iloc[current_idx]
    prev = df.iloc[current_idx - 1]
    
    try:
        ema50 = latest['EMA_50']
        ema200 = latest['EMA_200']
        rsi_14 = latest['RSI_14']
        rsi_3 = latest['RSI_3']
        macd = latest['MACD_12_26_9']
        macds = latest['MACDs_12_26_9']
        
        supertrend_dir_latest = latest.get('SUPERTd_10_3.0', 0)
        supertrend_dir_prev = prev.get('SUPERTd_10_3.0', 0)
        
        atr = latest['ATRr_14']
        close = latest['Close']
        low_10 = latest['LOW_10']
        
        uptrend = (close > ema200)
        if not uptrend:
            return {"signal": False}
            
        strategy_triggered = None
        
        if supertrend_dir_latest == 1 and supertrend_dir_prev == -1:
            strategy_triggered = "SuperTrend Breakout"
            
        elif (close > ema50) and (rsi_3 < 15):
            strategy_triggered = "Connors Micro-Dip"
            
        elif (macd > 0) and (macds > 0) and (macd > macds) and (prev['MACD_12_26_9'] <= prev['MACDs_12_26_9']):
            strategy_triggered = "MACD Momentum Bounce"
            
        if strategy_triggered:
            atr_stop = close - (2.0 * atr)
            stop_loss = min(atr_stop, low_10)
            
            risk_amount = close - stop_loss
            if risk_amount <= 0:
                 return {"signal": False}
                 
            target_1 = close + (risk_amount * 1.5)
            target_2 = close + (risk_amount * 2.5)
            
            return {
                "signal": True,
                "type": strategy_triggered,
                "close": float(close),
                "stop_loss": float(stop_loss),
                "target_1": float(target_1),
                "target_2": float(target_2),
                "risk_amount": float(risk_amount),
                "rsi": float(rsi_14),
                "macd": float(macd)
            }
            
        return {"signal": False}
    except KeyError as e:
        return {"signal": False}

def check_sma1020_signal(df: pd.DataFrame, current_idx: int = -1) -> dict:
    """
    SMA 5/20 Internal HA Cross Strategy (Optimized):
    Uses internally computed Heikin Ashi candles for signal smoothing,
    but trades execute at REAL market prices.
    
    Entry: SMA5(HA) > SMA20(HA) + SMA5 rising + 2 consecutive green HA candles + ADX > 20
    Stop Loss: 1% fixed from entry (tight cut on losers).
    Exit: Dynamic ATR Trailing Stop (2.0x) + Trend Reversal (SMA5 crosses SMA20).
    """
    if df.empty or len(df) < 30:
        return {"signal": False}

    latest = df.iloc[current_idx]
    prev = df.iloc[current_idx - 1]

    try:
        sma5 = latest['SMA_5_HA']
        sma20 = latest['SMA_20_HA']
        sma5_prev = prev['SMA_5_HA']

        ha_close = latest['HA_Close']
        ha_open = latest['HA_Open']
        ha_close_prev = prev['HA_Close']
        ha_open_prev = prev['HA_Open']

        close = latest['Close']
        atr = latest.get('ATRr_14', 0)
        
        # ADX filter
        adx_col = [c for c in df.columns if c.startswith('ADX_')]
        adx_val = latest[adx_col[0]] if adx_col else 25  # default pass if not found

        # Conditions
        sma5_rising = sma5 > sma5_prev
        bullish_cross = sma5 > sma20
        ha_green_now = ha_close > ha_open
        ha_green_prev = ha_close_prev > ha_open_prev
        above_sma = ha_close > sma5
        adx_ok = adx_val > 20

        # LONG signal: bullish cross + rising + 2 green HA candles + ADX
        if bullish_cross and sma5_rising and ha_green_now and ha_green_prev and above_sma and adx_ok:
            stop_loss = close * 0.99  # 1% tight stop — cut losers fast
            risk_amount = close - stop_loss
            if risk_amount <= 0:
                return {"signal": False}

            return {
                "signal": True,
                "type": "SMA 5/20 HA Cross",
                "direction": "long",
                "close": float(close),
                "stop_loss": float(stop_loss),
                "target_1": None,  # No hard target — ATR trailing stop lets winners run
                "target_2": None,
                "risk_amount": float(risk_amount),
                "rsi": float(adx_val),
                "macd": float(sma5 - sma20)
            }

        # SHORT signal: bearish cross + falling + 2 red HA candles + ADX
        sma5_falling = sma5 < sma5_prev
        bearish_cross = sma5 < sma20
        ha_red_now = ha_close < ha_open
        ha_red_prev = ha_close_prev < ha_open_prev
        below_sma = ha_close < sma5

        if bearish_cross and sma5_falling and ha_red_now and ha_red_prev and below_sma and adx_ok:
            stop_loss = close * 1.01  # 1% tight stop for short
            risk_amount = stop_loss - close
            if risk_amount <= 0:
                return {"signal": False}

            return {
                "signal": True,
                "type": "SMA 5/20 HA Cross (Short)",
                "direction": "short",
                "close": float(close),
                "stop_loss": float(stop_loss),
                "target_1": None,  # No hard target — ATR trailing stop lets winners run
                "target_2": None,
                "risk_amount": float(risk_amount),
                "rsi": float(adx_val),
                "macd": float(sma5 - sma20)
            }

        return {"signal": False}
    except (KeyError, IndexError) as e:
        print(f"SMA 5/20 signal error: {e}")
        return {"signal": False}
