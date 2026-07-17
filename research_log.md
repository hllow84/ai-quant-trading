# Research Log

All tested strategies and factors. Updated every session.

| date | strategy | instrument | timeframe | key params | result (PF/Sharpe/verdict) | notes |
|------|----------|------------|-----------|------------|----------------------------|-------|
| 2026-06-14 | ICT SMC Full Model (FTMO) | XAUUSD | H4 | sweep→OB/FVG→kill-zone entry, 1.5R TP, SL below OB, RR 1.5 | PF 2.19, 49 trades | Gold-only filter applied; weak absolute return given low trade count; needs spread + FTMO rule simulation |
| 2026-06-14 | ICT SMC Full Model (FTMO) | EURUSD | H4 | same params, pc_sym=EURUSD default | PF 0.98 | Below breakeven after spread; no edge on EURUSD H4 |
| 2026-06-14 | ICT SMC Full Model (FTMO) | EURUSD | H1 | same model, H1 bar | PF 0.58 | Worse than H4; finer timeframe amplifies noise |
| 2026-07-10 | SMA-200 long-only baseline | XAUUSD | Daily | window=200, no params to tune | Net Sharpe 0.665, Gross Sharpe 0.673, MDD ~27%, n_configs=1 | yfinance GC=F (futures) used — PROVISIONAL/SUPERSEDED; replaced by real SPOT run below. Cost: 4 bps fee. Look-ahead guard PASS. |
| 2026-07-17 | SMA-200 long-only baseline (REAL SPOT) | XAUUSD | Daily | window=200, no params to tune | Net Sharpe **1.127** (Gross 1.135), MDD 26.2%, CAGR 17.6%, 19 entries, n_configs=1 | Real Dukascopy M1 SPOT → daily (1,602 bars, 2018-2025). Real spread cost @ close (median 2.15 bps round-turn, LOWER than provisional 4 bps). Look-ahead PASS. **KEY: loses to buy-and-hold gold on EVERY metric** — B&H Sharpe 1.194, MDD 20.4%, CAGR 20.7%. SMA-200 timing overlay DESTROYS value (higher DD despite 66.5% exposure — whipsaws back in near tops). Both are pure long-gold beta in a secular bull, not alpha. |
| 2026-07-10 | ICT SMC Full Model v2 (FTMO) | XAUUSD | — | v2 Pine fixes: barstate.isconfirmed, pc_sym=XAUUSD, FVG sweep gate | Not yet backtested | Pine compile fixes applied; pending live TradingView test and systematic backtest with spot data |
