# AGENTS.md — Scope & Exclusion Rules

## In scope
- Build and maintain modules under `data/`, `research/`, `tests/`.
- Fetch free exchange-native data via ccxt (Binance/Bybit as reference venues).
- Run the factor analysis workflow per `FACTOR_RESEARCH_HARNESS_SPEC.md` §9.
- Self-verify against acceptance tests in `tests/test_harness.py` before reporting results.

## Out of scope (do not implement without explicit instruction)
- `data/adapters/glassnode_adapter.py` — only when a free-tier factor is exhausted.
- Any live trading, order placement, or execution logic.
- QuantConnect, vectorbt, yfinance — permanently ruled out.

## Autonomy rules
- Run autonomously and self-correct against acceptance tests.
- Stop and ask only when a design decision is genuinely ambiguous.
- Never report a Sharpe before costs are applied.
- Never report an optimized result without its plateau.
- Always apply the deflated Sharpe haircut and report both raw and deflated.
