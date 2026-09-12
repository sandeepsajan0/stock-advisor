import pandas as pd
from .data_fetcher import fetch_historical_data
from .analyzer import add_indicators, check_buy_signal, check_44sma_signal, check_intraday_signal, check_sma1020_signal
import numpy as np
import math

def run_backtest(ticker: str, mode: str = "swing", initial_capital: float = 100000.0, period: str = None):
    if period is None:
        period = "2y" if mode in ["swing", "44sma", "sma1020"] else "60d"
    interval = "1d" if mode in ["swing", "44sma", "sma1020"] else "15m"
    
    df = fetch_historical_data(ticker, period=period, interval=interval)
    if df is None or df.empty:
        return {"error": "Failed to fetch historical data for backtesting."}
        
    df = add_indicators(df, is_intraday=(mode == "intraday"), mode=mode)
    
    # Define start index based on indicator lengths
    if mode == "sma1020":
        start_idx = 30
    elif mode in ["intraday", "44sma"]:
        start_idx = 50
    else:
        start_idx = 200
    
    if len(df) <= start_idx:
        return {"error": "Not enough data points after indicator calculation."}
    
    active_trade = None
    trades = []
    capital = initial_capital
    peak_capital = initial_capital
    max_drawdown = 0.0
    equity_curve = []
    
    for i in range(start_idx, len(df)):
        current_row = df.iloc[i]
        date_str = str(df.index[i])
        close = current_row['Close']
        high = current_row['High']
        low = current_row['Low']
        atr = current_row.get('ATRr_14', 0)
        
        # Check for exits if in a trade
        if active_trade:
            # Update highest/lowest for trailing stop
            if active_trade['direction'] == 'long':
                active_trade['highest_high'] = max(active_trade.get('highest_high', active_trade['entry_price']), high)
            else:
                active_trade['lowest_low'] = min(active_trade.get('lowest_low', active_trade['entry_price']), low)

            exit_price = None
            exit_reason = None
            direction = active_trade.get('direction', 'long')
            
            if direction == 'long':
                # Dynamic ATR Trailing Stop logic
                if mode == "sma1020" and atr > 0:
                    trail_stop = active_trade['highest_high'] - (2.0 * atr)
                    if trail_stop > active_trade['stop_loss']:
                        active_trade['stop_loss'] = trail_stop

                if low <= active_trade['stop_loss']:
                    exit_price = active_trade['stop_loss']
                    exit_reason = "Stop Loss"
                elif active_trade.get('target_1') is not None and high >= active_trade['target_1']:
                    exit_price = active_trade['target_1']
                    exit_reason = "Target 1"
                    
                # Pattern-based exit for sma1020: SMA Trend Reversal (SMA10 crosses below SMA20)
                if exit_price is None and mode == "sma1020":
                    try:
                        sma5 = current_row['SMA_5_HA']
                        sma20 = current_row['SMA_20_HA']
                        if sma5 < sma20:
                            exit_price = current_row['Close']
                            exit_reason = "Trend Reversed"
                    except (KeyError, IndexError):
                        pass
                        
                if exit_price is not None:
                    profit_loss = exit_price - active_trade['entry_price']
                    profit_loss_pct = (profit_loss / active_trade['entry_price']) * 100
                    trade_qty = capital / active_trade['entry_price']
                    capital = capital + (profit_loss * trade_qty)
                    
            elif direction == 'short':
                # Dynamic ATR Trailing Stop logic
                if mode == "sma1020" and atr > 0:
                    trail_stop = active_trade['lowest_low'] + (2.0 * atr)
                    if trail_stop < active_trade['stop_loss']:
                        active_trade['stop_loss'] = trail_stop

                if high >= active_trade['stop_loss']:
                    exit_price = active_trade['stop_loss']
                    exit_reason = "Stop Loss"
                elif active_trade.get('target_1') is not None and low <= active_trade['target_1']:
                    exit_price = active_trade['target_1']
                    exit_reason = "Target 1"
                    
                # Pattern-based exit for sma1020 shorts: SMA Trend Reversal (SMA10 crosses above SMA20)
                if exit_price is None and mode == "sma1020":
                    try:
                        sma5 = current_row['SMA_5_HA']
                        sma20 = current_row['SMA_20_HA']
                        if sma5 > sma20:
                            exit_price = current_row['Close']
                            exit_reason = "Trend Reversed"
                    except (KeyError, IndexError):
                        pass
                        
                if exit_price is not None:
                    profit_loss = active_trade['entry_price'] - exit_price
                    profit_loss_pct = (profit_loss / active_trade['entry_price']) * 100
                    trade_qty = capital / active_trade['entry_price']
                    capital = capital + (profit_loss * trade_qty)
            
            if exit_price is not None:
                if capital > peak_capital:
                    peak_capital = capital
                drawdown = (peak_capital - capital) / peak_capital * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                trades.append({
                    "entry_date": active_trade['entry_date'],
                    "exit_date": date_str,
                    "type": active_trade['type'],
                    "direction": direction,
                    "entry_price": round(active_trade['entry_price'], 2),
                    "exit_price": round(exit_price, 2),
                    "exit_reason": exit_reason,
                    "profit_loss_pct": round(profit_loss_pct, 2),
                    "capital": round(capital, 2)
                })
                active_trade = None
                equity_curve.append(round(capital, 2))
                continue
            
            equity_curve.append(round(capital, 2))
            continue

        # Check for new signals
        if mode == "intraday":
            signal_info = check_intraday_signal(df, current_idx=i)
        elif mode == "44sma":
            signal_info = check_44sma_signal(df, current_idx=i)
        elif mode == "sma1020":
            signal_info = check_sma1020_signal(df, current_idx=i)
        else:
            signal_info = check_buy_signal(df, current_idx=i)
            
        if signal_info["signal"]:
            active_trade = {
                "entry_date": date_str,
                "type": signal_info["type"],
                "entry_price": signal_info["close"],
                "stop_loss": signal_info["stop_loss"],
                "target_1": signal_info["target_1"],
                "direction": signal_info.get("direction", "long")
            }
        
        equity_curve.append(round(capital, 2))
            
    # Close active trade at the end of the period
    if active_trade:
        last_close = df.iloc[-1]['Close']
        direction = active_trade.get('direction', 'long')
        if direction == 'long':
            profit_loss = last_close - active_trade['entry_price']
        else:
            profit_loss = active_trade['entry_price'] - last_close
        profit_loss_pct = (profit_loss / active_trade['entry_price']) * 100
        trade_qty = capital / active_trade['entry_price']
        capital = capital + (profit_loss * trade_qty)
        
        trades.append({
            "entry_date": active_trade['entry_date'],
            "exit_date": str(df.index[-1]),
            "type": active_trade['type'],
            "direction": direction,
            "entry_price": round(active_trade['entry_price'], 2),
            "exit_price": round(last_close, 2),
            "exit_reason": "End of Period",
            "profit_loss_pct": round(profit_loss_pct, 2),
            "capital": round(capital, 2)
        })

    # Calculate summary statistics
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['profit_loss_pct'] > 0)
    losing_trades = sum(1 for t in trades if t['profit_loss_pct'] <= 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    total_return_pct = ((capital - initial_capital) / initial_capital) * 100
    
    avg_win = 0
    avg_loss = 0
    if winning_trades > 0:
        avg_win = sum(t['profit_loss_pct'] for t in trades if t['profit_loss_pct'] > 0) / winning_trades
    if losing_trades > 0:
        avg_loss = sum(t['profit_loss_pct'] for t in trades if t['profit_loss_pct'] <= 0) / losing_trades
    
    gross_profit = sum(t['profit_loss_pct'] for t in trades if t['profit_loss_pct'] > 0)
    gross_loss = abs(sum(t['profit_loss_pct'] for t in trades if t['profit_loss_pct'] <= 0))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0
    
    # Extract chart data
    chart_df = df.copy()
    chart_df.reset_index(inplace=True)
    if 'Date' in chart_df.columns:
        chart_df['Date'] = chart_df['Date'].dt.strftime('%Y-%m-%d')
    elif 'Datetime' in chart_df.columns:
        chart_df['Date'] = chart_df['Datetime'].dt.strftime('%Y-%m-%d')
        
    chart_df = chart_df.replace([np.nan, float('inf'), float('-inf')], None)
    
    # We want OHLC + our SMAs
    cols_to_keep = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
    if 'SMA_5_HA' in chart_df.columns:
        cols_to_keep.append('SMA_5_HA')
    if 'SMA_20_HA' in chart_df.columns:
        cols_to_keep.append('SMA_20_HA')
        
    chart_data = chart_df[cols_to_keep].to_dict('records')
    for row in chart_data:
        for k, v in row.items():
            if isinstance(v, float) and math.isnan(v):
                row[k] = None
                
    return {
        "ticker": ticker,
        "mode": mode,
        "initial_capital": initial_capital,
        "final_capital": round(capital, 2),
        "total_return_pct": round(total_return_pct, 2),
        "win_rate_pct": round(win_rate, 2),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "avg_win_pct": round(avg_win, 2),
        "avg_loss_pct": round(avg_loss, 2),
        "profit_factor": profit_factor,
        "max_drawdown_pct": round(max_drawdown, 2),
        "equity_curve": equity_curve[-100:],  # Last 100 data points for chart
        "trades": trades,
        "chart_data": chart_data
    }
