#pragma once
#include <string>

class InputParser {
public:
    InputParser(int argc, char* argv[]);
    bool validate() const;
    std::string getAlgorithm() const;
    std::string getPattern() const;
    std::string getFilename() const;
    std::string getFileContent() const;
private:
    std::string algorithm_;
    std::string pattern_;
    std::string filename_;
    bool valid_;
};