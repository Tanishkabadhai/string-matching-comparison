"""
matchers.py
===========
My implementations of the two string matching algorithms this project compares:

    1. The Naive string matching algorithm
    2. The Rabin-Karp algorithm

Both functions return a MatchResult that contains the match positions AND
counters for the dominant operations (the ones that decide the running time).
The counters are what let us compare the two algorithms on the same input
instead of just claiming one is faster.

Terminology (same as the standard textbook treatment):
    T  = text,     n = len(T)
    P  = pattern,  m = len(P)
    s  = shift (the position in T where the pattern is aligned)
    A valid shift is one where T[s : s+m] == P.
    All shifts are 0-indexed.
"""

from dataclasses import dataclass, field
from typing import List

# Default parameters for Rabin-Karp.
#   d : radix, i.e. size of the alphabet. 256 covers all extended-ASCII characters.
#   q : the prime modulus. A small prime keeps numbers small; a larger prime
#       gives fewer false hits ("spurious hits").
DEFAULT_RADIX = 256
DEFAULT_MODULUS = 101


@dataclass
class MatchResult:
    """Everything one algorithm run produces."""

    algorithm: str
    n: int
    m: int
    matches: List[int] = field(default_factory=list)  # valid shifts found

    # --- dominant-operation counters -------------------------------------
    char_comparisons: int = 0   # individual T[i] == P[j] comparisons
    hash_comparisons: int = 0   # (Rabin-Karp) window hash vs pattern hash
    hash_updates: int = 0       # (Rabin-Karp) rolling-hash updates, window s -> s+1
    preprocessing_ops: int = 0  # (Rabin-Karp) work to hash P and the first window
    spurious_hits: int = 0      # (Rabin-Karp) hash equal but strings different

    @property
    def total_ops(self) -> int:
        """Simple overall cost figure = all counted primitive operations."""
        return (
            self.char_comparisons
            + self.hash_comparisons
            + self.hash_updates
            + self.preprocessing_ops
        )


# --------------------------------------------------------------------------
# Input validation (shared by both algorithms)
# --------------------------------------------------------------------------
def _validate(text: str, pattern: str) -> None:
    if not isinstance(text, str) or not isinstance(pattern, str):
        raise TypeError("text and pattern must both be strings")
    if len(pattern) == 0:
        raise ValueError("pattern must not be empty")


# --------------------------------------------------------------------------
# 1. NAIVE STRING MATCHING
# --------------------------------------------------------------------------
def naive_search(text: str, pattern: str) -> MatchResult:
    """
    Naive algorithm: slide the pattern over the text one position at a time
    and, at every shift s, compare the pattern with the text character by
    character. Stop comparing at the first mismatch.

    Pseudocode:
        NAIVE-MATCHER(T, P)
            n = T.length ; m = P.length
            for s = 0 to n - m
                j = 0
                while j < m and T[s + j] == P[j]
                    j = j + 1
                if j == m
                    print "Pattern occurs with shift" s

    Time: best case  O(n - m + 1)    -> first character mismatches at every shift
          worst case O((n - m + 1)m) -> almost the whole pattern matches at every shift
    """
    _validate(text, pattern)
    n, m = len(text), len(pattern)
    result = MatchResult("Naive", n, m)

    for s in range(n - m + 1):          # every possible shift
        j = 0
        while j < m:
            result.char_comparisons += 1  # dominant operation
            if text[s + j] != pattern[j]:
                break                     # mismatch: abandon this shift
            j += 1
        if j == m:                        # all m characters matched
            result.matches.append(s)

    return result


# --------------------------------------------------------------------------
# 2. RABIN-KARP
# --------------------------------------------------------------------------
def rabin_karp_search(
    text: str,
    pattern: str,
    d: int = DEFAULT_RADIX,
    q: int = DEFAULT_MODULUS,
) -> MatchResult:
    """
    Rabin-Karp algorithm: treat each length-m window of the text as a number
    in radix d, reduce it modulo q (its "hash"), and compare that single number
    with the hash of the pattern. Only if the hashes are equal do we compare
    characters (to rule out a spurious hit).

    The hash of the next window is obtained from the previous window's hash in
    O(1) ("rolling hash"):

        t(s+1) = ( d * ( t(s) - T[s] * h ) + T[s+m] ) mod q,   where h = d^(m-1) mod q

    Pseudocode:
        RABIN-KARP-MATCHER(T, P, d, q)
            n = T.length ; m = P.length
            h = d^(m-1) mod q
            p = 0 ; t0 = 0
            for i = 0 to m - 1                       // preprocessing
                p  = (d*p  + P[i]) mod q
                t0 = (d*t0 + T[i]) mod q
            for s = 0 to n - m                       // matching
                if p == t_s
                    if P[0..m-1] == T[s..s+m-1]      // rule out spurious hit
                        print "Pattern occurs with shift" s
                if s < n - m
                    t_(s+1) = (d*(t_s - T[s]*h) + T[s+m]) mod q

    Time: preprocessing Theta(m); matching O((n - m + 1)m) in the worst case,
          but expected O(n + m) when the number of valid shifts is small and q
          is a suitably large prime.
    """
    _validate(text, pattern)
    if not isinstance(d, int) or d < 2:
        raise ValueError("radix d must be an integer >= 2")
    if not isinstance(q, int) or q < 2:
        raise ValueError("modulus q must be an integer >= 2")

    n, m = len(text), len(pattern)
    result = MatchResult("Rabin-Karp", n, m)

    if m > n:                  # pattern longer than text: no valid shift exists
        return result

    h = pow(d, m - 1, q)       # d^(m-1) mod q, the weight of the leading character

    # ---- preprocessing: hash of the pattern and of the first window --------
    p_hash = 0
    t_hash = 0
    for i in range(m):
        p_hash = (d * p_hash + ord(pattern[i])) % q
        t_hash = (d * t_hash + ord(text[i])) % q
        result.preprocessing_ops += 2   # one hash step for P, one for T[0..m-1]

    # ---- matching -----------------------------------------------------------
    for s in range(n - m + 1):
        result.hash_comparisons += 1
        if p_hash == t_hash:
            # Hashes agree: could be a real match or a spurious hit.
            # Verify character by character (same early-exit rule as naive).
            j = 0
            while j < m:
                result.char_comparisons += 1
                if text[s + j] != pattern[j]:
                    break
                j += 1
            if j == m:
                result.matches.append(s)
            else:
                result.spurious_hits += 1

        if s < n - m:
            # Rolling update: drop T[s], append T[s+m]. Python's % is always
            # non-negative for a positive modulus, so no extra "+ q" fix is needed.
            t_hash = (d * (t_hash - ord(text[s]) * h) + ord(text[s + m])) % q
            result.hash_updates += 1

    return result
