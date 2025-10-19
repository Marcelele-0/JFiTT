#include "KMPMatcher.hpp"

KMPMatcher::KMPMatcher(const std::string& pattern)
    : pattern_(pattern), startingState_(0) {
    // Precompute prefix function for the given pattern so runSearch can be const
    computePrefixFunction();
}

void KMPMatcher::computePrefixFunction() {
    prefixFunction_.clear();
    const int n = static_cast<int>(pattern_.size());
    prefixFunction_.resize(n);
    if (n == 0) return;

    prefixFunction_[0] = 0;
    for (int i = 1; i < n; ++i) {
        int j = prefixFunction_[i - 1];
        while (j > 0 && pattern_[i] != pattern_[j]) {
            j = prefixFunction_[j - 1];
        }
        if (pattern_[i] == pattern_[j]) ++j;
        prefixFunction_[i] = j;
    }
}

std::vector<int> KMPMatcher::runSearch(const std::string& text) const {
    std::vector<int> matches;
    const int m = static_cast<int>(pattern_.size());
    const int n = static_cast<int>(text.size());
    if (m == 0 || n == 0 || n < m) return matches;

    // prefixFunction_ should have been computed in constructor; guard just in case
    if (static_cast<int>(prefixFunction_.size()) != m) return matches;

    int j = 0; // number of chars matched
    for (int i = 0; i < n; ++i) {
        while (j > 0 && text[i] != pattern_[j]) {
            j = prefixFunction_[j - 1];
        }
        if (text[i] == pattern_[j]) ++j;
        if (j == m) {
            matches.push_back(i - m + 1);
            j = prefixFunction_[j - 1];
        }
    }
    return matches;
}

void KMPMatcher::reset() {
    // Clear computed structures; keep pattern_ intact
    automateStates_.clear();
    acceptingStates_.clear();
    alphabet_.clear();
    prefixFunction_.clear();
    startingState_ = 0;
}