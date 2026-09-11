"use client";

import { useState } from 'react';
import StockCard from '@/components/StockCard';
import BacktestPanel from '@/components/BacktestPanel';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [mode, setMode] = useState('swing'); // 'swing', 'intraday', '44sma', 'sma1020'

  const scanMarket = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const res = await fetch(`${apiUrl}/api/scan?mode=${mode}`);
      if (!res.ok) throw new Error('Failed to fetch data from backend');
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError("Unable to reach the backend server. Is the FastAPI server running?");
    } finally {
      setLoading(false);
    }
  };

  const modes = [
    { key: 'swing', label: 'Swing Mode', color: 'var(--primary)' },
    { key: '44sma', label: '44 SMA', color: '#f59e0b' },
    { key: 'sma1020', label: 'SMA 5/20 HA', color: '#e879f9' },
    { key: 'intraday', label: 'Intraday', color: 'var(--secondary)' },
  ];

  const activeMode = modes.find(m => m.key === mode);

  return (
    <main className="container">
      <header className="header">
        <h1>Smart Stock Advisor <span style={{fontSize: '1rem', background: 'var(--accent)', color: '#000', padding: '2px 8px', borderRadius: '12px', verticalAlign: 'middle'}}>V7</span></h1>
        <p>Dynamic Sector-Based Discovery & AI Trading Engine</p>
        
        {/* Strategy Toggle */}
        <div style={{ display: 'flex', justifyContent: 'center', margin: '1.5rem 0' }}>
           <div style={{ display: 'flex', background: 'rgba(255,255,255,0.05)', borderRadius: '8px', padding: '4px', flexWrap: 'wrap', justifyContent: 'center' }}>
              {modes.map(m => (
                <button 
                  key={m.key}
                  onClick={() => setMode(m.key)}
                  style={{
                    background: mode === m.key ? m.color : 'transparent',
                    color: mode === m.key ? '#000' : '#cbd5e1',
                    border: 'none',
                    padding: '8px 20px',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    transition: 'all 0.3s'
                  }}>
                  {m.label}
                </button>
              ))}
           </div>
        </div>

        <button 
          className="btn-primary mt-2" 
          onClick={scanMarket} 
          disabled={loading}
          style={{ 
            background: `linear-gradient(135deg, ${activeMode.color}, ${activeMode.color}88)`
          }}
        >
          {loading ? (
            <><span className="loader"></span> Scanning {activeMode.label}...</>
          ) : (
            `Scan ${activeMode.label} Setups`
          )}
        </button>
      </header>

      {error && <div className="text-red flex-center" style={{ textAlign: 'center' }}>{error}</div>}

      {data && data.market_regime && (
        <div style={{
          background: data.market_regime.status === 'Bullish' ? 'rgba(74, 222, 128, 0.1)' : (data.market_regime.status === 'Bearish' ? 'rgba(248, 113, 113, 0.1)' : 'rgba(255, 255, 255, 0.05)'),
          border: `1px solid ${data.market_regime.status === 'Bullish' ? 'var(--primary)' : (data.market_regime.status === 'Bearish' ? 'var(--danger)' : 'var(--secondary)')}`,
          padding: '1rem',
          borderRadius: '8px',
          marginBottom: '2rem',
          textAlign: 'center'
        }}>
          <h3 style={{ margin: '0 0 0.5rem 0', color: data.market_regime.status === 'Bullish' ? 'var(--primary)' : (data.market_regime.status === 'Bearish' ? 'var(--danger)' : 'var(--secondary)') }}>
            {data.mode === 'intraday' ? 'Intraday ' : ''}Market Regime: {data.market_regime.status}
          </h3>
          <p style={{ margin: 0, color: '#e2e8f0' }}>{data.market_regime.message || 'Status unknown. Trade carefully.'}</p>
        </div>
      )}

      {data && data.sector_health && (
        <div style={{ marginBottom: '2rem' }}>
          <h4 style={{ margin: '0 0 1rem 0', color: '#cbd5e1' }}>Sector Health Overview</h4>
          <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {data.sector_health.map((sec, idx) => (
              <div key={idx} style={{
                background: sec.status === 'Bullish' ? 'rgba(74, 222, 128, 0.1)' : (sec.status === 'Bearish' ? 'rgba(248, 113, 113, 0.1)' : 'rgba(255, 255, 255, 0.05)'),
                border: `1px solid ${sec.status === 'Bullish' ? 'rgba(74, 222, 128, 0.3)' : (sec.status === 'Bearish' ? 'rgba(248, 113, 113, 0.3)' : 'rgba(255, 255, 255, 0.1)')}`,
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                fontSize: '0.9rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <span style={{ color: '#f0f0f5' }}>{sec.name}</span>
                <span style={{ color: sec.status === 'Bullish' ? 'var(--primary)' : (sec.status === 'Bearish' ? 'var(--danger)' : 'var(--secondary)') }}>
                  {sec.status === 'Bullish' ? '↗ Bullish' : (sec.status === 'Bearish' ? '↘ Bearish' : '→ Unknown')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data && data.results && data.results.length === 0 && (
        <div className="flex-center" style={{ flexDirection: 'column', minHeight: '30vh' }}>
          <h2 style={{ color: '#94a3b8' }}>No active setups found</h2>
          <p className="text-sm">Market conditions might not be favorable right now, or no stocks meet the strict algorithm criteria.</p>
        </div>
      )}

      {data && data.results && data.results.length > 0 && (
        <div className="grid">
          {data.results.map((stock, idx) => (
            <StockCard key={idx} data={stock} mode={data.mode} />
          ))}
        </div>
      )}

      {/* Backtest Section */}
      <BacktestPanel />
    </main>
  );
}
