"""
benchmark.py
============
Runs Naive and Rabin-Karp on identical inputs, records operation counts and
wall-clock time, writes a CSV, a text summary, and four charts into ./outputs.

    python benchmark.py

Everything is seeded, so the operation COUNTS are exactly reproducible.
Wall-clock times depend on your machine (they are the minimum of several runs).

Experiments
-----------
  1. Scaling with text length n, four input families:
       random text        - average case
       Naive best case    - first pattern char never matches
       Naive worst case   - pattern 'aaa...ab' on text 'aaa...a'
       all windows match  - pattern 'aaa...a' on text 'aaa...a' (worst case for BOTH)
  2. Spurious hits versus the modulus q
  3. Effect of pattern length m
"""

import csv
import os
import random
import time

import matplotlib

matplotlib.use("Agg")  # no display needed; we only save PNG files
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter

from matchers import naive_search, rabin_karp_search

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
SEED = 2026
ALPHABET = "abcdefghijklmnopqrstuvwxyz"

# ---- chart styling (validated blue/orange pair, light surface) -------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e1"
C_RK = "#2a78d6"     # Rabin-Karp  (blue)
C_NAIVE = "#eb6834"  # Naive       (orange)
C_REF = "#8a8984"    # reference / expected curves (neutral)

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": INK_2, "axes.labelcolor": INK_2, "text.color": INK,
    "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "font.size": 10, "axes.titlesize": 11,
    "axes.titleweight": "bold", "axes.titlelocation": "left",
})
thousands = FuncFormatter(lambda v, _: f"{int(v):,}")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def best_time_ms(fn, text, pattern, repeats=5, **kw):
    """Minimum wall-clock time over several runs, in milliseconds."""
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn(text, pattern, **kw)
        best = min(best, time.perf_counter() - t0)
    return best * 1000


def run_both(text, pattern, **rk_kw):
    """Run both algorithms; return (naive_result, rk_result, naive_ms, rk_ms)."""
    nv = naive_search(text, pattern)
    rk = rabin_karp_search(text, pattern, **rk_kw)
    assert nv.matches == rk.matches, "algorithms disagree - bug!"
    return (nv, rk,
            best_time_ms(naive_search, text, pattern),
            best_time_ms(rabin_karp_search, text, pattern, **rk_kw))


def make_random(n, m, rng):
    text = "".join(rng.choice(ALPHABET) for _ in range(n))
    pattern = "".join(rng.choice(ALPHABET) for _ in range(m))
    return text, pattern


SCENARIOS = {
    "random":    ("Random text (average case)",
                  lambda n, m, rng: make_random(n, m, rng)),
    "best":      ("Best case for Naive",
                  lambda n, m, rng: ("a" * n, "b" + "a" * (m - 1))),
    "worst":     ("Worst case for Naive",
                  lambda n, m, rng: ("a" * n, "a" * (m - 1) + "b")),
    "all_match": ("Every window matches (worst for both)",
                  lambda n, m, rng: ("a" * n, "a" * m)),
}

CSV_FIELDS = ["experiment", "scenario", "n", "m", "q", "algorithm", "matches",
              "char_comparisons", "hash_comparisons", "hash_updates",
              "preprocessing_ops", "spurious_hits", "total_ops", "time_ms"]


def row(experiment, scenario, n, m, q, res, ms):
    return dict(experiment=experiment, scenario=scenario, n=n, m=m, q=q,
                algorithm=res.algorithm, matches=len(res.matches),
                char_comparisons=res.char_comparisons,
                hash_comparisons=res.hash_comparisons,
                hash_updates=res.hash_updates,
                preprocessing_ops=res.preprocessing_ops,
                spurious_hits=res.spurious_hits, total_ops=res.total_ops,
                time_ms=round(ms, 3))


def style_axes(ax, xlabel, ylabel, title):
    ax.set_title(title, color=INK)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(thousands)


