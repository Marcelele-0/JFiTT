from typing import List, Set

class FiniteAutomate:
    def __init__(self, pattern: str, alphabet: Set[str]):
        self.pattern = pattern
        # keep a deterministic alphabet ordering
        self.alphabet = sorted(list(alphabet))
        self.m = len(pattern)
        self.transition_table: List[List[int]] = []

    def build_automate(self) -> None:
        m = self.m
        sigma = len(self.alphabet)
        # initialize table with zeros
        self.transition_table = [[0 for _ in range(sigma)] for _ in range(m + 1)]

        for q in range(m + 1):
            for a_idx, ch in enumerate(self.alphabet):
                k = min(m, q + 1)
                prefix = self.pattern[:q] + ch
                # find largest k such that pattern[:k] == suffix of prefix of length k
                while k > 0 and self.pattern[:k] != prefix[len(prefix) - k:]:
                    k -= 1
                self.transition_table[q][a_idx] = k

    def run_search(self, text: str) -> List[int]:
        if not self.transition_table:
            raise RuntimeError("Automate not built. Call build_automate() first.")
        result: List[int] = []
        state = 0
        for i, ch in enumerate(text):
            try:
                a = self.alphabet.index(ch)
            except ValueError:
                # unknown character -> reset state
                state = 0
                continue
            state = self.transition_table[state][a]
            if state == self.m:
                result.append(i + 1 - self.m)
        return result
