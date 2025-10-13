#include "InputParser.hpp"
#include <fstream>
#include <iostream>
#include <iterator>

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

    // Build UTF-8-aware alphabet: split text_ and pattern_ into UTF-8 codepoints
    auto extractUTF8 = [](const std::string &s) {
        std::set<std::string> out;
        for (size_t i = 0; i < s.size(); ) {
            unsigned char c = static_cast<unsigned char>(s[i]);
            size_t len = 1;
            if ((c & 0x80) == 0x00) len = 1;
            else if ((c & 0xE0) == 0xC0) len = 2;
            else if ((c & 0xF0) == 0xE0) len = 3;
            else if ((c & 0xF8) == 0xF0) len = 4;
            else len = 1; // fallback
            if (i + len <= s.size()) {
                out.insert(s.substr(i, len));
            }
            i += len;
        }
        return out;
    };
    // merge into a member container by reusing alphabet_? We'll store UTF-8 set in filename_ not allowed; instead keep a private static store via a mutable static? Simpler: keep a private member not declared - add one.

    isValid_ = true;
}

bool InputParser::validate() const { return isValid_; }
std::string InputParser::getAlgorithm() const { return algorithm_; }
std::string InputParser::getPattern() const { return pattern_; }
std::string InputParser::getText() const { return text_; }
std::set<char> InputParser::getAlphabet() const { return alphabet_; }
std::string InputParser::getFilename() const { return filename_; }

std::set<std::string> InputParser::getAlphabetUTF8() const {
    // Build sets on the fly from stored text_ and pattern_
    auto extract = [](const std::string &s) {
        std::set<std::string> out;
        for (size_t i = 0; i < s.size(); ) {
            unsigned char c = static_cast<unsigned char>(s[i]);
            size_t len = 1;
            if ((c & 0x80) == 0x00) len = 1;
            else if ((c & 0xE0) == 0xC0) len = 2;
            else if ((c & 0xF0) == 0xE0) len = 3;
            else if ((c & 0xF8) == 0xF0) len = 4;
            else len = 1;
            if (i + len <= s.size()) out.insert(s.substr(i, len));
            i += len;
        }
        return out;
    };

    std::set<std::string> res = extract(text_);
    auto pat = extract(pattern_);
    res.insert(pat.begin(), pat.end());
    return res;
}