"""
trace.py
========
Step-by-step execution traces of the two algorithms on the SAME input.
This is what lets you see the difference in how they work:
the trace shows, shift by shift, what each algorithm actually does.

The traces re-run the same logic as matchers.py but record a line per shift.
test_matchers.py checks that the trace finds exactly the same matches
and the same comparison counts as the real implementations, so the trace
cannot drift away from the real algorithms.
"""

from typing import List, Tuple

from matchers import DEFAULT_MODULUS, DEFAULT_RADIX, _validate

MAX_TRACE_TEXT_LEN = 80  # keep traces readable in a terminal


def _window_marker(n: int, s: int, m: int) -> str:
    """A line of spaces and '^' that underlines the current window."""
    return " " * s + "^" * m + " " * (n - s - m)


def trace_naive(text: str, pattern: str) -> Tuple[List[str], List[int], int]:
    """Return (trace_lines, matches, total_char_comparisons)."""
    _validate(text, pattern)
    n, m = len(text), len(pattern)
    lines: List[str] = []
    matches: List[int] = []
    total = 0

    lines.append(f"NAIVE trace   n={n}  m={m}  shifts to try = n-m+1 = {max(n - m + 1, 0)}")
    lines.append(f"  T =  {text}")
    for s in range(n - m + 1):
        j = 0
        steps = []
        while j < m:
            total += 1
            if text[s + j] == pattern[j]:
                steps.append(f"{text[s + j]}=={pattern[j]}")
                j += 1
            else:
                steps.append(f"{text[s + j]}!={pattern[j]}")
                break
        outcome = "MATCH" if j == m else "mismatch"
        if j == m:
            matches.append(s)
        lines.append(f"  s={s:<3}{_window_marker(n, s, m)}")
        lines.append(f"       compares: {' '.join(steps)}  -> {len(steps)} comparison(s), {outcome}")
    lines.append(f"  Result: matches at {matches}   total character comparisons = {total}")
    return lines, matches, total


def trace_rabin_karp(
    text: str,
    pattern: str,
    d: int = DEFAULT_RADIX,
    q: int = DEFAULT_MODULUS,
) -> Tuple[List[str], List[int], int]:
    """Return (trace_lines, matches, total_char_comparisons)."""
    _validate(text, pattern)
    n, m = len(text), len(pattern)
    lines: List[str] = []
    matches: List[int] = []
    char_cmp = 0
    spurious = 0

    lines.append(f"RABIN-KARP trace   n={n}  m={m}  d={d}  q={q}")
    if m > n:
        lines.append("  Pattern longer than text: no shifts to try.")
        return lines, matches, 0

    h = pow(d, m - 1, q)
    p_hash = t_hash = 0
    for i in range(m):
        p_hash = (d * p_hash + ord(pattern[i])) % q
        t_hash = (d * t_hash + ord(text[i])) % q
    lines.append(f"  h = d^(m-1) mod q = {h}      hash(P) = {p_hash}")
    lines.append(f"  T = {text}")

    for s in range(n - m + 1):
        window = text[s:s + m]
        row = f"  s={s:<3}window='{window}'  hash={t_hash:<4}"
        if t_hash != p_hash:
            row += f"!= {p_hash}  -> hashes differ, NO character comparison"
        else:
            j = 0
            while j < m:
                char_cmp += 1
                if text[s + j] != pattern[j]:
                    break
                j += 1
            if j == m:
                matches.append(s)
                row += f"== {p_hash}  -> hashes equal, verified {m} chars: MATCH"
            else:
                spurious += 1
                row += (f"== {p_hash}  -> hashes equal, verified {j + 1} char(s): "
                        f"strings differ => SPURIOUS HIT")
        lines.append(row)
        if s < n - m:
            new_hash = (d * (t_hash - ord(text[s]) * h) + ord(text[s + m])) % q
            lines.append(f"       roll: drop '{text[s]}', add '{text[s + m]}'  -> next hash = {new_hash}")
            t_hash = new_hash

    lines.append(
        f"  Result: matches at {matches}   spurious hits = {spurious}   "
        f"total character comparisons = {char_cmp}"
    )
    return lines, matches, char_cmp