# ---------------------------------------------------------------------------
# Experiment 1: scaling with n
# ---------------------------------------------------------------------------
def experiment_scaling(rows, log):
    ns = [1000, 2000, 4000, 8000, 16000]
    m = 20
    rng = random.Random(SEED)
    data = {}  # scenario -> dict of series
    log.append(f"EXPERIMENT 1: scaling with text length n   (m = {m}, d = 256, q = 101)")
    log.append("-" * 96)
    log.append(f"{'scenario':<38}{'n':>7}{'naive chars':>13}{'RK chars':>10}"
               f"{'RK all ops':>12}{'RK spur.':>9}{'naive ms':>10}{'RK ms':>9}")
    for key, (label, make) in SCENARIOS.items():
        series = {"n": [], "naive_c": [], "rk_c": [], "rk_all": [], "naive_t": [], "rk_t": []}
        for n in ns:
            text, pat = make(n, m, rng)
            nv, rk, t_nv, t_rk = run_both(text, pat)
            rows.append(row("scaling", key, n, m, 101, nv, t_nv))
            rows.append(row("scaling", key, n, m, 101, rk, t_rk))
            series["n"].append(n)
            series["naive_c"].append(nv.char_comparisons)
            series["rk_c"].append(rk.char_comparisons)
            series["rk_all"].append(rk.total_ops)
            series["naive_t"].append(t_nv)
            series["rk_t"].append(t_rk)
            log.append(f"{label:<38}{n:>7,}{nv.char_comparisons:>13,}{rk.char_comparisons:>10,}"
                       f"{rk.total_ops:>12,}{rk.spurious_hits:>9}{t_nv:>10.2f}{t_rk:>9.2f}")
        data[key] = series
        log.append("")
    return data


def legend_handles():
    return [
        Line2D([0], [0], color=C_NAIVE, lw=2, marker="o", ms=6, label="Naive: character comparisons"),
        Line2D([0], [0], color=C_RK, lw=2, marker="s", ms=6, label="Rabin-Karp: character comparisons"),
        Line2D([0], [0], color=C_RK, lw=2, ls="--", marker="s", ms=6, mfc=SURFACE,
               label="Rabin-Karp: ALL counted operations (hashing included)"),
    ]


def chart_scaling_operations(data):
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8), constrained_layout=True)
    for ax, (key, (label, _)) in zip(axes.flat, SCENARIOS.items()):
        s = data[key]
        ax.plot(s["n"], s["naive_c"], color=C_NAIVE, lw=2, marker="o", ms=6)
        ax.plot(s["n"], s["rk_c"], color=C_RK, lw=2, marker="s", ms=6)
        ax.plot(s["n"], s["rk_all"], color=C_RK, lw=2, ls="--", marker="s", ms=6, mfc=SURFACE)
        style_axes(ax, "text length n", "operations", label)
        ax.xaxis.set_major_formatter(thousands)
        ax.set_ylim(bottom=0)
    fig.suptitle("Operation counts for the same input (pattern length m = 20)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold", color=INK)
    fig.legend(handles=legend_handles(), loc="outside lower center", ncol=3,
               frameon=False, fontsize=9)
    fig.savefig(os.path.join(OUT_DIR, "fig1_operation_counts_vs_n.png"), dpi=160)
    plt.close(fig)


