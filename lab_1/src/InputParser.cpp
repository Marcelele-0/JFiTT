#include "InputParser.hpp"
#include <fstream>
#include <iostream>

InputParser::InputParser(int argc, char* argv[]) : isValid_(false) {
    if (argc != 4) {
        std::cerr << "Usage: <FA|KMP> <pattern> <filename>\n";
        return;
    }
    algorithm_ = argv[1];
    pattern_ = argv[2];
    filename_ = argv[3];

    // Wczytaj plik do tekstu
    std::ifstream file(filename_);
    if (!file) {
        std::cerr << "Cannot open file: " << filename_ << "\n";
        return;
    }
    text_ = std::string((std::istreambuf_iterator<char>(file)), std::istreambuf_iterator<char>());

    // Zbuduj alfabet na podstawie tekstu i wzorca
    for (char c : text_) alphabet_.insert(c);
    for (char c : pattern_) alphabet_.insert(c);

    isValid_ = true;
}

bool InputParser::validate() const { return isValid_; }
std::string InputParser::getAlgorithm() const { return algorithm_; }
std::string InputParser::getPattern() const { return pattern_; }
std::string InputParser::getText() const { return text_; }
std::set<char> InputParser::getAlphabet() const { return alphabet_; }
std::string InputParser::getFilename() const { return filename_; }