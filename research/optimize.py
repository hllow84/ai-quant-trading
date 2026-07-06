"""
optimize.py — Parameter grid search with plateau selection (spec §8.1).

Never argmax.  The objective surface is smoothed (neighbour mean), then the
largest contiguous region above threshold is found.  The selected cell is the
one inside that region whose local neighbourhood has the highest minimum value —
the most "interior" point of the plateau, not the lucky peak.

A one-cell plateau is reported as a red flag, not a result.
The count of configurations tested is fed into the Deflated Sharpe Ratio.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Any, Callable

import numpy as np
import pandas as pd

from research.walkforward import run as _wf_run
from research.metrics import deflated_sharpe_ratio


# ── Surface smoothing ─────────────────────────────────────────────────────────

def _smooth_surface(grid: np.ndarray) -> np.ndarray:
    """
    Replace each cell with the mean of its 3×3 neighbourhood (itself + up to 8
    neighbours).  Edge cells use smaller neighbourhoods.  NaN values are excluded
    from the mean but do not make the output NaN unless all neighbours are NaN.
    """
    R, C = grid.shape
    out  = np.full_like(grid, np.nan, dtype=float)
    for i in range(R):
        for j in range(C):
            patch = grid[max(0, i - 1):i + 2, max(0, j - 1):j + 2].astype(float)
            valid = patch[np.isfinite(patch)]
            out[i, j] = float(valid.mean()) if len(valid) > 0 else np.nan
    return out


# ── Plateau finder ────────────────────────────────────────────────────────────

def _find_largest_plateau(
    smoothed:  np.ndarray,
    threshold: float,
) -> tuple[np.ndarray, int, int]:
    """
    Find the largest connected component of cells with smoothed value ≥ threshold.
    Within that component, select the cell whose 3×3 neighbourhood has the highest
    minimum value (the most central / least exposed cell).

    Returns
    -------
    (plateau_mask, best_row, best_col)
        plateau_mask : bool array, True for all cells in the largest component
        best_row, best_col : the selected cell inside the plateau
    """
    R, C     = smoothed.shape
    above    = np.isfinite(smoothed) & (smoothed >= threshold)
    visited  = np.zeros((R, C), dtype=bool)
    comps: list[list[tuple[int, int]]] = []

    # 8-connected BFS to find all components above threshold
    for si in range(R):
        for sj in range(C):
            if above[si, sj] and not visited[si, sj]:
                comp: list[tuple[int, int]] = []
                queue = [(si, sj)]
                visited[si, sj] = True
                while queue:
                    ci, cj = queue.pop(0)
                    comp.append((ci, cj))
                    for di in (-1, 0, 1):
                        for dj in (-1, 0, 1):
                            ni, nj = ci + di, cj + dj
                            if (0 <= ni < R and 0 <= nj < C
                                    and above[ni, nj]
                                    and not visited[ni, nj]):
                                visited[ni, nj] = True
                                queue.append((ni, nj))
                comps.append(comp)

    # Fallback: no cell above threshold — return the single argmax cell
    if not comps:
        flat = np.where(np.isfinite(smoothed), smoothed, -np.inf)
        idx  = np.unravel_index(np.argmax(flat), smoothed.shape)
        mask = np.zeros((R, C), dtype=bool)
        mask[idx] = True
        return mask, int(idx[0]), int(idx[1])

    # Pick the largest component
    largest = max(comps, key=len)

    mask = np.zeros((R, C), dtype=bool)
    for (i, j) in largest:
        mask[i, j] = True

    # Within the largest component, select the cell with the highest
    # minimum-neighbourhood value (spec: "centre of the largest contiguous region")
    best_cell     = largest[0]
    best_min_nbr  = -np.inf
    for (i, j) in largest:
        patch    = smoothed[max(0, i - 1):i + 2, max(0, j - 1):j + 2]
        valid    = patch[np.isfinite(patch)]
        min_nbr  = float(valid.min()) if len(valid) > 0 else -np.inf
        if min_nbr > best_min_nbr:
            best_min_nbr = min_nbr
            best_cell    = (i, j)

    return mask, best_cell[0], best_cell[1]


# ── Result ────────────────────────────────────────────────────────────────────

@dataclass
class OptimizeResult:
    param1_name:    str
    param2_name:    str
    param1_values:  list
    param2_values:  list
    sharpe_grid:    np.ndarray     # (n_p1, n_p2) raw CV Sharpes
    smoothed_grid:  np.ndarray     # (n_p1, n_p2) neighbour-smoothed
    plateau_mask:   np.ndarray     # (n_p1, n_p2) bool
    best_row:       int
    best_col:       int
    best_params:    dict
    plateau_size:   int
    threshold:      float
    n_configs:      int

    @property
    def best_cv_sharpe(self) -> float:
        return float(self.sharpe_grid[self.best_row, self.best_col])

    def report(self) -> str:
        dsr_prob, e_max_sr = deflated_sharpe_ratio(
            sr_best   = self.best_cv_sharpe,
            sr_trials = self.sharpe_grid.flatten().tolist(),
            n_obs     = 1,     # placeholder; caller should pass actual OOS n_obs
        )
        flag = "  ⚠ ONE-CELL PLATEAU — treat as overfit" if self.plateau_size == 1 else ""
        lines = [
            "Optimisation report",
            "=" * 52,
            f"Grid shape:     {self.sharpe_grid.shape[0]} × {self.sharpe_grid.shape[1]}  "
            f"({self.n_configs} configs)",
            f"Threshold:      {self.threshold:.3f}",
            f"Plateau size:   {self.plateau_size} cells{flag}",
            f"Best params:    {self.best_params}",
            f"Best CV Sharpe: {self.best_cv_sharpe:.3f}  (raw, pre-DSR)",
            "-" * 52,
            "Smoothed grid (rows = param1, cols = param2):",
        ]
        for i, v1 in enumerate(self.param1_values):
            row_str = "  ".join(
                f"{self.smoothed_grid[i, j]:>6.3f}"
                + ("*" if (i == self.best_row and j == self.best_col) else " ")
                for j in range(len(self.param2_values))
            )
            lines.append(f"  {v1:>8}: {row_str}")
        lines.append(
            f"  {'':>8}  "
            + "  ".join(f"{v:>6}" for v in self.param2_values)
        )
        lines.append(f"  param2 = {self.param2_name}")
        return "\n".join(lines)


# ── Heatmap ───────────────────────────────────────────────────────────────────

def plot_heatmap(
    result:     "OptimizeResult",
    save_path:  str | None = None,
) -> None:
    """
    2-D heatmap of the raw CV Sharpe grid with the plateau contoured and the
    selected cell marked with a star.  Saves to file if save_path is given,
    otherwise shows interactively.
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("matplotlib not available — skipping heatmap.")
        return

    grid    = result.sharpe_grid
    mask    = result.plateau_mask
    p1      = result.param1_values
    p2      = result.param2_values
    br, bc  = result.best_row, result.best_col

    fig, ax = plt.subplots(figsize=(7, 5))

    vmin = np.nanmin(grid)
    vmax = np.nanmax(grid)
    im   = ax.imshow(
        grid, aspect="auto", origin="upper",
        cmap="RdYlGn", vmin=vmin, vmax=vmax,
        extent=[-0.5, len(p2) - 0.5, len(p1) - 0.5, -0.5],
    )
    plt.colorbar(im, ax=ax, label="CV Sharpe")

    # Highlight plateau cells with a light hatching overlay
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            if mask[i, j]:
                rect = mpatches.Rectangle(
                    (j - 0.5, i - 0.5), 1, 1,
                    linewidth=1.5, edgecolor="white", facecolor="none",
                    linestyle="--",
                )
                ax.add_patch(rect)

    # Star at the selected cell
    ax.plot(bc, br, marker="*", color="white", markersize=14,
            markeredgecolor="black", markeredgewidth=0.8, zorder=5)

    ax.set_xticks(range(len(p2)))
    ax.set_xticklabels([str(v) for v in p2], fontsize=8)
    ax.set_yticks(range(len(p1)))
    ax.set_yticklabels([str(v) for v in p1], fontsize=8)
    ax.set_xlabel(result.param2_name)
    ax.set_ylabel(result.param1_name)
    ax.set_title(
        f"Walk-forward CV Sharpe  |  plateau={result.plateau_size} cells  "
        f"|  best={result.best_params}"
    )

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=120)
    else:
        plt.show()
    plt.close()