def chart_scaling_time(data):
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 8), constrained_layout=True)
    for ax, (key, (label, _)) in zip(axes.flat, SCENARIOS.items()):
        s = data[key]
        ax.plot(s["n"], s["naive_t"], color=C_NAIVE, lw=2, marker="o", ms=6)
        ax.plot(s["n"], s["rk_t"], color=C_RK, lw=2, marker="s", ms=6)
        style_axes(ax, "text length n", "time (ms)", label)
        ax.xaxis.set_major_formatter(thousands)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_ylim(bottom=0)
    fig.suptitle("Measured running time, pure Python (best of 5 runs)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold", color=INK)
    handles = [
        Line2D([0], [0], color=C_NAIVE, lw=2, marker="o", ms=6, label="Naive"),
        Line2D([0], [0], color=C_RK, lw=2, marker="s", ms=6, label="Rabin-Karp"),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=2, frameon=False, fontsize=9)
    fig.savefig(os.path.join(OUT_DIR, "fig2_running_time_vs_n.png"), dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experiment 2: spurious hits vs q
# ---------------------------------------------------------------------------
def experiment_spurious(rows, log):
    n, m = 20000, 6
    qs = [3, 5, 7, 11, 13, 31, 61, 101, 251, 503, 1009, 10007]
    rng = random.Random(SEED + 1)
    text = "".join(rng.choice("abcdefghij") for _ in range(n))
    pattern = "".join(rng.choice("abcdefghij") for _ in range(m))
    log.append(f"EXPERIMENT 2: spurious hits vs modulus q   (n = {n:,}, m = {m}, d = 256, 10-letter alphabet)")
    log.append("-" * 96)
    log.append(f"{'q':>8}{'spurious hits':>16}{'(n-m+1)/q estimate':>22}{'RK char cmps':>15}{'naive char cmps':>17}")
    spurious, naive_cmp = [], naive_search(text, pattern).char_comparisons
    for q in qs:
        rk = rabin_karp_search(text, pattern, q=q)
        assert rk.matches == naive_search(text, pattern).matches
        rows.append(row("spurious_vs_q", "random10", n, m, q, rk, 0.0))
        spurious.append(rk.spurious_hits)
        log.append(f"{q:>8}{rk.spurious_hits:>16,}{(n - m + 1) / q:>22,.1f}"
                   f"{rk.char_comparisons:>15,}{naive_cmp:>17,}")
    log.append("")
    return qs, spurious, n - m + 1


def chart_spurious(qs, spurious, windows):
    fig, ax = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    est = [windows / q for q in qs]
    ax.plot(qs, est, color=C_REF, lw=1.5, ls="--")
    ax.plot(qs, spurious, color=C_RK, lw=2, marker="s", ms=6)
    ax.set_xscale("log")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_ylim(0, max(spurious[0], est[0]) * 2.2)
    style_axes(ax, "modulus q (log scale)", "spurious hits (symlog scale)",
               "Larger modulus -> fewer spurious hits")
    ax.set_xticks(qs)
    ax.set_xticklabels([str(q) for q in qs], rotation=45, fontsize=8)
    ax.minorticks_off()
    ax.legend(handles=[
        Line2D([0], [0], color=C_RK, lw=2, marker="s", ms=6, label="measured spurious hits"),
        Line2D([0], [0], color=C_REF, lw=1.5, ls="--", label="estimate (n - m + 1) / q"),
    ], loc="upper right", frameon=False, fontsize=9)
    fig.savefig(os.path.join(OUT_DIR, "fig3_spurious_hits_vs_q.png"), dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Experiment 3: effect of pattern length m (Naive worst-case family)
# ---------------------------------------------------------------------------
def experiment_pattern_length(rows, log):
    n = 10000
    ms = [2, 5, 10, 20, 40, 80, 160]
    log.append(f"EXPERIMENT 3: effect of pattern length m   (n = {n:,}, text 'a'*n, pattern 'a'*(m-1)+'b')")
    log.append("-" * 96)
    log.append(f"{'m':>6}{'naive chars':>14}{'(n-m+1)*m':>14}{'RK chars':>11}{'RK all ops':>13}")
    out = {"m": ms, "naive": [], "rk_c": [], "rk_all": []}
    for m in ms:
        text, pat = "a" * n, "a" * (m - 1) + "b"
        nv, rk, t_nv, t_rk = run_both(text, pat)
        rows.append(row("pattern_length", "worst", n, m, 101, nv, t_nv))
        rows.append(row("pattern_length", "worst", n, m, 101, rk, t_rk))
        out["naive"].append(nv.char_comparisons)
        out["rk_c"].append(rk.char_comparisons)
        out["rk_all"].append(rk.total_ops)
        log.append(f"{m:>6}{nv.char_comparisons:>14,}{(n - m + 1) * m:>14,}"
                   f"{rk.char_comparisons:>11,}{rk.total_ops:>13,}")
    log.append("")
    return out


def chart_pattern_length(d):
    fig, ax = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    ax.plot(d["m"], d["naive"], color=C_NAIVE, lw=2, marker="o", ms=6)
    ax.plot(d["m"], d["rk_c"], color=C_RK, lw=2, marker="s", ms=6)
    ax.plot(d["m"], d["rk_all"], color=C_RK, lw=2, ls="--", marker="s", ms=6, mfc=SURFACE)
    style_axes(ax, "pattern length m", "operations",
               "Naive cost grows with m; Rabin-Karp cost stays near 2n")
    ax.xaxis.set_major_formatter(thousands)
    ax.set_ylim(bottom=0)
    ax.annotate("Naive: character comparisons", (d["m"][-1], d["naive"][-1]),
                textcoords="offset points", xytext=(-8, -16), ha="right", color=INK_2, fontsize=9)
    ax.annotate("Rabin-Karp: about 2n operations in total (dashed), 0 character comparisons (solid)",
                (d["m"][-1], d["rk_all"][-1]), textcoords="offset points",
                xytext=(0, 14), ha="right", color=INK_2, fontsize=9)
    fig.savefig(os.path.join(OUT_DIR, "fig4_operations_vs_pattern_length.png"), dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    rows, log = [], []

    data = experiment_scaling(rows, log)
    qs, spurious, windows = experiment_spurious(rows, log)
    plen = experiment_pattern_length(rows, log)

    chart_scaling_operations(data)
    chart_scaling_time(data)
    chart_spurious(qs, spurious, windows)
    chart_pattern_length(plen)

    with open(os.path.join(OUT_DIR, "benchmark_results.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)

    summary = "\n".join(log)
    with open(os.path.join(OUT_DIR, "benchmark_summary.txt"), "w") as fh:
        fh.write(summary + "\n")
    print(summary)
    print(f"Saved CSV, summary and 4 charts to {OUT_DIR}")


if __name__ == "__main__":
    main()
