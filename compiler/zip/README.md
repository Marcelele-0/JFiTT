# Kompilator IMP

Kompilator języka IMP do kodu maszynowego maszyny wirtualnej.

## Wymagania

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) - menedżer pakietów Python

## Instalacja

```bash
# Instaluj uv (jeśli nie ma)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instaluj zależności
uv sync
```

## Użycie

```bash
# Kompilacja pliku .imp do .mr
uv run python src/main.py <plik_wejściowy.imp> <plik_wyjściowy.mr>

# Przykład
uv run python src/main.py examples/example0.imp output.mr
```

## Uruchomienie skompilowanego kodu

Użyj maszyny wirtualnej do uruchomienia pliku `.mr`:

```bash
./maszyna-wirtualna output.mr
```

## Struktura projektu

```
src/
├── main.py        # Punkt wejścia
├── lexer.py       # Analizator leksykalny
├── parser_.py     # Parser (gramatyka)
├── ast_nodes.py   # Definicje węzłów AST
├── semantic.py    # Analiza semantyczna
├── symbol_table.py # Tablica symboli
└── code_gen.py    # Generator kodu
```