# ── Main entry point ──────────────────────────────────────────────────────────

def run(
    factor:         pd.Series,
    asset_returns:  pd.Series,
    make_signal:    Callable[..., pd.Series],
    param_grid:     dict[str, list[Any]],
    funding_rates:  pd.Series | None = None,
    wf_kwargs:      dict | None = None,
    threshold:      float | None = None,
    bars_per_year:  int = 8_760,
) -> OptimizeResult:
    """
    Grid search over param_grid, evaluating walk-forward CV Sharpe for each combo.
    Selects the plateau centre, never the argmax.  Feed n_configs into DSR.

    Parameters
    ----------
    factor, asset_returns : same as walkforward.run()
    make_signal : callable(norm_factor, **params) → signal series
    param_grid  : exactly two keys, each mapping to a list of values.
                  Example: {"z_entry": [1.5, 2.0, 2.5], "window": [72, 168, 336]}
    wf_kwargs   : extra keyword args forwarded to walkforward.run()
    threshold   : plateau threshold on the smoothed Sharpe surface;
                  defaults to max(smoothed) - 0.3 if None
    """
    if len(param_grid) != 2:
        raise ValueError(
            f"param_grid must have exactly 2 keys for a 2-D heatmap; "
            f"got {list(param_grid.keys())}"
        )

    (p1_name, p1_vals), (p2_name, p2_vals) = list(param_grid.items())
    n1, n2   = len(p1_vals), len(p2_vals)
    n_configs = n1 * n2
    wf_kw    = wf_kwargs or {}
    grid     = np.full((n1, n2), np.nan, dtype=float)

    for i, v1 in enumerate(p1_vals):
        for j, v2 in enumerate(p2_vals):
            params   = {p1_name: v1, p2_name: v2}
            def _make(norm, _p=params): return make_signal(norm, **_p)
            try:
                res      = _wf_run(
                    factor, asset_returns, _make,
                    funding_rates=funding_rates,
                    bars_per_year=bars_per_year,
                    **wf_kw,
                )
                grid[i, j] = res.cv_sharpe
            except Exception:
                grid[i, j] = np.nan

    smoothed = _smooth_surface(grid)

    if threshold is None:
        finite_max = float(np.nanmax(smoothed)) if np.any(np.isfinite(smoothed)) else 0.0
        threshold  = finite_max - 0.3

    plateau_mask, best_row, best_col = _find_largest_plateau(smoothed, threshold)

    best_params = {
        p1_name: p1_vals[best_row],
        p2_name: p2_vals[best_col],
    }

    return OptimizeResult(
        param1_name   = p1_name,
        param2_name   = p2_name,
        param1_values = list(p1_vals),
        param2_values = list(p2_vals),
        sharpe_grid   = grid,
        smoothed_grid = smoothed,
        plateau_mask  = plateau_mask,
        best_row      = best_row,
        best_col      = best_col,
        best_params   = best_params,
        plateau_size  = int(plateau_mask.sum()),
        threshold     = threshold,
        n_configs     = n_configs,
    )
