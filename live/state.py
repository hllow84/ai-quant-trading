"""
state.py -- small local JSON state file: peak equity (for the kill switch),
kill-switch status, and rebalance counters (for the paper-trading gate and the
manual-review gate). Not committed to git (live/state/ is git-ignored).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from live.config import STATE_DIR

STATE_FILE = STATE_DIR / "state.json"

DEFAULT_STATE = {
    "peak_equity": None,
    "kill_switch_active": False,
    "kill_switch_triggered_at": None,
    "kill_switch_drawdown": None,
    "paper_rebalance_count": 0,
    "total_rebalance_count": 0,
    "last_rebalance_date": None,
    "consecutive_bad_monitor_runs": 0,
}


def load_state() -> dict:
    if not STATE_FILE.exists():
        return dict(DEFAULT_STATE)
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    # forward-fill any keys added since this state file was written
    for k, v in DEFAULT_STATE.items():
        state.setdefault(k, v)
    return state


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
