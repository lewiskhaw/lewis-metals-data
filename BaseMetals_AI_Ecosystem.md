# Base Metals AI Trading Ecosystem

## Project Overview
A high-performance, modular AI system designed for the analysis and automated trading of base metals (Copper, Zinc, Nickel, Aluminium). This ecosystem focuses on real-time data processing, robust machine learning models, and rigorous risk management.

## System Architecture

### 1. Data Ingestion Layer
- **Real-Time Market Data:** Integration with LME, COMEX via WebSockets for sub-second price updates.
- **Macro Indicators:** Automated fetching of global economic data (GDP, PPI, PMI) impacting metal demand.

### 2. Analytical Engine
- **Feature Engineering:** Calculation of volatility indices, moving averages, and order book imbalance ratios.
- **Prediction Models:** 
  - *Time-Series:* LSTM/GRU networks for short-term price forecasting.
  - *Sentiment:* FinBERT models for analyzing news sentiment regarding mining regulations and geopolitical stability.

### 3. Execution Strategy
- **Signal Processing:** Combining price prediction confidence with sentiment scores to generate trading signals.
- **Risk Management:** Dynamic position sizing (Kelly Criterion) and hard-coded circuit breakers for volatility protection.

## Tech Stack Recommendations
- **Language:** Python 3.10+
- **ML Frameworks:** PyTorch, Scikit-learn
- **Data Libraries:** Pandas, Polars, VectorBT (for backtesting)

## Development Roadmap

| Phase | Milestone | Status |
|-------|-----------|--------|
| 1     | Data Pipeline Setup & Cleaning | Planned |
| 2     | Model Training (Backtesting)   | Planned |
| 3     | Signal Integration             | Planned |
| 4     | Live Deployment                | Future |

## Directory Structure

```bash
/BaseMetals_Ecosystem/
├── /configs      # System configurations and API keys
├── /data         # Raw historical data and processed datasets
├── /models       # Trained model weights (.pt, .h5)
└── /src          # Source code modules
    ├── ingestion.py
    ├── features.py
    └── execution.py
```