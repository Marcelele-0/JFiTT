#!/bin/bash

# Skrypt do kompilacji i uruchomienia wszystkich zadań

REPORT="RAPORT.txt"
PROJECT_DIR="/home/licho/.programming/UNI/JFiTT/lab_2"

# Funkcja do dumpowania do raportu i na ekran
log_output() {
    echo "$1" | tee -a "$REPORT"
}

# Czyszczenie starego raportu
rm -f "$REPORT"

# Początek raportu
log_output "==============================================="
log_output "RAPORT Z URUCHOMIENIA WSZYSTKICH ZADAŃ - LAB 2"
log_output "==============================================="
log_output "Data: $(date)"
log_output "Katalog projektu: $PROJECT_DIR"
log_output ""

cd "$PROJECT_DIR"

# ===== ZADANIE 1 =====
log_output "###################################################"
log_output "# ZADANIE 1 - Czyszczenie białych znaków"
log_output "###################################################"
log_output ""

log_output "Kompilacja zadania 1..."
flex -o c_files/zadanie1.c flex/zadanie1.lx 2>&1 | tee -a "$REPORT"
gcc -o executables/zadanie1 c_files/zadanie1.c -lfl -lm 2>&1 | tee -a "$REPORT"

if [ -f executables/zadanie1 ]; then
    log_output "✓ Kompilacja sukcesu"
    log_output ""
    log_output "Uruchomienie zadania 1 na pliku test_files/plik_testowy.txt:"
    log_output "--- WYJŚCIE ---"
    ./executables/zadanie1 test_files/plik_testowy.txt 2>&1 | tee -a "$REPORT"
    log_output "--- KONIEC WYJŚCIA ---"
else
    log_output "✗ Błąd kompilacji zadania 1"
fi

log_output ""
log_output ""

# ===== ZADANIE 2 =====
log_output "###################################################"
log_output "# ZADANIE 2 - Usuwanie komentarzy Python"
log_output "###################################################"
log_output ""

log_output "Kompilacja zadania 2..."
flex -o c_files/zadanie2.c flex/zadanie2.lx 2>&1 | tee -a "$REPORT"
gcc -o executables/zadanie2 c_files/zadanie2.c -lfl -lm 2>&1 | tee -a "$REPORT"

if [ -f executables/zadanie2 ]; then
    log_output "✓ Kompilacja sukcesu"
    log_output ""
    log_output "Uruchomienie zadania 2 na pliku test_files/test.py:"
    log_output "--- WYJŚCIE ---"
    ./executables/zadanie2 test_files/test.py 2>&1 | tee -a "$REPORT"
    log_output "--- KONIEC WYJŚCIA ---"
else
    log_output "✗ Błąd kompilacji zadania 2"
fi

log_output ""
log_output ""

# ===== ZADANIE 3 =====
log_output "###################################################"
log_output "# ZADANIE 3 - Usuwanie komentarzy C/C++"
log_output "###################################################"
log_output ""

log_output "Kompilacja zadania 3..."
flex -o c_files/zadanie3.c flex/zadanie3.lx 2>&1 | tee -a "$REPORT"
gcc -o executables/zadanie3 c_files/zadanie3.c -lfl -lm 2>&1 | tee -a "$REPORT"

if [ -f executables/zadanie3 ]; then
    log_output "✓ Kompilacja sukcesu"
    log_output ""
    log_output "--- WERSJA BEZ DOXYGENU (domyślnie) ---"
    log_output "Uruchomienie na pliku test_files/test.cpp:"
    log_output "--- WYJŚCIE ---"
    ./executables/zadanie3 test_files/test.cpp 2>&1 | tee -a "$REPORT"
    log_output "--- KONIEC WYJŚCIA ---"
    log_output ""
    log_output "--- WERSJA Z DOXYGENIEM ---"
    log_output "Uruchomienie na pliku test_files/test.cpp z flagą -d:"
    log_output "--- WYJŚCIE ---"
    ./executables/zadanie3 -d test_files/test.cpp 2>&1 | tee -a "$REPORT"
    log_output "--- KONIEC WYJŚCIA ---"
