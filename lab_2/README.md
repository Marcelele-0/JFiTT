# Lab 2 - Flex Tasks

## Struktura projektu

- `flex/` - Pliki `.lx` (definicje Flex)
- `c_files/` - Pliki `.c` (skompilowany kod C)
- `executables/` - Pliki wykonywalne
- `test_files/` - Pliki testowe

---

## Instrukcje kompilacji i uruchomienia

### Zadanie 1

**Kompilacja:**
```bash
flex -o c_files/zadanie1.c flex/zadanie1.lx
gcc -o executables/zadanie1 c_files/zadanie1.c -lfl -lm
```

**Uruchomienie:**
```bash
./executables/zadanie1 test_files/plik_testowy.txt
```

---

### Zadanie 2

**Kompilacja:**
```bash
flex -o c_files/zadanie2.c flex/zadanie2.lx
gcc -o executables/zadanie2 c_files/zadanie2.c -lfl -lm
```

**Uruchomienie:**
```bash
./executables/zadanie2 test_files/test.py
```

---

### Zadanie 3

**Kompilacja:**
```bash
flex -o c_files/zadanie3.c flex/zadanie3.lx
gcc -o executables/zadanie3 c_files/zadanie3.c -lfl -lm
```

**Uruchomienie:**
```bash
./executables/zadanie3 test_files/test.cpp
```

---

### Zadanie 4

**Kompilacja:**
```bash
flex -o c_files/zadanie4.c flex/zadanie4.lx
gcc -o executables/zadanie4 c_files/zadanie4.c -lfl -lm
```

**Uruchomienie:**
```bash
./executables/zadanie4
```

