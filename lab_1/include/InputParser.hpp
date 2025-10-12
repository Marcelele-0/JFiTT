#pragma once
#include <string>
#include <set>

class InputParser {
public:
    InputParser(int argc, char* argv[]);
    bool validate() const;
    std::string getAlgorithm() const;
    std::string getPattern() const;
    std::string getText() const;
    std::set<char> getAlphabet() const;
    std::string getFilename() const;

private:
    bool isValid_;
    std::string algorithm_;
    std::string pattern_;
    std::string text_;
    std::set<char> alphabet_;
    std::string filename_;
};