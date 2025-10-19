#pragma once
#include <string>
#include <set>

#include <vector>

class InputParser {
public:
    InputParser(int argc, char* argv[]);
    bool validate() const;
    std::string getAlgorithm() const;
    std::string getPattern() const;
    std::string getText() const;
    std::set<char> getAlphabet() const;
    // Return a set of UTF-8 codepoint strings found in pattern and text
    std::set<std::string> getAlphabetUTF8() const;
    std::string getFilename() const;

private:
    bool isValid_;
    std::string algorithm_;
    std::string pattern_;
    std::string text_;
    std::set<char> alphabet_;
    std::string filename_;
};