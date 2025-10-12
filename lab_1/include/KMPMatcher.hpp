#pragma once
#include <string>
#include <vector>
#include <set>

class KMPMatcher {
public:
    KMPMatcher(const std::string& pattern);
    void computePrefixFunction();
    std::vector<int> runSearch(const std::string& text) const;
    void reset();
private:
    std::vector<int> automateStates_;
    int startingState_;
    std::set<int> acceptingStates_;
    std::set<char> alphabet_;
    std::vector<int> prefixFunction_;
    std::string pattern_;
};