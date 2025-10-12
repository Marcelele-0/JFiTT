#include <iostream>
#include "InputParser.hpp"
#include "FiniteAutomate.hpp"
// #include "KMPMatcher.hpp" // jeśli chcesz dodać obsługę KMP w przyszłości

int main(int argc, char* argv[]) {
    InputParser parser(argc, argv);
    if (!parser.validate()) {
        return 1;
    }

    std::string algorithm = parser.getAlgorithm();
    std::string pattern = parser.getPattern();
    std::string text = parser.getText();
    std::set<char> alphabet = parser.getAlphabet();

    if (algorithm == "FA") {
        FiniteAutomate automate(pattern, alphabet);
        automate.buildAutomate();
        auto occurrences = automate.runSearch(text);

        for (int pos : occurrences) {
            std::cout << "Pattern found at position: " << pos << "\n";
        }
    }
    // else if (algorithm == "KMP") {
    //     KMPMatcher matcher(pattern);
    //     auto occurrences = matcher.runSearch(text);
    //     for (int pos : occurrences) {
    //         std::cout << "Pattern found at position: " << pos << "\n";
    //     }
    // }
    else {
        std::cerr << "Unknown algorithm: " << algorithm << std::endl;
        return 1;
    }

    return 0;
}