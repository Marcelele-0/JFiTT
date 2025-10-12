#pragma once
#include <string>
#include <vector>
#include <set>
#include <map>

class FiniteAutomate {
public:
    FiniteAutomate(const std::string& pattern, const std::set<char>& alphabet);
    void buildAutomate();
    int transition(int state, char ch) const;
    std::vector<int> runSearch(const std::string& text) const;
    void reset();
private:
    std::vector<int> automateStates_;
    int startingState_;
    std::set<int> acceptingStates_;
    std::set<char> alphabet_;
    std::map<std::pair<int, char>, int> stateFunction_;
    std::string pattern_;
};