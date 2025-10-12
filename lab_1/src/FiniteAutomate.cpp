#include "FiniteAutomate.hpp"

FiniteAutomate::FiniteAutomate(const std::string& pattern, const std::set<char>& alphabet)
    : pattern_(pattern), alphabet_(alphabet), startingState_(0) {}

void FiniteAutomate::buildAutomate() {
    // TODO: Zaimplementuj budowę automatu
}

int FiniteAutomate::transition(int state, char ch) const {
    // TODO: Zaimplementuj funkcję przejścia
    return 0;
}

std::vector<int> FiniteAutomate::runSearch(const std::string& text) const {
    // TODO: Zaimplementuj wyszukiwanie wzorca
    return {};
}

void FiniteAutomate::reset() {
    // TODO: Resetuj stan automatu jeśli to konieczne
}