#include <cassert>
#include <set>
#include <string>
#include <vector>
#include <iostream>
#include "../include/FiniteAutomate.hpp"

void test_basic_match() {
    std::string pattern = "abc";
    std::string text = "xxabcxxabcabcx";
    std::set<char> alphabet{'a', 'b', 'c', 'x'};

    FiniteAutomate automate(pattern, alphabet);
    automate.buildAutomate();
    std::vector<int> result = automate.runSearch(text);

    std::vector<int> expected{2, 7, 10};
    assert(result == expected);
    std::cout << "test_basic_match passed\n";
}

void test_no_match() {
    std::string pattern = "abc";
    std::string text = "xxxabxabxx";
    std::set<char> alphabet{'a', 'b', 'c', 'x'};

    FiniteAutomate automate(pattern, alphabet);
    automate.buildAutomate();
    std::vector<int> result = automate.runSearch(text);

    assert(result.empty());
    std::cout << "test_no_match passed\n";
}

void test_overlap_match() {
    std::string pattern = "aa";
    std::string text = "aaa";
    std::set<char> alphabet{'a'};

    FiniteAutomate automate(pattern, alphabet);
    automate.buildAutomate();
    std::vector<int> result = automate.runSearch(text);

    std::vector<int> expected{0, 1};
    assert(result == expected);
    std::cout << "test_overlap_match passed\n";
}

int main() {
    test_basic_match();
    test_no_match();
    test_overlap_match();
    std::cout << "All FiniteAutomate tests passed!\n";
    return 0;
}