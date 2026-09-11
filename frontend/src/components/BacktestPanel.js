"use client";

import React, { useState } from 'react';

export default function BacktestPanel() {
  const [ticker, setTicker] = useState('');
  const [mode, setMode] = useState('sma1020');
  const [period, setPeriod] = useState('2y');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const runBacktest = async () => {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL !== undefined ? process.env.NEXT_PUBLIC_API_URL : (process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '');
      const res = await fetch(`${apiUrl}/api/backtest/${ticker.trim().toUpperCase()}?mode=${mode}&period=${period}`);
      if (!res.ok) throw new Error('Failed');
      const json = await res.json();
      if (json.error) { setError(json.error); }
      else { setData(json); }
    } catch (err) {
      setError("Unable to reach the backend server.");
    } finally {
      setLoading(false);
    }
  };

  const fmt = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(val);

  const modeLabels = {
    'swing': 'Swing',
    '44sma': '44 SMA',
    'intraday': 'Intraday',
    'sma1020': 'SMA 5/20 HA'
  };

  const modeColors = {
    'swing': 'var(--primary)',
    '44sma': '#f59e0b',
    'intraday': 'var(--secondary)',
    'sma1020': '#e879f9'
  };

  return (
    <div style={{ marginTop: '3rem' }}>
      {/* Section Header */}
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.8rem', margin: '0 0 0.5rem 0', background: 'linear-gradient(135deg, #e879f9, #60a5fa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          📊 Strategy Backtester
        </h2>
        <p className="text-sm">Enter any stock symbol and test it against any strategy with historical data</p>
      </div>

      {/* Input Card */}
      <div className="glass-card" style={{ maxWidth: '700px', margin: '0 auto 2rem auto', borderTop: '3px solid #e879f9' }}>
        <div style={{ display: 'flex', gap: '0.8rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && runBacktest()}
            placeholder="Enter stock (e.g. SBIN, RELIANCE, TCS)"
            style={{
              flex: 1, minWidth: '200px', padding: '12px 16px',
              background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px', color: 'var(--foreground)', fontSize: '1rem',
              outline: 'none', transition: 'border 0.3s'
            }}
          />
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            style={{
              padding: '12px', background: 'rgba(0,0,0,0.4)',
              border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px',
              color: 'var(--foreground)', fontSize: '1rem', outline: 'none'
            }}
          >
            <option value="1y">1 Year</option>
            <option value="2y">2 Years</option>
            <option value="5y">5 Years</option>
            <option value="max">Max Data</option>
          </select>
          
          <button
            onClick={runBacktest}
            disabled={loading || !ticker.trim()}
            className="btn-primary"
            style={{ background: 'linear-gradient(135deg, #e879f9, #a855f7)', whiteSpace: 'nowrap' }}
          >
            {loading ? <><span className="loader" style={{ borderLeftColor: '#fff' }}></span> Running...</> : 'Run Backtest'}
          </button>
        </div>

        {/* Strategy Selector */}
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {Object.entries(modeLabels).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setMode(key)}
              style={{
                padding: '6px 16px', borderRadius: '20px', border: 'none',
                background: mode === key ? modeColors[key] : 'rgba(255,255,255,0.05)',
                color: mode === key ? '#000' : '#94a3b8',
                fontWeight: mode === key ? '700' : '500', cursor: 'pointer',
                fontSize: '0.85rem', transition: 'all 0.3s'
              }}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {error && <p style={{ textAlign: 'center' }} className="text-red">{error}</p>}

      {/* Results */}
      {data && (
        <div style={{ maxWidth: '900px', margin: '0 auto' }}>
          {/* Summary Header */}
          <div className="glass-card" style={{ borderTop: `3px solid ${modeColors[data.mode] || '#e879f9'}`, marginBottom: '1.5rem' }}>
            <div className="flex-between mb-2">
              <div>
                <h3 style={{ margin: 0, fontSize: '1.6rem' }}>{data.ticker.replace('.NS', '')}</h3>
                <span className="text-sm">{modeLabels[data.mode]} Strategy • {period.toUpperCase()} Backtest</span>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '2rem', fontWeight: '800', color: data.total_return_pct > 0 ? 'var(--primary)' : 'var(--danger)' }}>
                  {data.total_return_pct > 0 ? '+' : ''}{data.total_return_pct}%
                </div>
                <span className="text-sm">Total Return</span>
              </div>
            </div>

            {/* Stats Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '1rem', marginTop: '1.5rem' }}>
              <StatBox label="Final Capital" value={fmt(data.final_capital)} color={data.total_return_pct > 0 ? 'var(--primary)' : 'var(--danger)'} />
              <StatBox label="Win Rate" value={`${data.win_rate_pct}%`} color={data.win_rate_pct >= 50 ? 'var(--primary)' : '#f59e0b'} />
              <StatBox label="Total Trades" value={data.total_trades} color="var(--secondary)" />
              <StatBox label="Profit Factor" value={data.profit_factor || '—'} color={data.profit_factor >= 1.5 ? 'var(--primary)' : '#f59e0b'} />
              <StatBox label="Max Drawdown" value={`-${data.max_drawdown_pct}%`} color="var(--danger)" />
              <StatBox label="Avg Win" value={`+${data.avg_win_pct || 0}%`} color="var(--primary)" />
              <StatBox label="Avg Loss" value={`${data.avg_loss_pct || 0}%`} color="var(--danger)" />
              <StatBox label="Won / Lost" value={`${data.winning_trades || 0} / ${data.losing_trades || 0}`} color="var(--foreground)" />
            </div>
          </div>

          {/* Equity Curve */}
          {data.equity_curve && data.equity_curve.length > 0 && (
            <div className="glass-card" style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ margin: '0 0 1rem 0', color: '#cbd5e1' }}>📈 Equity Curve</h4>
              <EquityCurve data={data.equity_curve} initialCapital={data.initial_capital} />
            </div>
          )}

          {/* Trade Log */}
          {data.trades && data.trades.length > 0 && (
            <div className="glass-card">
              <h4 style={{ margin: '0 0 1rem 0', color: '#cbd5e1' }}>📋 Trade Log ({data.trades.length} trades)</h4>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                      <th style={thStyle}>#</th>
                      <th style={thStyle}>Type</th>
                      <th style={thStyle}>Entry Date</th>
                      <th style={thStyle}>Entry ₹</th>
                      <th style={thStyle}>Exit ₹</th>
                      <th style={thStyle}>Exit Reason</th>
                      <th style={thStyle}>P/L %</th>
                      <th style={thStyle}>Capital</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.trades.map((t, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={tdStyle}>{idx + 1}</td>
                        <td style={tdStyle}>
                          <span style={{
                            padding: '2px 8px', borderRadius: '10px', fontSize: '0.75rem', fontWeight: '700',
                            background: (t.direction || 'long') === 'long' ? 'rgba(74, 222, 128, 0.15)' : 'rgba(248, 113, 113, 0.15)',
                            color: (t.direction || 'long') === 'long' ? 'var(--primary)' : 'var(--danger)'
                          }}>
                            {(t.direction || 'long').toUpperCase()}
                          </span>
                        </td>
                        <td style={tdStyle}>{t.entry_date?.split(' ')[0]}</td>
                        <td style={tdStyle}>₹{t.entry_price}</td>
                        <td style={tdStyle}>₹{t.exit_price}</td>
                        <td style={tdStyle}>
                          <span style={{
                            padding: '2px 8px', borderRadius: '10px', fontSize: '0.7rem',
                            background: t.exit_reason === 'Target 1' ? 'rgba(74,222,128,0.1)' : (t.exit_reason === 'Stop Loss' ? 'rgba(248,113,113,0.1)' : 'rgba(255,255,255,0.05)'),
                            color: t.exit_reason === 'Target 1' ? 'var(--primary)' : (t.exit_reason === 'Stop Loss' ? 'var(--danger)' : '#94a3b8')
                          }}>
                            {t.exit_reason}
                          </span>
                        </td>
                        <td style={{ ...tdStyle, color: t.profit_loss_pct > 0 ? 'var(--primary)' : 'var(--danger)', fontWeight: '700' }}>
                          {t.profit_loss_pct > 0 ? '+' : ''}{t.profit_loss_pct}%
                        </td>
                        <td style={tdStyle}>{fmt(t.capital)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// --- Sub-components ---

function StatBox({ label, value, color }) {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.3)', padding: '1rem', borderRadius: '10px',
      textAlign: 'center', border: '1px solid rgba(255,255,255,0.05)'
    }}>
      <div style={{ fontSize: '1.3rem', fontWeight: '800', color }}>{value}</div>
      <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '4px' }}>{label}</div>
    </div>
  );
}

function EquityCurve({ data, initialCapital }) {
  const max = Math.max(...data);
  const min = Math.min(...data, initialCapital);
  const range = max - min || 1;
  const width = 100;
  const height = 80;

  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  // Fill area
  const fillPoints = `0,${height} ${points} ${width},${height}`;

  const finalVal = data[data.length - 1];
  const isUp = finalVal >= initialCapital;

  return (
    <div style={{ position: 'relative' }}>
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: '120px' }} preserveAspectRatio="none">
        <defs>
          <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={isUp ? '#4ade80' : '#f87171'} stopOpacity="0.3" />
            <stop offset="100%" stopColor={isUp ? '#4ade80' : '#f87171'} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <polygon points={fillPoints} fill="url(#eqGrad)" />
        <polyline points={points} fill="none" stroke={isUp ? '#4ade80' : '#f87171'} strokeWidth="0.5" />
        {/* Initial capital line */}
        <line x1="0" y1={height - ((initialCapital - min) / range) * height} x2={width} y2={height - ((initialCapital - min) / range) * height}
              stroke="rgba(255,255,255,0.2)" strokeWidth="0.3" strokeDasharray="2,2" />
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px' }}>
        <span className="text-sm">Start: {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(initialCapital)}</span>
        <span className="text-sm" style={{ color: isUp ? 'var(--primary)' : 'var(--danger)' }}>
          End: {new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(finalVal)}
        </span>
      </div>
    </div>
  );
}

const thStyle = { padding: '8px 10px', textAlign: 'left', color: '#94a3b8', fontWeight: '600', whiteSpace: 'nowrap' };
const tdStyle = { padding: '8px 10px', color: 'var(--foreground)', whiteSpace: 'nowrap' };
