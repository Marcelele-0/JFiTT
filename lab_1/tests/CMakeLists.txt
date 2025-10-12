add_executable(tests
    test_main.cpp
)

enable_testing()
add_test(NAME PatternSearchTests COMMAND tests)