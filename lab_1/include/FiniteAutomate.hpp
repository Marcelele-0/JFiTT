#pragma once
#include <string>
#include <vector>
#include <set>
#include <algorithm>

class FiniteAutomate {
public:
    FiniteAutomate(const std::string& pattern, const std::set<char>& alphabet);
    void buildAutomate();
    int transition(int state, char ch) const;
    std::vector<int> runSearch(const std::string& text) const;
private:
    std::string pattern_;
    std::set<char> alphabet_;
    int startingState_;
    std::set<int> acceptingStates_;
    std::vector<std::vector<int>> transitionTable_;
};