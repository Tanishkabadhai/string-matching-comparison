"""
test_matchers.py
================
Unit tests for both algorithms. Run with:

    python -m unittest -v test_matchers

Test groups
-----------
  A. Normal operation (known answers)
  B. Edge cases and boundary conditions
  C. Invalid input
  D. Correctness: both algorithms are compared
     against an independent brute-force reference on many random inputs
  E. Complexity facts: counters match the analytical formulas
  F. Rabin-Karp specifics: spurious hits do not cause wrong answers
  G. Trace module agrees with the real implementations
"""

import random
import unittest

from matchers import naive_search, rabin_karp_search
from trace import trace_naive, trace_rabin_karp


def reference_matches(text: str, pattern: str):
    """Independent oracle: slicing comparison, no shared code with the algorithms."""
    n, m = len(text), len(pattern)
    return [s for s in range(n - m + 1) if text[s:s + m] == pattern]


BOTH = [("naive", naive_search), ("rabin-karp", rabin_karp_search)]


class A_NormalOperation(unittest.TestCase):
    def test_known_answers(self):
        cases = [
            ("abracadabra", "abra", [0, 7]),
            ("hello world", "world", [6]),
            ("abcabcabc", "abc", [0, 3, 6]),
            ("mississippi", "issi", [1, 4]),       # overlapping occurrences
            ("2359023141526739921", "31415", [6]),  # textbook example
        ]
        for name, fn in BOTH:
            for text, pat, expected in cases:
                with self.subTest(algo=name, text=text, pattern=pat):
                    self.assertEqual(fn(text, pat).matches, expected)

    def test_no_match(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("abcdefg", "xyz").matches, [])

    def test_overlapping_matches_all_reported(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("aaaaa", "aa").matches, [0, 1, 2, 3])