else
    log_output "✗ Błąd kompilacji zadania 3"
fi

log_output ""
log_output ""

# ===== ZADANIE 4 =====
log_output "###################################################"
log_output "# ZADANIE 4 - Kalkulator RPN (Reverse Polish Notation)"
log_output "###################################################"
log_output ""

log_output "Kompilacja zadania 4..."
flex -o c_files/zadanie4.c flex/zadanie4.lx 2>&1 | tee -a "$REPORT"
gcc -o executables/zadanie4 c_files/zadanie4.c -lfl -lm 2>&1 | tee -a "$REPORT"

if [ -f executables/zadanie4 ]; then
    log_output "✓ Kompilacja sukcesu"
    log_output ""
    log_output "Uruchomienie zadania 4 z testami:"
    log_output ""
    
    # Test 1: 2 3 + 4 * = 20
    log_output "Test 1: 2 3 + 4 *"
    log_output "Oczekiwane: = 20"
    log_output "Faktyczne:"
    echo "2 3 + 4 *" | ./executables/zadanie4 2>&1 | tee -a "$REPORT"
    log_output ""
    
    # Test 2: 1 2 3 4 + * -  = -13
    log_output "Test 2: 1 2 3 4 + * -"
    log_output "Oczekiwane: = -13"
    log_output "Faktyczne:"
    echo "1 2 3 4 + * -" | ./executables/zadanie4 2>&1 | tee -a "$REPORT"
    log_output ""
    
    # Test 3: -1 2 -3 4 + * - = -3
    log_output "Test 3: -1 2 -3 4 + * -"
    log_output "Oczekiwane: = -3"
    log_output "Faktyczne:"
    echo "-1 2 -3 4 + * -" | ./executables/zadanie4 2>&1 | tee -a "$REPORT"
    log_output ""
    
    # Test 4: 8 -7 6 -5 4 * -3 % / - + = 4
    log_output "Test 4: 8 -7 6 -5 4 * -3 % / - +"
    log_output "Oczekiwane: = 4"
    log_output "Faktyczne:"
    echo "8 -7 6 -5 4 * -3 % / - +" | ./executables/zadanie4 2>&1 | tee -a "$REPORT"
    log_output ""
    
    # Test 5: 2 3 2 ^ ^ = 512
    log_output "Test 5: 2 3 2 ^ ^"
    log_output "Oczekiwane: = 512"
    log_output "Faktyczne:"
    echo "2 3 2 ^ ^" | ./executables/zadanie4 2>&1 | tee -a "$REPORT"
    log_output ""
    
    # Test 6: 2 3+* (błąd - za mała liczba argumentów)
    log_output "Test 6: 2 3+*"
    log_output "Oczekiwane: Błąd: za mała liczba argumentów"
    log_output "Faktyczne:"
    echo "2 3+*" | ./executables/zadanie4 2>&1 | tee -a "$REPORT"
    log_output ""
    
    # Test 7: 2 3 4 + (błąd - za mała liczba operatorów)
    log_output "Test 7: 2 3 4 +"
    log_output "Oczekiwane: Błąd: za mała liczba operatorów"
    log_output "Faktyczne:"
    echo "2 3 4 +" | ./executables/zadanie4 2>&1 | tee -a "$REPORT"
    log_output ""
    
    # Test 8: 2.4 3+ (błąd - zły symbol ".")
    log_output "Test 8: 2.4 3+"
    log_output "Oczekiwane: Błąd: zły symbol \".\""
    log_output "Faktyczne:"
    echo "2.4 3+" | ./executables/zadanie4 2>&1 | tee -a "$REPORT"
    log_output ""
    
else
    log_output "✗ Błąd kompilacji zadania 4"
fi

log_output ""
log_output "==============================================="
log_output "KONIEC RAPORTU"
log_output "==============================================="
log_output "Raport zapisany w: $REPORT"
