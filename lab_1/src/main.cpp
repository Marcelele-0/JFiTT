#include <iostream>
#include <string>
#include "InputParser.hpp"

int main(int argc, char* argv[]) {
    InputParser parser(argc, argv);
    if (!parser.validate()) {
        std::cerr << "Usage: " << argv[0] << " <FA|KMP> <pattern> <filename>" << std::endl;
        return 1;
    }
    std::string algorithm = parser.getAlgorithm();
    std::string pattern = parser.getPattern();
    std::string filename = parser.getFilename();

    std::cout << "Algorithm: " << algorithm << "\nPattern: " << pattern << "\nFilename: " << filename << std::endl;

    // TODO: Wywołaj odpowiedni algorytm

    return 0;
}