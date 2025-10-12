#include "FiniteAutomate.hpp"

FiniteAutomate::FiniteAutomate(const std::string& pattern, const std::set<char>& alphabet):
    pattern_(pattern),
    alphabet_(alphabet),
    startingState_(0)
{}

void FiniteAutomate::buildAutomate() {
    // Zakładamy, że alfabet jest zdefiniowany przez użytkownika
    int m = pattern_.size();
    int sigma = alphabet_.size();

    // Tworzymy tablicę przejść: (m+1) stanów x |alphabet_| znaków
    transitionTable_.assign(m + 1, std::vector<int>(sigma, 0));

    // Mapowanie znaków alfabetu na indeksy (dla wygody)
    std::vector<char> alphabetVec(alphabet_.begin(), alphabet_.end());

    for (int q = 0; q <= m; ++q) {
        for (int a = 0; a < sigma; ++a) {
            char ch = alphabetVec[a];
            int k = std::min(m, q + 1);
            std::string prefix = pattern_.substr(0, q) + ch;
            while (k > 0 && pattern_.substr(0, k) != prefix.substr(prefix.size() - k, k)) {
                --k;
            }
            transitionTable_[q][a] = k;
        }
    }

    // Stan akceptujący to stan m
    acceptingStates_.clear();
    acceptingStates_.insert(m);
}

int FiniteAutomate::transition(int state, char ch) const {
    // Zwraca następny stan dla danego stanu i znaku (lub 0 jeśli znak nie z alfabetu)
    auto it = std::find(alphabet_.begin(), alphabet_.end(), ch);
    if (it == alphabet_.end()) return 0;
    int a = std::distance(alphabet_.begin(), it);
    return transitionTable_[state][a];
}

std::vector<int> FiniteAutomate::runSearch(const std::string& text) const {
    // Szuka wszystkich wystąpień wzorca w tekście
    std::vector<int> result;
    int state = startingState_;
    std::vector<char> alphabetVec(alphabet_.begin(), alphabet_.end());

    for (size_t i = 0; i < text.size(); ++i) {
        auto it = std::find(alphabetVec.begin(), alphabetVec.end(), text[i]);
        int a = (it != alphabetVec.end()) ? std::distance(alphabetVec.begin(), it) : -1;
        if (a == -1) {
            state = 0; // reset dla nieznanego znaku
            continue;
        }
        state = transitionTable_[state][a];
        if (acceptingStates_.count(state)) {
            result.push_back(i + 1 - pattern_.size());
        }
    }
    return result;
}