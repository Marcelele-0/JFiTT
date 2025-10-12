#include "InputParser.hpp"
#include <fstream>
#include <sstream>

InputParser::InputParser(int argc, char* argv[]) : valid_(false) {
    if (argc == 4) {
        algorithm_ = argv[1];
        pattern_ = argv[2];
        filename_ = argv[3];
        valid_ = (algorithm_ == "FA" || algorithm_ == "KMP");
    }
}

bool InputParser::validate() const {
    return valid_;
}

std::string InputParser::getAlgorithm() const {
    return algorithm_;
}

std::string InputParser::getPattern() const {
    return pattern_;
}

std::string InputParser::getFilename() const {
    return filename_;
}

std::string InputParser::getFileContent() const {
    std::ifstream file(filename_);
    std::ostringstream ss;
    ss << file.rdbuf();
    return ss.str();
}