class B_EdgeCases(unittest.TestCase):
    def test_pattern_longer_than_text(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("ab", "abc").matches, [])

    def test_pattern_equals_text(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("abc", "abc").matches, [0])

    def test_empty_text(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("", "a").matches, [])

    def test_single_character(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("a", "a").matches, [0])
                self.assertEqual(fn("banana", "a").matches, [1, 3, 5])

    def test_match_at_start_and_end(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("xyzabc", "xyz").matches, [0])
                self.assertEqual(fn("abcxyz", "xyz").matches, [3])

    def test_case_sensitive(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("Hello hello", "hello").matches, [6])

    def test_special_and_unicode_characters(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                self.assertEqual(fn("a b  c\tb", "  ").matches, [3])
                self.assertEqual(fn("naïve café café", "café").matches, [6, 11])


class C_InvalidInput(unittest.TestCase):
    def test_empty_pattern_rejected(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                with self.assertRaises(ValueError):
                    fn("abc", "")

    def test_non_string_rejected(self):
        for name, fn in BOTH:
            with self.subTest(algo=name):
                with self.assertRaises(TypeError):
                    fn(123, "a")
                with self.assertRaises(TypeError):
                    fn("abc", None)

    def test_bad_rabin_karp_parameters(self):
        with self.assertRaises(ValueError):
            rabin_karp_search("abc", "a", q=1)
        with self.assertRaises(ValueError):
            rabin_karp_search("abc", "a", d=1)
        with self.assertRaises(ValueError):
            rabin_karp_search("abc", "a", q="101")


class D_CorrectnessAgainstOracle(unittest.TestCase):
    def test_random_inputs_small_alphabet(self):
        """Small alphabet -> many matches and many hash collisions: a harsh test."""
        rng = random.Random(2026)
        for _ in range(1500):
            n = rng.randint(0, 40)
            m = rng.randint(1, 8)
            text = "".join(rng.choice("ab") for _ in range(n))
            pat = "".join(rng.choice("ab") for _ in range(m))
            expected = reference_matches(text, pat)
            self.assertEqual(naive_search(text, pat).matches, expected, (text, pat))
            self.assertEqual(rabin_karp_search(text, pat).matches, expected, (text, pat))

    def test_random_inputs_larger_alphabet(self):
        rng = random.Random(7)
        alphabet = "abcdefghijklmnopqrstuvwxyz "
        for _ in range(500):
            n = rng.randint(0, 200)
            m = rng.randint(1, 10)
            text = "".join(rng.choice(alphabet) for _ in range(n))
            # half the time take the pattern from the text so matches really exist
            if n >= m and rng.random() < 0.5:
                start = rng.randint(0, n - m)
                pat = text[start:start + m]
            else:
                pat = "".join(rng.choice(alphabet) for _ in range(m))
            expected = reference_matches(text, pat)
            self.assertEqual(naive_search(text, pat).matches, expected)
            self.assertEqual(rabin_karp_search(text, pat).matches, expected)

    def test_both_algorithms_agree_with_each_other(self):
        rng = random.Random(99)
        for _ in range(300):
            text = "".join(rng.choice("abc") for _ in range(rng.randint(0, 60)))
            pat = "".join(rng.choice("abc") for _ in range(rng.randint(1, 6)))
            self.assertEqual(naive_search(text, pat).matches,
                             rabin_karp_search(text, pat).matches)


class E_ComplexityCounters(unittest.TestCase):
    """The counters must equal the formulas derived in the analysis."""

    def test_naive_best_case(self):
        # first pattern char never appears in text: exactly one comparison per shift
        n, m = 100, 10
        r = naive_search("a" * n, "b" + "a" * (m - 1))
        self.assertEqual(r.char_comparisons, n - m + 1)

    def test_naive_worst_case(self):
        # all but the last char match at every shift: m comparisons per shift
        n, m = 100, 10
        r = naive_search("a" * n, "a" * (m - 1) + "b")
        self.assertEqual(r.char_comparisons, (n - m + 1) * m)

    def test_naive_worst_case_all_match(self):
        n, m = 50, 5
        r = naive_search("a" * n, "a" * m)
        self.assertEqual(r.char_comparisons, (n - m + 1) * m)
        self.assertEqual(len(r.matches), n - m + 1)

    def test_rabin_karp_structure_counts(self):
        n, m = 100, 10
        r = rabin_karp_search("abcde" * 20, "xyzxyzxyzx")
        self.assertEqual(r.hash_comparisons, n - m + 1)  # one per shift
        self.assertEqual(r.hash_updates, n - m)          # one per transition
        self.assertEqual(r.preprocessing_ops, 2 * m)     # Theta(m)

    def test_rabin_karp_worst_case_all_match(self):
        n, m = 50, 5
        r = rabin_karp_search("a" * n, "a" * m)
        self.assertEqual(r.char_comparisons, (n - m + 1) * m)  # still O((n-m+1)m)

    def test_rabin_karp_avoids_comparisons_where_naive_does_not(self):
        n, m = 100, 10
        text, pat = "a" * n, "a" * (m - 1) + "b"
        self.assertEqual(rabin_karp_search(text, pat, q=1009).char_comparisons, 0)
        self.assertGreater(naive_search(text, pat).char_comparisons, 0)


class F_RabinKarpSpuriousHits(unittest.TestCase):
    def test_textbook_spurious_hit(self):
        # CLRS-style example: d=10, q=13 -> window "67399" hashes like "31415"
        r = rabin_karp_search("2359023141526739921", "31415", d=10, q=13)
        self.assertEqual(r.matches, [6])
        self.assertEqual(r.spurious_hits, 1)

    def test_tiny_modulus_still_correct(self):
        rng = random.Random(5)
        for q in (2, 3, 5, 7):
            for _ in range(200):
                text = "".join(rng.choice("abc") for _ in range(rng.randint(5, 50)))
                pat = "".join(rng.choice("abc") for _ in range(rng.randint(1, 5)))
                r = rabin_karp_search(text, pat, q=q)
                self.assertEqual(r.matches, reference_matches(text, pat))

    def test_larger_modulus_fewer_spurious_hits(self):
        rng = random.Random(11)
        text = "".join(rng.choice("abcdefghij") for _ in range(5000))
        pat = "".join(rng.choice("abcdefghij") for _ in range(6))
        small = rabin_karp_search(text, pat, q=7).spurious_hits
        large = rabin_karp_search(text, pat, q=10007).spurious_hits
        self.assertGreater(small, large)

    def test_spurious_plus_true_equals_hash_hits(self):
        text, pat = "2359023141526739921", "31415"
        r = rabin_karp_search(text, pat, d=10, q=13)
        self.assertEqual(r.spurious_hits + len(r.matches), 2)


class G_TraceAgreesWithImplementation(unittest.TestCase):
    def test_trace_matches_real_runs(self):
        rng = random.Random(3)
        for _ in range(200):
            text = "".join(rng.choice("abc") for _ in range(rng.randint(0, 40)))
            pat = "".join(rng.choice("abc") for _ in range(rng.randint(1, 5)))
            n_lines, n_matches, n_cmp = trace_naive(text, pat)
            r_lines, r_matches, r_cmp = trace_rabin_karp(text, pat, q=11)
            real_n = naive_search(text, pat)
            real_r = rabin_karp_search(text, pat, q=11)
            self.assertEqual(n_matches, real_n.matches)
            self.assertEqual(n_cmp, real_n.char_comparisons)
            self.assertEqual(r_matches, real_r.matches)
            self.assertEqual(r_cmp, real_r.char_comparisons)


if __name__ == "__main__":
    unittest.main(verbosity=2)
