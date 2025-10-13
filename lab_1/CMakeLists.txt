cmake_minimum_required(VERSION 3.14)
project(pattern_search)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

add_executable(pattern_search
    src/main.cpp
    src/InputParser.cpp
    src/FiniteAutomate.cpp
    src/KMPMatcher.cpp
)

add_executable(test_fa
    test/TestFiniteAutomate.cpp
    src/FiniteAutomate.cpp
)
target_include_directories(test_fa PRIVATE include)

add_executable(test_kmp
    test/TestKMPMatcher.cpp
    src/KMPMatcher.cpp
)
target_include_directories(test_kmp PRIVATE include)

add_executable(test_parser
    test/TestInputParser.cpp
    src/InputParser.cpp
)
target_include_directories(test_parser PRIVATE include)