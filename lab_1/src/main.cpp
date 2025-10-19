#include <iostream>
#include "InputParser.hpp"
#include "FiniteAutomate.hpp"
#include "KMPMatcher.hpp"

// Helper: convert a byte index in a UTF-8 string to codepoint index
static int byteIndexToCodepointIndex(const std::string &s, int byteIndex) {
    int cp = 0;
    for (int i = 0; i < byteIndex && i < (int)s.size(); ) {
        unsigned char c = static_cast<unsigned char>(s[i]);
        int len = 1;
        if ((c & 0x80) == 0x00) len = 1;
        else if ((c & 0xE0) == 0xC0) len = 2;
        else if ((c & 0xF0) == 0xE0) len = 3;
        else if ((c & 0xF8) == 0xF0) len = 4;
        else len = 1;
        i += len;
        ++cp;
    }
    return cp;
}

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
            int charPos = byteIndexToCodepointIndex(text, pos);
            std::cout << "Pattern found at byte position: " << pos
                      << " (char index: " << charPos << ")\n";
        }
    }
    else if (algorithm == "KMP") {
        KMPMatcher matcher(pattern);
        auto occurrences = matcher.runSearch(text);
        for (int pos : occurrences) {
            int charPos = byteIndexToCodepointIndex(text, pos);
            std::cout << "Pattern found at byte position: " << pos
                      << " (char index: " << charPos << ")\n";
        }
    }
    else {
        std::cerr << "Unknown algorithm: " << algorithm << std::endl;
        return 1;
    }

    return 0;
}