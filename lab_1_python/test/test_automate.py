import unittest
from finite_automate import FiniteAutomate
from kmp_matcher import KMPMatcher

class TestFiniteAutomate(unittest.TestCase):
    def test_basic_match(self):
        pattern = "abc"
        text = "xxabcxxabcabcx"
        alphabet = set(['a','b','c','x'])

        fa = FiniteAutomate(pattern, alphabet)
        fa.build_automate()
        result = fa.run_search(text)
        expected = [2, 7, 10]
        self.assertEqual(result, expected)

    def test_no_match(self):
        pattern = "abc"
        text = "xxxabxabxx"
        alphabet = set(['a','b','c','x'])

        fa = FiniteAutomate(pattern, alphabet)
        fa.build_automate()
        result = fa.run_search(text)
        self.assertEqual(result, [])

    def test_overlap_match(self):
        pattern = "aa"
        text = "aaa"
        alphabet = set(['a'])

        fa = FiniteAutomate(pattern, alphabet)
        fa.build_automate()
        result = fa.run_search(text)
        expected = [0, 1]
        self.assertEqual(result, expected)

class TestKMPMatcher(unittest.TestCase):
    def test_basic_match(self):
        pattern = "abc"
        text = "xxabcxxabcabcx"
        matcher = KMPMatcher(pattern)
        result = matcher.run_search(text)
        expected = [2, 7, 10]
        self.assertEqual(result, expected)

    def test_no_match(self):
        pattern = "abc"
        text = "xxxabxabxx"
        matcher = KMPMatcher(pattern)
        result = matcher.run_search(text)
        self.assertEqual(result, [])

    def test_overlap_match(self):
        pattern = "aa"
        text = "aaa"
        matcher = KMPMatcher(pattern)
        result = matcher.run_search(text)
        expected = [0, 1]
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
