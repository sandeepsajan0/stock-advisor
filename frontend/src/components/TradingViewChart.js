"use client";

import React, { useEffect, useRef } from 'react';
import { createChart, CrosshairMode } from 'lightweight-charts';

export default function TradingViewChart({ chartData, tradesData }) {
  const chartContainerRef = useRef();

  useEffect(() => {
    if (!chartData || chartData.length === 0) return;

    // Create Chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: '#cbd5e1',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
      },
      autoSize: true,
    });

    // Format candlestick data
    const candleData = chartData.map(d => ({
      time: d.Date,
      open: d.Open,
      high: d.High,
      low: d.Low,
      close: d.Close,
    }));

    // Add Candlestick Series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#4ade80',
      downColor: '#f87171',
      borderVisible: false,
      wickUpColor: '#4ade80',
      wickDownColor: '#f87171',
    });
    candlestickSeries.setData(candleData);

    // Add SMA 5 (if exists)
    if (chartData[0].SMA_5_HA !== undefined) {
      const sma5Data = chartData
        .filter(d => d.SMA_5_HA !== null)
        .map(d => ({ time: d.Date, value: d.SMA_5_HA }));
      
      const sma5Series = chart.addLineSeries({
        color: '#e879f9',
        lineWidth: 2,
        title: 'SMA 5',
      });
      sma5Series.setData(sma5Data);
    }

    // Add SMA 20 (if exists)
    if (chartData[0].SMA_20_HA !== undefined) {
      const sma20Data = chartData
        .filter(d => d.SMA_20_HA !== null)
        .map(d => ({ time: d.Date, value: d.SMA_20_HA }));
        
      const sma20Series = chart.addLineSeries({
        color: '#60a5fa',
        lineWidth: 2,
        title: 'SMA 20',
      });
      sma20Series.setData(sma20Data);
    }

    // Add Markers for Trades
    if (tradesData && tradesData.length > 0) {
      const markers = [];
      tradesData.forEach(trade => {
        // Entry Marker
        markers.push({
          time: trade.entry_date.split(' ')[0],
          position: trade.direction === 'long' ? 'belowBar' : 'aboveBar',
          color: trade.direction === 'long' ? '#4ade80' : '#f87171',
          shape: trade.direction === 'long' ? 'arrowUp' : 'arrowDown',
          text: `Entry ${trade.direction === 'long' ? 'Buy' : 'Short'} @ ${trade.entry_price}`,
        });

        // Exit Marker
        if (trade.exit_date) {
            markers.push({
              time: trade.exit_date.split(' ')[0],
              position: trade.direction === 'long' ? 'aboveBar' : 'belowBar',
              color: trade.profit_loss_pct > 0 ? '#4ade80' : '#f87171',
              shape: trade.direction === 'long' ? 'arrowDown' : 'arrowUp',
              text: `Exit ${trade.exit_reason} @ ${trade.exit_price}`,
            });
        }
      });
      
      // Sort markers by time (required by lightweight-charts)
      markers.sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime());
      candlestickSeries.setMarkers(markers);
    }

    chart.timeScale().fitContent();

    // Resize observer
    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [chartData, tradesData]);

  return (
    <div
      ref={chartContainerRef}
      style={{ width: '100%', height: '400px', margin: '1rem 0' }}
    />
  );
}
