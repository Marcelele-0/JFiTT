#include "KMPMatcher.hpp"

KMPMatcher::KMPMatcher(const std::string& pattern)
    : pattern_(pattern), startingState_(0) {}

void KMPMatcher::computePrefixFunction() {
    // TODO: Implementacja funkcji prefiksowej
}

std::vector<int> KMPMatcher::runSearch(const std::string& text) const {
    // TODO: Implementacja wyszukiwania wzorca KMP
    return {};
}

void KMPMatcher::reset() {
    // TODO: Reset stanu algorytmu jeśli potrzebny
}