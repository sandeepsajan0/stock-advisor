"use client";

import React, { useState } from 'react';

export default function StockCard({ data, mode }) {
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestData, setBacktestData] = useState(null);
  const [backtestError, setBacktestError] = useState(null);

  const { ticker, signal_details, date } = data;
  const { 
    type, close, stop_loss, target_1, target_2, rsi, ai_sentiment, sector
  } = signal_details;

  const runBacktest = async () => {
    setBacktestLoading(true);
    setBacktestError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL !== undefined ? process.env.NEXT_PUBLIC_API_URL : (process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '');
      const res = await fetch(`${apiUrl}/api/backtest/${ticker}?mode=${mode}`);
      if (!res.ok) throw new Error('Failed to run backtest');
      const json = await res.json();
      setBacktestData(json);
    } catch (err) {
      setBacktestError("Unable to reach backend.");
    } finally {
      setBacktestLoading(false);
    }
  };

  // Format currency
  const fmt = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val);

  // Dynamic Strategy Badge Colors
  let badgeColor = 'rgba(74, 222, 128, 0.15)';
  let badgeBorder = 'rgba(74, 222, 128, 0.3)';
  let textColor = 'var(--primary)';
  
  if (type.includes('SuperTrend')) {
     badgeColor = 'rgba(192, 132, 252, 0.15)';
     badgeBorder = 'rgba(192, 132, 252, 0.3)';
     textColor = 'var(--accent)';
  } else if (type.includes('Connors') || type.includes('VWAP')) {
     badgeColor = 'rgba(96, 165, 250, 0.15)';
     badgeBorder = 'rgba(96, 165, 250, 0.3)';
     textColor = 'var(--secondary)';
  } else if (type.includes('Scalp')) {
     badgeColor = 'rgba(251, 146, 60, 0.15)';
     badgeBorder = 'rgba(251, 146, 60, 0.3)';
     textColor = '#fb923c';
  } else if (type.includes('44 SMA')) {
     badgeColor = 'rgba(245, 158, 11, 0.15)'; // Amber/Orange
     badgeBorder = 'rgba(245, 158, 11, 0.3)';
     textColor = '#f59e0b';
  } else if (type.includes('SMA 5/20') || type.includes('SMA 10/20')) {
     badgeColor = 'rgba(232, 121, 249, 0.15)'; // Fuchsia/Purple
     badgeBorder = 'rgba(232, 121, 249, 0.3)';
     textColor = '#e879f9';
  }

  // Formatting for index names vs stocks
  const displayTicker = ticker === "^NSEI" ? "NIFTY 50" : (ticker === "^NSEBANK" ? "BANK NIFTY" : ticker.replace('.NS', ''));

  return (
    <div className="glass-card" style={{ borderTop: mode === 'intraday' ? '3px solid var(--secondary)' : (mode === '44sma' ? '3px solid #f59e0b' : (mode === 'sma1020' ? '3px solid #e879f9' : '3px solid var(--primary)')) }}>
      <div className="flex-between mb-2">
        <h2 className="font-bold" style={{ fontSize: '1.5rem', margin: 0 }}>{displayTicker}</h2>
        <span className="badge" style={{ background: badgeColor, border: `1px solid ${badgeBorder}`, color: textColor }}>{type}</span>
      </div>
      
      <div style={{ marginBottom: '1.5rem' }}>
        <p className="text-sm" style={{ margin: '0 0 4px 0' }}>Current Price (LTP)</p>
        <div className="font-bold" style={{ fontSize: '2rem', color: 'var(--foreground)' }}>{fmt(close)}</div>
        <p className="text-sm mt-1">Signal Time: {date}</p>
      </div>

      <div style={{ background: 'rgba(0,0,0,0.3)', padding: '1.2rem', borderRadius: '12px', marginBottom: '1.5rem' }}>
        <div className="flex-between mt-1">
          <span className="text-sm font-bold">Target 1</span>
          <span className="text-green font-bold">{fmt(target_1)}</span>
        </div>
        <div className="flex-between mt-1">
          <span className="text-sm font-bold">Target 2</span>
          <span className="text-green font-bold">{fmt(target_2)}</span>
        </div>
        <div className="flex-between mt-1" style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '0.8rem', marginTop: '0.8rem' }}>
          <span className="text-sm font-bold">{mode === 'intraday' ? 'Tight Stop Loss' : 'Wider Stop Loss'}</span>
          <span className="text-red font-bold">{fmt(stop_loss)}</span>
        </div>
      </div>

      <div>
        <h4 style={{ margin: '0 0 0.8rem 0', fontSize: '0.9rem', color: '#cbd5e1' }}>Context & AI Sentiment</h4>
        <div className="flex-between mb-2">
          <span className="text-sm">Sector</span>
          <span className="font-bold" style={{ color: 'var(--secondary)' }}>{sector || 'N/A'}</span>
        </div>
        {mode !== 'intraday' && (
          <div className="flex-between mb-2">
            <span className="text-sm">RSI (14)</span>
            <span style={{ color: rsi < 45 ? 'var(--primary)' : 'var(--secondary)' }}>{rsi.toFixed(2)}</span>
          </div>
        )}
        {ai_sentiment && (
          <div className="flex-between mb-2" style={{
            background: 'rgba(255,255,255,0.05)',
            padding: '0.5rem',
            borderRadius: '6px'
          }}>
            <span className="text-sm">FinBERT AI</span>
            <span style={{ 
              fontWeight: 'bold',
              color: ai_sentiment.label === 'Bullish' ? 'var(--primary)' : (ai_sentiment.label === 'Bearish' ? 'var(--danger)' : 'var(--foreground)')
            }}>
              {ai_sentiment.label === 'Bullish' ? '🟢 Bullish' : (ai_sentiment.label === 'Bearish' ? '🔴 Bearish' : '⚪ Neutral')}
            </span>
          </div>
        )}
      </div>

      <div style={{ marginTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '1.5rem' }}>
        <button 
          onClick={runBacktest}
          disabled={backtestLoading}
          style={{
            width: '100%',
            padding: '10px',
            background: 'rgba(255,255,255,0.05)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: 'var(--foreground)',
            borderRadius: '6px',
            cursor: 'pointer',
            transition: 'all 0.3s',
            fontWeight: 'bold'
          }}
          onMouseOver={(e) => e.target.style.background = 'rgba(255,255,255,0.1)'}
          onMouseOut={(e) => e.target.style.background = 'rgba(255,255,255,0.05)'}
        >
          {backtestLoading ? 'Running Backtest...' : `Run Historical Backtest (${mode})`}
        </button>

        {backtestError && <p className="text-sm text-red mt-2">{backtestError}</p>}
        
        {backtestData && !backtestData.error && (
          <div style={{
            marginTop: '1rem',
            background: 'rgba(0,0,0,0.3)',
            padding: '1rem',
            borderRadius: '8px',
            border: '1px solid var(--secondary)'
          }}>
            <h4 style={{ margin: '0 0 0.5rem 0', color: 'var(--secondary)' }}>Backtest Results</h4>
            <div className="flex-between mt-1">
              <span className="text-sm">Total Trades</span>
              <span className="font-bold">{backtestData.total_trades}</span>
            </div>
            <div className="flex-between mt-1">
              <span className="text-sm">Win Rate</span>
              <span className="font-bold text-green">{backtestData.win_rate_pct}%</span>
            </div>
            <div className="flex-between mt-1">
              <span className="text-sm">Total Return</span>
              <span className="font-bold" style={{ color: backtestData.total_return_pct > 0 ? 'var(--primary)' : 'var(--danger)' }}>
                {backtestData.total_return_pct > 0 ? '+' : ''}{backtestData.total_return_pct}%
              </span>
            </div>
            <div className="flex-between mt-1">
              <span className="text-sm">Max Drawdown</span>
              <span className="font-bold text-red">-{backtestData.max_drawdown_pct}%</span>
            </div>
          </div>
        )}
        
        {backtestData && backtestData.error && (
          <p className="text-sm text-red mt-2">{backtestData.error}</p>
        )}
      </div>
    </div>
  );
}
