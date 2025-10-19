from typing import List

class KMPMatcher:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.prefix_function: List[int] = []

    def compute_prefix_function(self) -> None:
        m = len(self.pattern)
        self.prefix_function = [0] * m
        k = 0
        for q in range(1, m):
            while k > 0 and self.pattern[k] != self.pattern[q]:
                k = self.prefix_function[k - 1]
            if self.pattern[k] == self.pattern[q]:
                k += 1
            self.prefix_function[q] = k

    def run_search(self, text: str) -> List[int]:
        if not self.prefix_function:
            self.compute_prefix_function()
        n = len(text)
        m = len(self.pattern)
        result: List[int] = []
        q = 0
        for i in range(n):
            while q > 0 and (q >= m or self.pattern[q] != text[i]):
                q = self.prefix_function[q - 1]
            if q < m and self.pattern[q] == text[i]:
                q += 1
            if q == m:
                result.append(i + 1 - m)
                q = self.prefix_function[q - 1]
        return result

    def reset(self) -> None:
        self.prefix_function = []
