"""
Kompilator języka IMP - Generator kodu maszynowego.

Generuje kod dla maszyny wirtualnej z rejestrami a-h.
"""

from ast_nodes import *


class CodeGenerator:
    """Generator kodu maszynowego dla języka IMP."""

    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.code = []
        self.current_scope = 'GLOBAL'
        self.label_counter = 0
        self.reg_stack = ['g']
        self.stack_depth = 0
        self.mem_spill_start = 1000

        # Inicjalizacja wskaźnika stosu (SP) w rejestrze h
        raw_sp = self.symbol_table.memory_counter + 1000
        self.sp_start = 1 << (raw_sp - 1).bit_length()

    def emit(self, instr):
        """Dodaje instrukcję do kodu wynikowego."""
        if '\n' in instr:
            raise ValueError(f"Instrukcja zawiera newline: {repr(instr)}")
        self.code.append(instr)

    def get_new_label(self, prefix):
        """Generuje unikalną etykietę."""
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def get_code(self):
        """Zwraca końcowy kod po optymalizacjach."""
        self._optimize_jumps()
        self._optimize_tail_calls()
        self._remove_dead_code()
        self._resolve_labels()
        return '\n'.join(self.code)

    # ========== OPTYMALIZACJE ==========

    def _optimize_jumps(self):
        """Optymalizuje skoki (chain jumping, redundant jumps)."""
        # 1. Jump Chaining
        label_map = {}
        for i, line in enumerate(self.code):
            if line.endswith(':'):
                label = line[:-1]
                if i + 1 < len(self.code):
                    next_line = self.code[i + 1].strip()
                    if next_line.startswith('JUMP '):
                        target = next_line.split()[1]
                        label_map[label] = target

        # Rozwiązanie łańcuchów
        for label in list(label_map.keys()):
            target = label_map[label]
            visited = {label}
            while target in label_map:
                if target in visited:
                    break
                visited.add(target)
                target = label_map[target]
            label_map[label] = target

        # Zastosowanie
        if label_map:
            new_code = []
            for line in self.code:
                parts = line.split()
                if len(parts) > 1 and parts[0] in ['JUMP', 'JZERO', 'JPOS']:
                    if parts[1] in label_map:
                        new_code.append(f"{parts[0]} {label_map[parts[1]]}")
                    else:
                        new_code.append(line)
                else:
                    new_code.append(line)
            self.code = new_code

        # 2. Usunięcie skoków do następnej linii
        optimized = []
        i = 0
        while i < len(self.code):
            line = self.code[i]
            if line.startswith('JUMP '):
                target = line.split()[1]
                if i + 1 < len(self.code) and self.code[i + 1].strip() == f"{target}:":
                    i += 1
                    continue
            optimized.append(line)
            i += 1
        self.code = optimized

    def _optimize_tail_calls(self):
        """Optymalizacja ogonowych wywołań rekurencyjnych (TCO)."""
        new_code = []
        i = 0
        while i < len(self.code):
            line = self.code[i]
            if line.startswith("CALL "):
                j = i + 1
                while j < len(self.code) and self.code[j].strip().endswith(':'):
                    j += 1

                if j + 2 < len(self.code):
                    l1 = self.code[j].strip()
                    l2 = self.code[j + 1].strip()
                    l3 = self.code[j + 2].strip()

                    if l1 == "DEC h" and l2 == "RLOAD h" and l3 == "RTRN":
                        target = line.split()[1]
                        new_code.append("DEC h")
                        new_code.append("RLOAD h")
                        new_code.append(f"JUMP {target}")
                        i += 1
                        continue

            new_code.append(line)
            i += 1
        self.code = new_code

    def _remove_dead_code(self):
        """Usuwa martwy kod po bezwarunkowych skokach."""
        new_code = []
        is_dead = False

        for line in self.code:
            stripped = line.strip()

            if stripped.endswith(':'):
                is_dead = False
                new_code.append(line)
                continue

            if is_dead:
                continue

            new_code.append(line)

            if stripped.startswith('JUMP ') or stripped == 'RTRN' or stripped == 'HALT':
                is_dead = True

        self.code = new_code

    def _resolve_labels(self):
        """Rozwiązuje etykiety na numery linii."""
        # Peephole optimization
        optimized = []
        i = 0
        while i < len(self.code):
            line = self.code[i].strip()

            if i + 1 < len(self.code):
                next_line = self.code[i + 1].strip()

                # STORE X, LOAD X -> STORE X
                if line.startswith("STORE ") and next_line.startswith("LOAD "):
                    if line.split()[1] == next_line.split()[1]:
                        optimized.append(line)
                        i += 2
                        continue

                # SWP X, SWP X -> nic
                if line.startswith("SWP ") and next_line.startswith("SWP "):
                    if line.split()[1] == next_line.split()[1]:
                        i += 2
                        continue

                # LOAD X, LOAD Y -> LOAD Y
                if line.startswith("LOAD ") and next_line.startswith("LOAD "):
                    optimized.append(next_line)
                    i += 2
                    continue

            optimized.append(line)
            i += 1

        self.code = optimized

        # Zbieranie etykiet
        labels = {}
        clean_code = []
        line_counter = 0

        for line in self.code:
            line = line.strip()
            if line.endswith(':'):
                labels[line[:-1]] = line_counter
            else:
                clean_code.append(line)
                line_counter += 1

        # Zamiana etykiet na numery
        final_code = []
        for line in clean_code:
            parts = line.split()
            if parts[0] in ['JUMP', 'JPOS', 'JZERO', 'CALL']:
                target = parts[1]
                if target in labels:
                    final_code.append(f"{parts[0]} {labels[target]}")
                else:
                    final_code.append(line)
            else:
                final_code.append(line)

        self.code = final_code

    # ========== GENERACJA KODU ==========

    def generate(self, ast):
        """Generuje kod dla całego programu."""
        # Inicjalizacja SP
        self.generate_constant(self.sp_start)
        self.emit("SWP h")

        self.emit("JUMP MAIN")

        for proc in ast.procedures:
            self._generate_procedure(proc)

        self.emit("MAIN:")
        self._generate_block(ast.main)
        self.emit("HALT")

    def _generate_procedure(self, node):
        """Generuje kod procedury."""
        self.current_scope = node.name
        self.symbol_table.enter_scope(node.name)

        self.emit(f"PROC_{node.name}:")
        self.emit("RSTORE h")  # Zapisz adres powrotu
        self.emit("INC h")     # Inkrementuj SP

        self._generate_block(node)

        self.emit("DEC h")     # Dekrementuj SP
        self.emit("RLOAD h")   # Załaduj adres powrotu
        self.emit("RTRN")      # Powrót

        self.current_scope = 'GLOBAL'
        self.symbol_table.exit_scope()

    def _generate_block(self, node):
        """Generuje kod bloku poleceń."""
        for cmd in node.commands:
            self.visit(cmd)

    def visit(self, node):
        """Wywołuje odpowiednią metodę wizytatora."""
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, self._generic_visit)
        visitor(node)

    def _generic_visit(self, node):
        raise Exception(f"Brak wizytatora dla {node.__class__.__name__}")

    # ========== GENERACJA STAŁYCH ==========

    def generate_constant(self, value):
        """Generuje stałą wartość w akumulatorze."""
        self.emit("RST a")
        if value == 0:
            return

        bin_str = bin(value)[2:]
        for bit in bin_str:
            self.emit("SHL a")
            if bit == '1':
                self.emit("INC a")

    def is_power_of_two(self, n):
        return n > 0 and (n & (n - 1)) == 0

    def get_power_of_two(self, n):
        return n.bit_length() - 1

    # ========== WIZYTATORY ==========

    def visit_Assign(self, node):
        """Przypisanie: identifier := expression."""
        if node.identifier.index is not None:
            # Tablica: tab[i] := expr
            sym = self.symbol_table.get(node.identifier.name)
            self._load_index(node.identifier.index)

            if sym.array_range is not None:
                start = sym.array_range[0]
                loc_idx = self.mem_spill_start + self.stack_depth
                self.emit(f"STORE {loc_idx}")
                self.generate_constant(start)
                self.emit("SWP b")
                self.emit(f"LOAD {loc_idx}")
                self.emit("SUB b")
                self.emit("SWP b")
                self.generate_constant(sym.address)
                self.emit("ADD b")
            else:
                self.emit("SWP b")
                self.emit(f"LOAD {sym.address}")
                self.emit("ADD b")

            loc = self.mem_spill_start + self.stack_depth
            self.emit(f"STORE {loc}")

            self.stack_depth += 1
            self.visit(node.expression)
            self.stack_depth -= 1

            self.emit("SWP b")
            self.emit(f"LOAD {loc}")
            self.emit("SWP b")
            self.emit("RSTORE b")
        else:
            # Prosta zmienna
            self.visit(node.expression)
            sym = self.symbol_table.get(node.identifier.name)

            if self._is_reference_param(sym):
                self.emit("SWP b")
                self.emit(f"LOAD {sym.address}")
                self.emit("SWP b")
                self.emit("RSTORE b")
            else:
                self.emit(f"STORE {sym.address}")

    def visit_Identifier(self, node):
        """Ładuje wartość identyfikatora do akumulatora."""
        sym = self.symbol_table.get(node.name)

        if node.index:
            self._load_index(node.index)

            if sym.array_range is not None:
                start = sym.array_range[0]
                if start == 0:
                    self.emit("SWP b")
                    self.generate_constant(sym.address)
                    self.emit("ADD b")
                else:
                    loc_idx = self.mem_spill_start + self.stack_depth
                    self.emit(f"STORE {loc_idx}")
                    self.generate_constant(start)
                    self.emit("SWP b")
                    self.emit(f"LOAD {loc_idx}")
                    self.emit("SUB b")
                    self.emit("SWP b")
                    self.generate_constant(sym.address)
                    self.emit("ADD b")
            else:
                self.emit("SWP b")
                self.emit(f"LOAD {sym.address}")
                self.emit("ADD b")

            self.emit("SWP b")
            self.emit("RLOAD b")
        else:
            if self._is_reference_param(sym):
                self.emit(f"LOAD {sym.address}")
                self.emit("SWP b")
                self.emit("RLOAD b")
            elif self._is_const_param(sym):
                self.emit(f"LOAD {sym.address}")
            else:
                self.emit(f"LOAD {sym.address}")

    def visit_Number(self, node):
        """Ładuje stałą liczbową."""
        self.generate_constant(node.value)

    def visit_BinaryOp(self, node):
        """Operacje binarne: +, -, *, /, %."""
        # Constant folding
        if isinstance(node.left, Number) and isinstance(node.right, Number):
            val = self._fold_constants(node)
            self.generate_constant(val)
            return

        # Strength reduction
        if self._try_strength_reduction(node):
            return

        # Optymalizacje INC/DEC
        if self._try_inc_dec_optimization(node):
            return

        if node.op in ['+', '-']:
            self._generate_add_sub(node)
        elif node.op in ['*', '/', '%']:
            self._generate_mul_div_mod(node)

    def visit_If(self, node):
        """Instrukcja warunkowa IF."""
        else_label = self.get_new_label("IF_ELSE")
        end_label = self.get_new_label("IF_END")

        self._generate_condition_jump(node.condition, else_label, jump_if_true=False)

        for cmd in node.then_commands:
            self.visit(cmd)
        self.emit(f"JUMP {end_label}")

        self.emit(f"{else_label}:")
        if node.else_commands:
            for cmd in node.else_commands:
                self.visit(cmd)

        self.emit(f"{end_label}:")

    def visit_While(self, node):
        """Pętla WHILE."""
        start_label = self.get_new_label("WHILE_START")
        end_label = self.get_new_label("WHILE_END")

        self.emit(f"{start_label}:")
        self._generate_condition_jump(node.condition, end_label, jump_if_true=False)

        for cmd in node.commands:
            self.visit(cmd)

        self.emit(f"JUMP {start_label}")
        self.emit(f"{end_label}:")

    def visit_Repeat(self, node):
        """Pętla REPEAT...UNTIL."""
        start_label = self.get_new_label("REPEAT_START")

        self.emit(f"{start_label}:")

        for cmd in node.commands:
            self.visit(cmd)

        self._generate_condition_jump(node.condition, start_label, jump_if_true=False)

    def visit_For(self, node):
        """Pętla FOR."""
        self.visit(node.start_expr)
        sym = self.symbol_table.get(node.iterator)
        self.emit(f"STORE {sym.address}")

        limit_address = self.symbol_table.memory_counter
        self.symbol_table.memory_counter += 1

        self.visit(node.end_expr)
        self.emit(f"STORE {limit_address}")

        start_label = self.get_new_label("FOR_START")
        end_label = self.get_new_label("FOR_END")

        # Początkowe sprawdzenie zakresu
        self.emit(f"LOAD {limit_address}")
        self.emit("STORE 1")
        self.emit(f"LOAD {sym.address}")
        self.emit("STORE 0")

        if not node.down_to:
            self.emit("LOAD 0"); self.emit("SWP b"); self.emit("LOAD 1")
            self.emit("SWP b"); self.emit("SUB b")
            self.emit(f"JPOS {end_label}")
        else:
            self.emit("LOAD 1"); self.emit("SWP b"); self.emit("LOAD 0")
            self.emit("SWP b"); self.emit("SUB b")
            self.emit(f"JPOS {end_label}")

        self.emit(f"{start_label}:")

        for cmd in node.commands:
            self.visit(cmd)

        # Sprawdzenie zakończenia
        self.emit(f"LOAD {sym.address}")
        self.emit("STORE 0")
        self.emit(f"LOAD {limit_address}")
        self.emit("STORE 1")

        if not node.down_to:
            self.emit("LOAD 1"); self.emit("SWP b"); self.emit("LOAD 0")
            self.emit("SWP b"); self.emit("SUB b")
            self.emit(f"JZERO {end_label}")
        else:
            self.emit("LOAD 0"); self.emit("SWP b"); self.emit("LOAD 1")
            self.emit("SWP b"); self.emit("SUB b")
            self.emit(f"JZERO {end_label}")

        # Aktualizacja iteratora
        self.emit(f"LOAD {sym.address}")
        if not node.down_to:
            self.emit("INC a")
        else:
            self.emit("DEC a")
        self.emit(f"STORE {sym.address}")

        self.emit(f"JUMP {start_label}")
        self.emit(f"{end_label}:")

    def visit_ProcCall(self, node):
        """Wywołanie procedury."""
        proc_syms = self.symbol_table.get_all_in_scope(node.name)
        proc_info = self.symbol_table.get_procedure(node.name)
        args_info = proc_info['args']

        for i, arg_expr in enumerate(node.args):
            arg_sym = self.symbol_table.get(arg_expr)
            param_name = args_info[i][1]
            param_type = args_info[i][0]
            param_sym = proc_syms[param_name]

            if param_type == 'CONST':
                self.visit_Identifier(Identifier(arg_expr))
            else:
                self._pass_by_reference(arg_sym)

                if arg_sym.type == 'ARRAY' and arg_sym.array_range is not None:
                    start_index = arg_sym.array_range[0]
                    loc_addr = self.mem_spill_start + self.stack_depth
                    loc_start = self.mem_spill_start + self.stack_depth + 1

                    self.emit(f"STORE {loc_addr}")
                    self.generate_constant(start_index)
                    self.emit(f"STORE {loc_start}")
                    self.emit(f"LOAD {loc_addr}")
                    self.emit("SWP b")
                    self.emit(f"LOAD {loc_start}")
                    self.emit("SWP b")
                    self.emit("SUB b")

            self.emit(f"STORE {param_sym.address}")

        self.emit(f"CALL PROC_{node.name}")

    def visit_Read(self, node):
        """Instrukcja READ."""
        sym = self.symbol_table.get(node.identifier.name)

        if node.identifier.index is not None:
            self._load_index(node.identifier.index)

            if sym.array_range is not None:
                start = sym.array_range[0]
                self.emit("STORE 0")
                self.generate_constant(start)
                self.emit("SWP b")
                self.emit("LOAD 0")
                self.emit("SUB b")
                self.emit("SWP b")
                self.generate_constant(sym.address)
                self.emit("ADD b")
            else:
                self.emit("SWP b")
                self.emit(f"LOAD {sym.address}")
                self.emit("ADD b")

            self.emit("SWP b")
            self.emit("READ")
            self.emit("RSTORE b")
        else:
            if self._is_reference_param(sym):
                self.emit(f"LOAD {sym.address}")
                self.emit("SWP b")
                self.emit("READ")
                self.emit("RSTORE b")
            else:
                self.emit("READ")
                self.emit(f"STORE {sym.address}")

    def visit_Write(self, node):
        """Instrukcja WRITE."""
        self.visit(node.value)
        self.emit("WRITE")

    # ========== METODY POMOCNICZE ==========

    def _load_index(self, index):
        """Ładuje indeks tablicy do akumulatora."""
        if isinstance(index, int):
            self.generate_constant(index)
        elif isinstance(index, str):
            idx_sym = self.symbol_table.get(index)
            if self._is_reference_param(idx_sym):
                self.emit(f"LOAD {idx_sym.address}")
                self.emit("SWP b")
                self.emit("RLOAD b")
            elif self._is_const_param(idx_sym):
                self.emit(f"LOAD {idx_sym.address}")
            else:
                self.emit(f"LOAD {idx_sym.address}")
        else:
            self.generate_constant(index)

    def _is_reference_param(self, sym):
        """Sprawdza czy symbol jest parametrem przekazywanym przez referencję."""
        if self.current_scope == 'GLOBAL' or sym.scope == 'GLOBAL':
            return False
        try:
            proc_info = self.symbol_table.get_procedure(self.current_scope)
            param_info = next((arg for arg in proc_info['args'] if arg[1] == sym.name), None)
            return param_info and param_info[0] not in ['CONST']
        except:
            return False

    def _is_const_param(self, sym):
        """Sprawdza czy symbol jest parametrem CONST."""
        if self.current_scope == 'GLOBAL' or sym.scope == 'GLOBAL':
            return False
        try:
            proc_info = self.symbol_table.get_procedure(self.current_scope)
            param_info = next((arg for arg in proc_info['args'] if arg[1] == sym.name), None)
            return param_info and param_info[0] == 'CONST'
        except:
            return False

    def _pass_by_reference(self, arg_sym):
        """Przekazuje argument przez referencję."""
        if self.current_scope != 'GLOBAL':
            proc_info = self.symbol_table.get_procedure(self.current_scope)
            arg_param_info = next((arg for arg in proc_info['args'] if arg[1] == arg_sym.name), None)

            if arg_param_info:
                if arg_param_info[0] == 'CONST':
                    self.generate_constant(arg_sym.address)
                else:
                    self.emit(f"LOAD {arg_sym.address}")
            else:
                self.generate_constant(arg_sym.address)
        else:
            self.generate_constant(arg_sym.address)

    def _fold_constants(self, node):
        """Składanie stałych w czasie kompilacji."""
        left, right = node.left.value, node.right.value
        if node.op == '+':
            return left + right
        elif node.op == '-':
            return max(0, left - right)
        elif node.op == '*':
            return left * right
        elif node.op == '/':
            return left // right if right != 0 else 0
        elif node.op == '%':
            return left % right if right != 0 else 0
        return 0

    def _try_strength_reduction(self, node):
        """Redukcja siły dla mnożenia/dzielenia przez potęgi 2."""
        if node.op == '*':
            if isinstance(node.right, Number) and node.right.value == 0:
                self.emit("RST a")
                return True
            if isinstance(node.left, Number) and node.left.value == 0:
                self.emit("RST a")
                return True
            if isinstance(node.right, Number) and self.is_power_of_two(node.right.value):
                self.visit(node.left)
                for _ in range(self.get_power_of_two(node.right.value)):
                    self.emit("SHL a")
                return True
            if isinstance(node.left, Number) and self.is_power_of_two(node.left.value):
                self.visit(node.right)
                for _ in range(self.get_power_of_two(node.left.value)):
                    self.emit("SHL a")
                return True

        elif node.op == '/':
            if isinstance(node.right, Number) and self.is_power_of_two(node.right.value):
                self.visit(node.left)
                for _ in range(self.get_power_of_two(node.right.value)):
                    self.emit("SHR a")
                return True

        elif node.op == '%':
            if isinstance(node.right, Number) and self.is_power_of_two(node.right.value):
                self.visit(node.left)
                power = self.get_power_of_two(node.right.value)
                loc = self.mem_spill_start + self.stack_depth
                self.emit(f"STORE {loc}")
                for _ in range(power):
                    self.emit("SHR a")
                for _ in range(power):
                    self.emit("SHL a")
                self.emit("SWP b")
                self.emit(f"LOAD {loc}")
                self.emit("SUB b")
                return True

        return False

    def _try_inc_dec_optimization(self, node):
        """Optymalizacja dla x+1, x-1 itp."""
        if node.op == '+':
            if isinstance(node.right, Number) and 0 < node.right.value <= 10:
                self.visit(node.left)
                for _ in range(node.right.value):
                    self.emit("INC a")
                return True
            if isinstance(node.left, Number) and 0 < node.left.value <= 10:
                self.visit(node.right)
                for _ in range(node.left.value):
                    self.emit("INC a")
                return True

        elif node.op == '-':
            if isinstance(node.right, Number) and 0 < node.right.value <= 10:
                self.visit(node.left)
                for _ in range(node.right.value):
                    self.emit("DEC a")
                return True

        return False

    def _generate_add_sub(self, node):
        """Generuje kod dla dodawania/odejmowania."""
        self.visit(node.left)

        if self.stack_depth < len(self.reg_stack):
            reg = self.reg_stack[self.stack_depth]
            self.emit(f"SWP {reg}")

            self.stack_depth += 1
            self.visit(node.right)
            self.stack_depth -= 1

            if node.op == '+':
                self.emit(f"ADD {reg}")
            else:
                self.emit(f"SWP {reg}")
                self.emit(f"SUB {reg}")
        else:
            loc = self.mem_spill_start + self.stack_depth
            self.emit(f"STORE {loc}")

            self.stack_depth += 1
            self.visit(node.right)
            self.stack_depth -= 1

            self.emit("SWP b")
            self.emit(f"LOAD {loc}")

            if node.op == '+':
                self.emit("ADD b")
            else:
                self.emit("SUB b")

    def _generate_mul_div_mod(self, node):
        """Generuje kod dla mnożenia/dzielenia/modulo."""
        self.visit(node.left)
        self.emit("STORE 0")

        self.visit(node.right)
        self.emit("STORE 1")

        if node.op == '*':
            self.generate_multiplication()
        elif node.op == '/':
            self.generate_division()
        elif node.op == '%':
            self.generate_modulo()

    def generate_multiplication(self):
        """Algorytm mnożenia przez kolejne podwajanie."""
        self.emit("LOAD 1"); self.emit("SWP b")
        self.emit("LOAD 0"); self.emit("SWP c")
        self.emit("RST d")

        start = self.get_new_label("MULT_START")
        end = self.get_new_label("MULT_END")
        skip = self.get_new_label("MULT_SKIP")

        self.emit(f"{start}:")
        self.emit("SWP b")
        self.emit(f"JZERO {end}")
        self.emit("SWP b")

        self.emit("RST a"); self.emit("ADD b"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD b"); self.emit("SHR a"); self.emit("SHL a")
        self.emit("STORE 2")
        self.emit("LOAD 2"); self.emit("SWP f")
        self.emit("RST a"); self.emit("ADD b"); self.emit("SUB f")
        self.emit(f"JZERO {skip}")

        self.emit("SWP d"); self.emit("ADD c"); self.emit("SWP d")

        self.emit(f"{skip}:")
        self.emit("SWP c"); self.emit("SHL a"); self.emit("SWP c")
        self.emit("SWP b"); self.emit("SHR a"); self.emit("SWP b")
        self.emit(f"JUMP {start}")

        self.emit(f"{end}:")
        self.emit("SWP d")

    def generate_division(self):
        """Algorytm dzielenia."""
        self.emit("LOAD 1"); self.emit("SWP b")
        self.emit("LOAD 0"); self.emit("SWP c")

        zero = self.get_new_label("DIV_ZERO")
        self.emit("RST a"); self.emit("ADD b")
        self.emit(f"JZERO {zero}")

        self.emit("RST d")
        self.emit("RST a"); self.emit("INC a"); self.emit("SWP f")
        self.emit("RST a"); self.emit("ADD b"); self.emit("SWP e")

        align = self.get_new_label("DIV_ALIGN")
        align_end = self.get_new_label("DIV_ALIGN_END")

        self.emit(f"{align}:")
        self.emit("RST a"); self.emit("ADD e"); self.emit("SUB c")
        self.emit(f"JPOS {align_end}")
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHL a"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHL a"); self.emit("SWP f")
        self.emit(f"JUMP {align}")
        self.emit(f"{align_end}:")

        self.emit("RST a"); self.emit("ADD e"); self.emit("SHR a"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHR a"); self.emit("SWP f")

        loop = self.get_new_label("DIV_LOOP")
        end = self.get_new_label("DIV_END")

        self.emit(f"{loop}:")
        self.emit("RST a"); self.emit("ADD f")
        self.emit(f"JZERO {end}")

        skip = self.get_new_label("DIV_SKIP")
        self.emit("RST a"); self.emit("ADD e"); self.emit("SUB c")
        self.emit(f"JPOS {skip}")

        self.emit("RST a"); self.emit("ADD c"); self.emit("SUB e"); self.emit("SWP c")
        self.emit("RST a"); self.emit("ADD d"); self.emit("ADD f"); self.emit("SWP d")

        self.emit(f"{skip}:")
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHR a"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHR a"); self.emit("SWP f")
        self.emit(f"JUMP {loop}")

        self.emit(f"{end}:")
        self.emit("RST a"); self.emit("ADD d")
        self.emit(f"{zero}:")

    def generate_modulo(self):
        """Algorytm modulo."""
        self.emit("LOAD 1"); self.emit("SWP b")
        self.emit("LOAD 0"); self.emit("SWP c")

        zero = self.get_new_label("MOD_ZERO")
        self.emit("RST a"); self.emit("ADD b")
        self.emit(f"JZERO {zero}")

        self.emit("RST d")
        self.emit("RST a"); self.emit("INC a"); self.emit("SWP f")
        self.emit("RST a"); self.emit("ADD b"); self.emit("SWP e")

        align = self.get_new_label("MOD_ALIGN")
        align_end = self.get_new_label("MOD_ALIGN_END")

        self.emit(f"{align}:")
        self.emit("RST a"); self.emit("ADD e"); self.emit("SUB c")
        self.emit(f"JPOS {align_end}")
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHL a"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHL a"); self.emit("SWP f")
        self.emit(f"JUMP {align}")
        self.emit(f"{align_end}:")

        self.emit("RST a"); self.emit("ADD e"); self.emit("SHR a"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHR a"); self.emit("SWP f")

        loop = self.get_new_label("MOD_LOOP")
        end = self.get_new_label("MOD_END")

        self.emit(f"{loop}:")
        self.emit("RST a"); self.emit("ADD f")
        self.emit(f"JZERO {end}")

        skip = self.get_new_label("MOD_SKIP")
        self.emit("RST a"); self.emit("ADD e"); self.emit("SUB c")
        self.emit(f"JPOS {skip}")

        self.emit("RST a"); self.emit("ADD c"); self.emit("SUB e"); self.emit("SWP c")

        self.emit(f"{skip}:")
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHR a"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHR a"); self.emit("SWP f")
        self.emit(f"JUMP {loop}")

        self.emit(f"{end}:")
        self.emit("RST a"); self.emit("ADD c")
        self.emit(f"{zero}:")

    def _generate_condition_jump(self, node, label, jump_if_true=True):
        """Generuje skok warunkowy."""
        self.visit(node.left)
        self.emit("SWP g")

        self.stack_depth += 1
        self.visit(node.right)
        self.stack_depth -= 1

        if node.op == '=':
            self.emit("STORE 1"); self.emit("SWP g"); self.emit("STORE 0")
            self.emit("LOAD 0"); self.emit("SWP b"); self.emit("LOAD 1")
            self.emit("SUB b"); self.emit("STORE 2")
            self.emit("LOAD 1"); self.emit("SWP b"); self.emit("LOAD 0")
            self.emit("SUB b"); self.emit("SWP b"); self.emit("LOAD 2"); self.emit("ADD b")

            if jump_if_true:
                self.emit(f"JZERO {label}")
            else:
                self.emit(f"JPOS {label}")

        elif node.op == '!=':
            self.emit("STORE 1"); self.emit("SWP g"); self.emit("STORE 0")
            self.emit("LOAD 0"); self.emit("SWP b"); self.emit("LOAD 1")
            self.emit("SUB b"); self.emit("STORE 2")
            self.emit("LOAD 1"); self.emit("SWP b"); self.emit("LOAD 0")
            self.emit("SUB b"); self.emit("SWP b"); self.emit("LOAD 2"); self.emit("ADD b")

            if jump_if_true:
                self.emit(f"JPOS {label}")
            else:
                self.emit(f"JZERO {label}")

        elif node.op == '<':
            self.emit("SUB g")
            if jump_if_true:
                self.emit(f"JPOS {label}")
            else:
                self.emit(f"JZERO {label}")

        elif node.op == '>':
            self.emit("SWP g"); self.emit("SUB g")
            if jump_if_true:
                self.emit(f"JPOS {label}")
            else:
                self.emit(f"JZERO {label}")

        elif node.op == '<=':
            self.emit("SWP g"); self.emit("SUB g")
            if jump_if_true:
                self.emit(f"JZERO {label}")
            else:
                self.emit(f"JPOS {label}")

        elif node.op == '>=':
            self.emit("SUB g")
            if jump_if_true:
                self.emit(f"JZERO {label}")
            else:
                self.emit(f"JPOS {label}")