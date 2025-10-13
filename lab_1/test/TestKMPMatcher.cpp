#include <cassert>
#include <iostream>
#include <vector>
#include "../include/KMPMatcher.hpp"

void test_basic_match() {
    std::string pattern = "aba";
    std::string text = "abacababababa";
    KMPMatcher matcher(pattern);
    std::vector<int> result = matcher.runSearch(text);
    std::vector<int> expected{0, 4, 6, 8, 10};
    assert(result == expected);
    std::cout << "test_basic_match passed\n";
}

void test_no_match() {
    std::string pattern = "abcd";
    std::string text = "abcabcab";
    KMPMatcher matcher(pattern);
    std::vector<int> result = matcher.runSearch(text);
    assert(result.empty());
    std::cout << "test_no_match passed\n";
}

void test_overlap_match() {
    std::string pattern = "aa";
    std::string text = "aaa";
    KMPMatcher matcher(pattern);
    std::vector<int> result = matcher.runSearch(text);
    std::vector<int> expected{0,1};
    assert(result == expected);
    std::cout << "test_overlap_match passed\n";
}

int main() {
    test_basic_match();
    test_no_match();
    test_overlap_match();
    std::cout << "All KMP tests passed!\n";
    return 0;
}
