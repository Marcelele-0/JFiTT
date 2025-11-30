# GF(1234577) Calculator

A calculator for the Galois Field GF(1234577), supporting basic arithmetic, modular division, and exponentiation. It outputs the result in Reverse Polish Notation (RPN) along with the computed value.

## Features
- Arithmetic modulo 1234577.
- Negative number handling (normalized to [0, P-1]).
- Division via modular inverse.
- Fast modular exponentiation.
- RPN output with constant folding for unary negation.

## Building
Requirements: `gcc` (or `g++`), `bison`, `flex`, `make`.

```bash
make
```

Enter expressions, e.g.:
```
2 + 3
-1
(2 + 3) * 4
```

## Structure
- `src/`: Source files (`.c`, `.l`, `.y`).
- `include/`: Header files.
- `obj/`: Intermediate build files.
