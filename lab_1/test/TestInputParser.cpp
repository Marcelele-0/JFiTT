#include <cassert>
#include <fstream>
#include <iostream>
#include <set>
#include "../include/InputParser.hpp"

void test_parser_success() {
    // Stwórz tymczasowy plik z tekstem
    const char* tmpname = "test_tmp_text.txt";
    std::ofstream out(tmpname);
    out << "abcxabcdabxabcdabcdabcy";
    out.close();

    const char* argv[] = {"prog", "FA", "abc", tmpname};
    InputParser parser(4, const_cast<char**>(argv));
    assert(parser.validate());
    assert(parser.getAlgorithm() == "FA");
    assert(parser.getPattern() == "abc");
    assert(parser.getFilename() == tmpname);
    std::string text = parser.getText();
    assert(!text.empty());
    std::set<char> alphabet = parser.getAlphabet();
    // alphabet should contain at least 'a','b','c','x','d','y'
    for (char c : std::string("abcdxy")) {
        assert(alphabet.count(c) == 1);
    }

    // cleanup
    std::remove(tmpname);
    std::cout << "test_parser_success passed\n";
}

void test_parser_failure() {
    const char* argv[] = {"prog", "FA", "abc"}; // wrong argc
    InputParser parser(3, const_cast<char**>(argv));
    assert(!parser.validate());
    std::cout << "test_parser_failure passed\n";
}

void test_parser_special_chars() {
    const char* tmpname = "test_tmp_text_special.txt";
    std::ofstream out(tmpname);
    // include special chars: %, /, >, and double quotes
    out << R"TXT(Hello%/> "quoted" end%/>)TXT";
    out.close();

    const char* argv[] = {"prog", "FA", "%/>", tmpname};
    InputParser parser(4, const_cast<char**>(argv));
    assert(parser.validate());
    assert(parser.getPattern() == "%/>");
    std::set<char> alphabet = parser.getAlphabet();
    assert(alphabet.count('%') == 1);
    assert(alphabet.count('/') == 1);
    assert(alphabet.count('>') == 1);
    assert(alphabet.count('"') == 1);

    std::remove(tmpname);
    std::cout << "test_parser_special_chars passed\n";
}

int main() {
    test_parser_success();
    test_parser_failure();
    test_parser_special_chars();
    std::cout << "All InputParser tests passed!\n";
    return 0;
}
