# 📈 Real-Time Crypto Microstructure Dashboard  
### *Live Trade Ingestion • Order Book Analytics • Market Regime Detection • Short-Term Price Prediction*

This project is a **real-time crypto market analytics system** built using:

- WebSockets streaming (Binance)
- Async ingestion pipelines
- Polars for high-performance processing
- Custom microstructure features (VWAP, imbalance, microprice, spread)
- Streamlit for real-time visualization
- A short-term prediction engine (5–10s horizon)
- Market regime classifier (Bullish / Bearish / Neutral)

It replicates the kind of tools used inside **quant trading firms** for internal monitoring and microstructure research — but simplified so it is understandable even to beginners.

---

# 🚀 Features

### ✅ **Real-Time Trade Ingestion**
- Streams every BTC/USDT trade from Binance  
- Writes compact Parquet files every few seconds  
- Zero-latency dashboards

### ✅ **Real-Time Order Book Depth (Level-5)**
- Tracks best bid/ask  
- Computes liquidity imbalance  
- Computes microprice (pressure-adjusted fair value)

### ✅ **Advanced Market Microstructure Metrics**
- VWAP  
- Buy/Sell aggressor flow  
- Volatility (1m, 5m)  
- Spread, mid, microprice  
- Order book imbalance  

### ✅ **Live Market Regime Detector**
Classifies real-time conditions as:

- **Strongly Bullish**
- **Bullish**
- **Neutral**
- **Bearish**
- **Strongly Bearish**

### ✅ **Short-Term Price Prediction (5–10 seconds)**
Uses microstructure signals to estimate:

- **UP**
- **DOWN**
- **NEUTRAL**

(Probabilities module coming soon.)

### ✅ **Streamlit Dashboard**
Auto-refreshing every 1.5s with:

- Price chart  
- Depth analytics  
- Microstructure metrics  
- Liquidity imbalance  
- Prediction + regime  
- Beginner-friendly explanations  

---

# 🏗 Architecture Overview
            ┌──────────────────────────┐
            │    Binance WebSockets     │
            │  - Trades Stream          │
            │  - Order Book Depth       │
            └─────────────┬────────────┘
                          │
            ┌─────────────▼────────────┐
            │   Ingestion Pipelines     │
            │  ingest.py                │
            │  ingest_depth.py          │
            │  - async streaming        │
            │  - batch parquet writes   │
            └─────────────┬────────────┘
                          │
            ┌─────────────▼────────────┐
            │     Data Lake (local)     │
            │  data/raw/*.parquet       │
            └─────────────┬────────────┘
                          │
            ┌─────────────▼────────────┐
            │   Processing Layer        │
            │  process.py               │
            │  process_depth.py         │
            │  - VWAP, volatility       │
            │  - buy/sell flow          │
            │  - order book metrics     │
            │  - imbalance series       │
            └─────────────┬────────────┘
                          │
            ┌─────────────▼────────────┐
            │  Intelligence Layer       │
            │  regime.py                │
            │  predict.py               │
            │  - regime detection       │
            │  - short-term prediction  │
            └─────────────┬────────────┘
                          │
            ┌─────────────▼────────────┐
            │    Streamlit Dashboard    │
            │  live charts + metrics    │
            │  auto-ingestion launcher  │
            └──────────────────────────┘


