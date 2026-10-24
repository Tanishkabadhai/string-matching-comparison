"""
main.py
=======
Command-line front end: run the Naive and Rabin-Karp algorithms on the SAME
input and print a side-by-side comparison.

Examples
--------
    python main.py --demo                              # 4 prepared scenarios
    python main.py --text "abracadabra" --pattern "abra"
    python main.py --text "abracadabra" --pattern "abra" --trace
    python main.py --text "2359023141526739921" --pattern "31415" --q 13 --trace
    python main.py --file input.txt --pattern "needle"  # read the text from a file
"""

import argparse
import sys

from matchers import DEFAULT_MODULUS, DEFAULT_RADIX, MatchResult, naive_search, rabin_karp_search
from trace import MAX_TRACE_TEXT_LEN, trace_naive, trace_rabin_karp


def _fmt_matches(matches) -> str:
    """Short display of a list of shifts so long lists do not break the table."""
    if len(matches) <= 4:
        return str(matches)
    return "[" + ", ".join(map(str, matches[:3])) + ", ... " + str(matches[-1]) + "]"


def print_comparison(naive: MatchResult, rk: MatchResult) -> None:
    """Side-by-side table of the counters for one input."""
    rows = [
        ("Matches found (shifts)", _fmt_matches(naive.matches), _fmt_matches(rk.matches)),
        ("Number of matches", len(naive.matches), len(rk.matches)),
        ("Character comparisons", naive.char_comparisons, rk.char_comparisons),
        ("Hash comparisons", "-", rk.hash_comparisons),
        ("Rolling-hash updates", "-", rk.hash_updates),
        ("Preprocessing operations", "-", rk.preprocessing_ops),
        ("Spurious hits", "-", rk.spurious_hits),
        ("Total (unweighted sum)", naive.total_ops, rk.total_ops),
    ]
    width = 26
    print(f"  {'Measure':<{width}}{'Naive':>22}{'Rabin-Karp':>22}")
    print("  " + "-" * (width + 44))
    for label, a, b in rows:
        print(f"  {label:<{width}}{str(a):>22}{str(b):>22}")
    agree = "YES" if naive.matches == rk.matches else "NO  <-- BUG"
    print(f"\n  Both algorithms report identical matches: {agree}")


def run_one(text: str, pattern: str, d: int, q: int, show_trace: bool, title: str = "") -> None:
    if title:
        print("=" * 72)
        print(title)
        print("=" * 72)
    shown = text if len(text) <= 60 else text[:57] + "..."
    print(f"  Text    (n={len(text)}): {shown}")
    print(f"  Pattern (m={len(pattern)}): {pattern}")
    print(f"  Rabin-Karp parameters: d={d}, q={q}\n")

    if show_trace:
        if len(text) > MAX_TRACE_TEXT_LEN:
            print(f"  (trace skipped: text longer than {MAX_TRACE_TEXT_LEN} characters)\n")
        else:
            for line in trace_naive(text, pattern)[0]:
                print(line)
            print()
            for line in trace_rabin_karp(text, pattern, d, q)[0]:
                print(line)
            print()

    naive = naive_search(text, pattern)
    rk = rabin_karp_search(text, pattern, d, q)
    print_comparison(naive, rk)
    print()


def demo(d: int, q: int) -> None:
    """Four hand-picked inputs, each chosen to expose one behaviour."""
    run_one(
        "abracadabra#abracadabra", "abra", d, q, True,
        "SCENARIO 1: ordinary text, pattern occurs several times",
    )
    run_one(
        "aaaaaaaaaaaaaaaaaaaa", "aaaab", d, q, True,
        "SCENARIO 2: worst case for NAIVE (almost-matching at every shift)",
    )
    run_one(
        "2359023141526739921", "31415", 10, 13, True,
        "SCENARIO 3: digit text, d=10, q=13 -> Rabin-Karp spurious hit",
    )
    run_one(
        "aaaaaaaaaaaaaaaaaaaa", "aaaa", d, q, False,
        "SCENARIO 4: worst case for BOTH (every shift is a real match)",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Naive vs Rabin-Karp string matching")
    p.add_argument("--text", help="the text T to search in")
    p.add_argument("--file", help="read the text T from this file instead of --text")
    p.add_argument("--pattern", help="the pattern P to search for")
    p.add_argument("--d", type=int, default=DEFAULT_RADIX, help=f"radix (default {DEFAULT_RADIX})")
    p.add_argument("--q", type=int, default=DEFAULT_MODULUS, help=f"prime modulus (default {DEFAULT_MODULUS})")
    p.add_argument("--trace", action="store_true", help="print a step-by-step trace of both algorithms")
    p.add_argument("--demo", action="store_true", help="run four prepared demonstration scenarios")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.demo:
            demo(args.d, args.q)
            return 0

        if args.pattern is None or (args.text is None and args.file is None):
            print("error: give --pattern and either --text or --file (or use --demo)", file=sys.stderr)
            return 2

        if args.file:
            with open(args.file, "r", encoding="utf-8") as fh:
                text = fh.read().rstrip("\n")
        else:
            text = args.text

        run_one(text, args.pattern, args.d, args.q, args.trace)
        return 0

    except (ValueError, TypeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
