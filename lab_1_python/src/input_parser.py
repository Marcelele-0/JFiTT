import sys
from typing import Set

class InputParser:
    def __init__(self, argv):
        self.is_valid = False
        self.algorithm = ""
        self.pattern = ""
        self.text = ""
        self.alphabet = set()
        self.filename = ""

        if len(argv) != 4:
            print("Usage: <FA|KMP> <pattern> <filename>", file=sys.stderr)
            return

        self.algorithm = argv[1].upper()
        if self.algorithm not in ("FA", "KMP"):
            print(f"Unknown algorithm: {self.algorithm}", file=sys.stderr)
            return

        def unescape(s: str) -> str:
            out = []
            i = 0
            while i < len(s):
                if s[i] == '\\' and i + 1 < len(s):
                    i += 1
                    esc = s[i]
                    if esc == 'n':
                        out.append('\n')
                    elif esc == 'r':
                        out.append('\r')
                    elif esc == 't':
                        out.append('\t')
                    elif esc == '\\':
                        out.append('\\')
                    else:
                        out.append(esc)
                else:
                    out.append(s[i])
                i += 1
            return ''.join(out)

        self.pattern = unescape(argv[2])
        # remove stray CR that may come from Windows line endings
        self.pattern = self.pattern.replace('\r', '')

        self.filename = argv[3]

        # Read text from file or stdin
        try:
            if self.filename == '-':
                self.text = sys.stdin.read()
            else:
                with open(self.filename, 'r', encoding='utf-8', errors='replace') as f:
                    self.text = f.read()
        except Exception as e:
            print(f"Cannot open file: {self.filename} ({e})", file=sys.stderr)
            return

        # Normalize text line endings
        self.text = self.text.replace('\r', '')

        if not self.pattern:
            print("Pattern is empty", file=sys.stderr)
            return
        if not self.text:
            print("Text is empty", file=sys.stderr)
            return

        # Build alphabet from text and pattern
        for c in self.text:
            self.alphabet.add(c)
        for c in self.pattern:
            self.alphabet.add(c)

        self.is_valid = True

    def validate(self) -> bool:
        return self.is_valid

    def get_algorithm(self) -> str:
        return self.algorithm

    def get_pattern(self) -> str:
        return self.pattern

    def get_text(self) -> str:
        return self.text

    def get_alphabet(self) -> Set[str]:
        return set(self.alphabet)

    def get_filename(self) -> str:
        return self.filename
