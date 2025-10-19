import sys
from input_parser import InputParser
from finite_automate import FiniteAutomate


def main(argv=None):
    if argv is None:
        argv = sys.argv

    parser = InputParser(argv)
    if not parser.validate():
        return 1

    algorithm = parser.get_algorithm()
    pattern = parser.get_pattern()
    text = parser.get_text()
    alphabet = parser.get_alphabet()

    if algorithm == "FA":
        fa = FiniteAutomate(pattern, alphabet)
        fa.build_automate()
        occurrences = fa.run_search(text)
        for pos in occurrences:
            print(f"Pattern found at position: {pos}")
        return 0
    elif algorithm == "KMP":
        print("KMP algorithm not yet implemented in Python port", file=sys.stderr)
        return 2
    else:
        print(f"Unknown algorithm: {algorithm}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
