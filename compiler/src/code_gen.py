from ast_nodes import *

class CodeGenerator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.code = []
        self.current_scope = 'GLOBAL'
        # Registers: a, b, c, d, e, f, g, h
        # a is accumulator
        # b - f: General purpose / Multiplier / Divisor
        # g: Expression stack optimization
        # h: Return Address Stack Pointer (SP)
        self.reg_stack = ['g'] 
        self.stack_depth = 0
        self.stack_depth = 0
        self.mem_spill_start = 1000 # Move spill far away to detect collisions
        
        # Initialize SP (h) to a high memory address
        self.sp_start = self.symbol_table.memory_counter + 1000
        
    def emit(self, instr):
        if '\n' in instr:
            raise ValueError(f"Instruction contains newline: {repr(instr)}")
        self.code.append(instr)

    def get_code(self):
        self.resolve_labels()
        return '\n'.join(self.code)

    def resolve_labels(self):
        # 1. Find all labels and their line numbers
        labels = {}
        clean_code = []
        line_counter = 0
        
        for line in self.code:
            line = line.strip()
            if line.endswith(':'):
                label_name = line[:-1]
                labels[label_name] = line_counter
            else:
                clean_code.append(line)
                line_counter += 1
        
        
        # 2. Replace labels with line numbers in JUMP instructions
        final_code = []
        for i, line in enumerate(clean_code):
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

    def generate(self, ast):
        # Initialize SP
        self.generate_constant(self.sp_start)
        self.emit("SWP h") # h = SP
        
        self.emit("JUMP MAIN")
        
        for proc in ast.procedures:
            self.generate_procedure(proc)
            
        self.emit("MAIN:")
        self.generate_block(ast.main)
        self.emit("HALT")

    def generate_procedure(self, node):
        self.current_scope = node.name
        self.symbol_table.enter_scope(node.name)
        
        self.emit(f"PROC_{node.name}:")
        
        # Save Return Address (a) to Stack
        # Mem[SP] = a
        # h is SP
        # a has RetAddr (from CALL)
        # We need RSTORE h (stores a to Mem[h])
        self.emit("RSTORE h")
        
        # Increment SP
        self.emit("INC h")
        
        self.generate_block(node)
        
        # Restore Return Address
        # Decrement SP
        self.emit("DEC h")
        
        # Load RetAddr from Mem[SP]
        # RLOAD h (loads Mem[h] to a)
        self.emit("RLOAD h")
        
        # Jump to RetAddr
        # RTRN sets PC to a
        self.emit("RTRN")
        
        self.current_scope = 'GLOBAL'
        self.symbol_table.exit_scope()

    def generate_block(self, node):
        for cmd in node.commands:
            self.visit(cmd)

    def visit(self, node):
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No code gen for {node.__class__.__name__}")

    def visit_Assign(self, node):
        # If it's an array assignment: tab[i] := expr
        if node.identifier.index is not None:
            # 1. Calculate address
            sym = self.symbol_table.get(node.identifier.name)
            
            if isinstance(node.identifier.index, int):
                self.generate_constant(node.identifier.index)
            elif isinstance(node.identifier.index, str):
                idx_sym = self.symbol_table.get(node.identifier.index)
                
                # Check if index variable is a parameter (pointer or value)
                if self.current_scope != 'GLOBAL':
                    current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                    idx_param_info = next((arg for arg in current_proc_info['args'] if arg[1] == idx_sym.name), None)
                    
                    if idx_param_info:
                        if idx_param_info[0] == 'CONST':
                            # Passed by value. Just load it.
                            self.emit(f"LOAD {idx_sym.address}")
                        else:
                            # Passed by reference. Load pointer, then value.
                            self.emit(f"LOAD {idx_sym.address}")
                            self.emit("SWP b")
                            self.emit("RLOAD b")
                    else:
                        self.emit(f"LOAD {idx_sym.address}")
                else:
                    self.emit(f"LOAD {idx_sym.address}")
            else:
                self.generate_constant(node.identifier.index)
            
            # a has index.
            if sym.array_range is not None:
                # Declared array
                start = sym.array_range[0]
                # index in a
                loc_idx = self.mem_spill_start + self.stack_depth
                self.emit(f"STORE {loc_idx}") # Save index
                self.generate_constant(start) # start in a
                self.emit("SWP b") # start in b
                self.emit(f"LOAD {loc_idx}") # index in a
                self.emit("SUB b") # index - start
                
                # Add base address
                # offset in a
                self.emit("SWP b") # offset in b
                self.generate_constant(sym.address) # base in a
                self.emit("ADD b") # base + offset
            else:
                # Parameter array
                # index in a
                self.emit("SWP b") # index in b
                self.emit(f"LOAD {sym.address}") # virtual_base in a
                self.emit("ADD b") # virtual_base + index
                
            # Address is in a. Store in temp.
            loc = self.mem_spill_start + self.stack_depth
            self.emit(f"STORE {loc}")
            
            # 2. Calculate expression -> a
            self.stack_depth += 1
            self.visit(node.expression)
            self.stack_depth -= 1
            
            # 3. Store a to address in loc
            # We need RSTORE b (stores a to address in b)
            self.emit("SWP b") # b = value
            self.emit(f"LOAD {loc}") # a = address
            self.emit("SWP b") # a = value, b = address
            self.emit("RSTORE b")
            
        else:
            # Simple variable
            self.visit(node.expression)
            sym = self.symbol_table.get(node.identifier.name)
            
            if sym.scope != 'GLOBAL' and sym.type in ['VAR', 'ARRAY', 'OUT']:
                # Check if param
                current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                param_info = next((arg for arg in current_proc_info['args'] if arg[1] == sym.name), None)
                
                if param_info:
                    if param_info[0] == 'CONST':
                        # Cannot assign to CONST parameter!
                        # Semantic analysis should catch this, but code gen should handle it or fail.
                        # Assuming semantic analysis passed, this shouldn't happen for CONST.
                        # But if it's a local variable shadowing a param? No, shadowing not allowed.
                        pass
                    else:
                        # Indirect store
                        self.emit("SWP b") # b = value
                        self.emit(f"LOAD {sym.address}") # a = pointer
                        self.emit("SWP b") # a = value, b = pointer
                        self.emit("RSTORE b")
                        return

            self.emit(f"STORE {sym.address}")

    def visit_Identifier(self, node):
        sym = self.symbol_table.get(node.name)
        
        # Calculate address
        if node.index:
            # Array access: tab[index]
            # Address = base + index - start
            # 1. Load index -> a
            if isinstance(node.index, int):
                self.generate_constant(node.index)
            else:
                # Index is a variable name (string)
                if isinstance(node.index, str):
                    # Load value of index variable
                    idx_sym = self.symbol_table.get(node.index)
                    
                    # Check if index variable is a parameter (pointer or value)
                    if self.current_scope != 'GLOBAL':
                        current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                        idx_param_info = next((arg for arg in current_proc_info['args'] if arg[1] == idx_sym.name), None)
                        
                        if idx_param_info:
                            if idx_param_info[0] == 'CONST':
                                # Passed by value. Just load it.
                                self.emit(f"LOAD {idx_sym.address}")
                            else:
                                # Passed by reference. Load pointer, then value.
                                self.emit(f"LOAD {idx_sym.address}")
                                self.emit("SWP b")
                                self.emit("RLOAD b")
                        else:
                            self.emit(f"LOAD {idx_sym.address}")
                    else:
                        self.emit(f"LOAD {idx_sym.address}")
                else:
                    self.generate_constant(node.index)
            
            # a has index value.
            
            if sym.array_range is not None:
                # Declared array: Address = base + index - start
                start = sym.array_range[0]
                # index in a
                loc_idx = self.mem_spill_start + self.stack_depth
                self.emit(f"STORE {loc_idx}") # Save index
                self.generate_constant(start) # start in a
                self.emit("SWP b") # start in b
                self.emit(f"LOAD {loc_idx}") # index in a
                self.emit("SUB b") # index - start
                
                # Add base address
                # offset in a
                self.emit("SWP b") # offset in b
                self.generate_constant(sym.address) # base in a
                self.emit("ADD b") # base + offset
            else:
                # Array parameter: Address = virtual_base + index
                # sym.address holds the virtual_base pointer
                # index in a
                self.emit("SWP b") # index in b
                self.emit(f"LOAD {sym.address}") # Load virtual_base in a
                self.emit("ADD b") # virtual_base + index
            
            # Now a has the effective address.
            # Load value from this address.
            # Use g as scratch if needed, but here we use b for RLOAD
            self.emit("SWP b")
            self.emit("RLOAD b")
            
        else:
            # Simple variable
            # Check if it's a parameter
            if self.current_scope != 'GLOBAL':
                current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                param_info = next((arg for arg in current_proc_info['args'] if arg[1] == sym.name), None)
                
                if param_info:
                    if param_info[0] == 'CONST':
                        # Passed by value. Just load it.
                        self.emit(f"LOAD {sym.address}")
                    else:
                        # Passed by reference. Load pointer, then value.
                        self.emit(f"LOAD {sym.address}") # Load the pointer
                        self.emit("SWP b")
                        self.emit("RLOAD b") # Load value pointed to
                else:
                    self.emit(f"LOAD {sym.address}")
            else:
                self.emit(f"LOAD {sym.address}")

    def visit_Number(self, node):
        self.generate_constant(node.value)

    def generate_constant(self, value):
        self.emit("RST a") # a = 0
        if value == 0:
            return
        
        # Binary representation
        bin_str = bin(value)[2:]
        for bit in bin_str:
            self.emit("SHL a") # a *= 2
            if bit == '1':
                self.emit("INC a")

    def is_power_of_two(self, n):
        return n > 0 and (n & (n - 1)) == 0

    def get_power_of_two(self, n):
        return n.bit_length() - 1

    def visit_BinaryOp(self, node):
        # Constant Folding
        if isinstance(node.left, Number) and isinstance(node.right, Number):
            val = 0
            if node.op == '+': val = node.left.value + node.right.value
            elif node.op == '-': val = max(0, node.left.value - node.right.value)
            elif node.op == '*': val = node.left.value * node.right.value
            elif node.op == '/': 
                if node.right.value != 0: val = node.left.value // node.right.value
                else: val = 0
            elif node.op == '%':
                if node.right.value != 0: val = node.left.value % node.right.value
                else: val = 0
            self.generate_constant(val)
            return

        # Strength Reduction for *, /, %
        if node.op == '*':
            if isinstance(node.right, Number) and self.is_power_of_two(node.right.value):
                self.visit(node.left)
                power = self.get_power_of_two(node.right.value)
                for _ in range(power): self.emit("SHL a")
                return
            if isinstance(node.left, Number) and self.is_power_of_two(node.left.value):
                self.visit(node.right)
                power = self.get_power_of_two(node.left.value)
                for _ in range(power): self.emit("SHL a")
                return
        
        elif node.op == '/':
            if isinstance(node.right, Number) and self.is_power_of_two(node.right.value):
                self.visit(node.left)
                power = self.get_power_of_two(node.right.value)
                for _ in range(power): self.emit("SHR a")
                return

        elif node.op == '%':
            if isinstance(node.right, Number) and self.is_power_of_two(node.right.value):
                self.visit(node.left)
                power = self.get_power_of_two(node.right.value)
                
                loc = self.mem_spill_start + self.stack_depth
                self.emit(f"STORE {loc}")
                
                for _ in range(power): self.emit("SHR a")
                for _ in range(power): self.emit("SHL a")
                
                self.emit("SWP b")
                self.emit(f"LOAD {loc}")
                self.emit("SUB b")
                return

        # Optimized BinaryOp using registers g, h (not h actually, stack pointer is h)
        # Using register 'g' as temp
        
        if node.op in ['+', '-']:
            self.visit(node.left)
            
            if self.stack_depth < len(self.reg_stack):
                # Use register stack
                reg = self.reg_stack[self.stack_depth]
                self.emit(f"SWP {reg}") # Save left to reg
                
                self.stack_depth += 1
                self.visit(node.right)
                self.stack_depth -= 1
                
                # Perform Op
                # Left is in reg, Right is in a
                if node.op == '+':
                    self.emit(f"ADD {reg}") # a = a + reg (commutative)
                else: # '-'
                    # a = left - right
                    # left is in reg, right is in a
                    # We want reg - a
                    self.emit(f"SWP {reg}") # a = left, reg = right
                    self.emit(f"SUB {reg}") # a = left - right
            else:
                # Spill to memory
                loc = self.mem_spill_start + self.stack_depth
                self.emit(f"STORE {loc}")
                
                self.stack_depth += 1
                self.visit(node.right)
                self.stack_depth -= 1
                
                # Perform Op
                # Left in Mem[loc], Right in a
                self.emit("SWP b") # Right in b
                self.emit(f"LOAD {loc}") # Left in a
                
                if node.op == '+':
                    self.emit("ADD b")
                else: # '-'
                    self.emit("SUB b")

        elif node.op in ['*', '/', '%']:
            # Complex ops use fixed memory 0 and 1
            
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
        # Inputs: Mem[0] (Multiplicand a), Mem[1] (Multiplier b)
        # Output: a
        # Registers:
        # b: Multiplier (b)
        # c: Multiplicand (a)
        # d: Result (res)
        # e: Temp for parity check
        
        # Load b -> b
        self.emit("LOAD 1")
        self.emit("SWP b")
        
        # Load a -> c
        self.emit("LOAD 0")
        self.emit("SWP c")
        
        # Init res (d) = 0
        self.emit("RST d")
        
        start_label = self.get_new_label("MULT_START")
        end_label = self.get_new_label("MULT_END")
        skip_add_label = self.get_new_label("MULT_SKIP_ADD")
        
        self.emit(f"{start_label}:")
        
        # Check if b (b) == 0
        self.emit("SWP b") # a = b
        self.emit(f"JZERO {end_label}")
        self.emit("SWP b") # Restore b
        
        # Check parity: (b / 2) * 2 == b?
        # Copy b to e
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SWP e") # e = b
        
        # Check parity of e
        self.emit("RST a")
        self.emit("ADD b")
        self.emit("SHR a")
        self.emit("SHL a")
        # Now a = (b >> 1) << 1.
        # Subtract from b (b)
        # Store cleared to temp (Mem[2]).
        self.emit("STORE 2")
        
        self.emit("LOAD 2")
        self.emit("SWP f") # f = cleared
        self.emit("RST a")
        self.emit("ADD b") # a = b
        self.emit("SUB f") # a = b - cleared
        
        # Now a is 1 (odd) or 0 (even).
        self.emit(f"JZERO {skip_add_label}")
        
        # Add a (c) to res (d)
        self.emit("SWP d") # a = res
        self.emit("ADD c") # a += a
        self.emit("SWP d") # res = a
        
        self.emit(f"{skip_add_label}:")
        
        # Double a (c)
        self.emit("SWP c")
        self.emit("SHL a")
        self.emit("SWP c")
        
        # Halve b (b)
        self.emit("SWP b")
        self.emit("SHR a")
        self.emit("SWP b")
        
        self.emit(f"JUMP {start_label}")
        
        self.emit(f"{end_label}:")
        # Result in d. Move to a.
        self.emit("SWP d")

    def visit_If(self, node):
        else_label = self.get_new_label("IF_ELSE")
        end_label = self.get_new_label("IF_END")
        
        self.visit(node.condition) # a has 1 (true) or 0 (false)
        self.emit(f"JZERO {else_label}")
        
        for cmd in node.then_commands:
            self.visit(cmd)
        self.emit(f"JUMP {end_label}")
        
        self.emit(f"{else_label}:")
        if node.else_commands:
            for cmd in node.else_commands:
                self.visit(cmd)
        
        self.emit(f"{end_label}:")

    def visit_While(self, node):
        start_label = self.get_new_label("WHILE_START")
        end_label = self.get_new_label("WHILE_END")
        
        self.emit(f"{start_label}:")
        self.visit(node.condition)
        self.emit(f"JZERO {end_label}")
        
        for cmd in node.commands:
            self.visit(cmd)
            
        self.emit(f"JUMP {start_label}")
        self.emit(f"{end_label}:")

    def visit_Repeat(self, node):
        start_label = self.get_new_label("REPEAT_START")
        
        self.emit(f"{start_label}:")
        
        for cmd in node.commands:
            self.visit(cmd)
            
        self.visit(node.condition) # Wynik warunku w rejestrze 'a'
        
        # Pętla REPEAT-UNTIL kończy się, gdy warunek jest prawdziwy.
        # Jeśli warunek jest fałszywy (0), skaczemy na początek.
        self.emit(f"JZERO {start_label}")

    def visit_For(self, node):
        self.visit(node.start_expr)
        sym = self.symbol_table.get(node.iterator)
        self.emit(f"STORE {sym.address}")
        
        limit_address = self.symbol_table.memory_counter
        self.symbol_table.memory_counter += 1
        
        self.visit(node.end_expr)
        self.emit(f"STORE {limit_address}")
        
        start_label = self.get_new_label("FOR_START")
        end_label = self.get_new_label("FOR_END")
        
        self.emit(f"{start_label}:")
        
        # Check condition: i <= limit (TO) or i >= limit (DOWNTO)
        # We need to compute a - b, checking saturating arithmetic.
        
        # 1. Load limit -> 1
        self.emit(f"LOAD {limit_address}")
        self.emit("STORE 1")
        
        # 2. Load iterator -> 0
        self.emit(f"LOAD {sym.address}")
        self.emit("STORE 0")
        
        # 3. Perform comparison subtraction
        if not node.down_to: # TO: i <= limit <=> i - limit <= 0?
            # With saturating sub (monus):
            # i - limit == 0 if i <= limit.
            # So if i - limit == 0, we continue.
            # If i - limit > 0, we stop.
            # JPOS jumps if > 0.
            
            # Load i -> a
            self.emit("LOAD 0")
            # Load limit -> a, swap to b
            self.emit("SWP b")
            self.emit("LOAD 1") # limit in a, i in b
            self.emit("SWP b")  # i in a, limit in b
            
            self.emit("SUB b")  # i - limit
            self.emit(f"JPOS {end_label}")
            
        else: # DOWNTO: i >= limit <=> limit - i <= 0?
            # limit - i == 0 if limit <= i.
            # If limit - i > 0 (limit > i), we stop.
            
            # Load limit -> a
            self.emit("LOAD 1")
            # Load i -> a, swap to b
            self.emit("SWP b")
            self.emit("LOAD 0") # i in a, limit in b
            self.emit("SWP b")  # limit in a, i in b
            
            self.emit("SUB b")  # limit - i
            self.emit(f"JPOS {end_label}")
            
        for cmd in node.commands:
            self.visit(cmd)
            
        # Update iterator
        self.emit(f"LOAD {sym.address}")
        if not node.down_to:
            self.emit("INC a")
        else:
            self.emit("DEC a")
        self.emit(f"STORE {sym.address}")
        
        self.emit(f"JUMP {start_label}")
        self.emit(f"{end_label}:")

    def visit_Condition(self, node):
        # Evaluate condition -> a = 1 (true) or 0 (false)
        # Optimize using registers g
        
        self.visit(node.left)
        
        # Use g to store left operand
        self.emit("SWP g")
        
        self.stack_depth += 1
        self.visit(node.right)
        self.stack_depth -= 1
        # Right in a, Left in g
        
        # EQ: a == b <=> a-b == 0 AND b-a == 0

        
        if node.op == '<':
            # b - a > 0
            # Right (a) - Left (g)
            self.emit("SUB g")
            self.emit_normalize_boolean()
            return

        elif node.op == '>':
            # a - b > 0
            # Left (g) - Right (a)
            self.emit("SWP g") # a=Left, g=Right
            self.emit("SUB g")
            self.emit_normalize_boolean()
            return
            
        elif node.op == '<=':
            # a <= b <=> not (a > b) <=> not (a - b > 0)
            self.emit("SWP g")
            self.emit("SUB g")
            self.emit_normalize_boolean()
            self.emit_invert_boolean_val()
            return
            
        elif node.op == '>=':
            # a >= b <=> not (a < b) <=> not (b - a > 0)
            # Right - Left
            self.emit("SUB g")
            self.emit_normalize_boolean()
            self.emit_invert_boolean_val()
            return

        # Fallback for =, !=
        if node.op == '=':
            # Left in g, Right in a
            self.emit("STORE 1") # Right -> 1
            self.emit("SWP g") # Left -> a
            self.emit("STORE 0") # Left -> 0
            
            # a-b
            self.emit("LOAD 0"); self.emit("SWP b"); self.emit("LOAD 1"); self.emit("SUB b"); self.emit("STORE 2")
            # b-a
            self.emit("LOAD 1"); self.emit("SWP b"); self.emit("LOAD 0"); self.emit("SUB b"); self.emit("SWP b"); self.emit("LOAD 2"); self.emit("ADD b")
            
            self.emit_invert_boolean()
            
        elif node.op == '!=':
            self.emit("STORE 1")
            self.emit("SWP g")
            self.emit("STORE 0")
            
            # a-b
            self.emit("LOAD 0"); self.emit("SWP b"); self.emit("LOAD 1"); self.emit("SUB b"); self.emit("STORE 2")
            # b-a
            self.emit("LOAD 1"); self.emit("SWP b"); self.emit("LOAD 0"); self.emit("SUB b"); self.emit("SWP b"); self.emit("LOAD 2"); self.emit("ADD b")
            
            self.emit_normalize_boolean()

    def emit_invert_boolean(self):
        # If a == 0 -> a = 1
        # If a > 0  -> a = 0
        lbl_true = self.get_new_label("BOOL_TRUE")
        lbl_end = self.get_new_label("BOOL_END")
        self.emit(f"JZERO {lbl_true}")
        self.emit("RST a") # 0
        self.emit(f"JUMP {lbl_end}")
        self.emit(f"{lbl_true}:")
        self.emit("RST a"); self.emit("INC a") # 1
        self.emit(f"{lbl_end}:")

    def emit_normalize_boolean(self):
        # If a > 0 -> a = 1
        # If a == 0 -> a = 0
        lbl_true = self.get_new_label("NORM_TRUE")
        lbl_end = self.get_new_label("NORM_END")
        self.emit(f"JPOS {lbl_true}")
        self.emit("RST a")
        self.emit(f"JUMP {lbl_end}")
        self.emit(f"{lbl_true}:")
        self.emit("RST a"); self.emit("INC a")
        self.emit(f"{lbl_end}:")
        
    def emit_invert_boolean_val(self):
         # Assumes a is 0 or 1.
         # 0 -> 1, 1 -> 0
         # 1 - a
         self.emit("STORE 2")
         self.emit("RST a"); self.emit("INC a") # 1
         # a=1. Want 1 - val.
         self.emit("SWP b"); self.emit("LOAD 2"); self.emit("SWP b"); self.emit("SUB b") 

    def generate_division(self):
        # Inputs: Mem[0] (Dividend A), Mem[1] (Divisor B)
        # Output: a (Quotient)
        
        # b: Divisor (B)
        # c: Dividend (A) -> Remainder (R)
        # d: Quotient (Q)
        # e: Temp D (shifted divisor)
        # f: Shift count (power of 2)
        
        # Load B -> b
        self.emit("LOAD 1"); self.emit("SWP b")
        
        # Load A -> c
        self.emit("LOAD 0"); self.emit("SWP c")
        
        # Check B == 0
        self.emit("RST a"); self.emit("ADD b")
        lbl_zero = self.get_new_label("DIV_ZERO")
        self.emit(f"JZERO {lbl_zero}")
        
        # Init Q = 0 -> d
        self.emit("RST d")
        
        # Init Shift Count (Power) = 1 -> f
        self.emit("RST a"); self.emit("INC a"); self.emit("SWP f")
        
        # Init Shifted Divisor D = B -> e
        self.emit("RST a"); self.emit("ADD b"); self.emit("SWP e")
        
        # Align D to A (Shift Left Loop)
        lbl_align = self.get_new_label("DIV_ALIGN")
        lbl_align_end = self.get_new_label("DIV_ALIGN_END")
        
        self.emit(f"{lbl_align}:")
        # Check if D > A (e > c)
        # e - c > 0?
        self.emit("RST a"); self.emit("ADD e") # a = D
        self.emit("SUB c") # a = D - A
        self.emit(f"JPOS {lbl_align_end}") # If D > A, stop shifting
        
        # Shift D left
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHL a"); self.emit("SWP e")
        
        # Shift Power left
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHL a"); self.emit("SWP f")
        
        self.emit(f"JUMP {lbl_align}")
        self.emit(f"{lbl_align_end}:")
        
        # Now D > A. We went one step too far.
        # Shift back right once.
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHR a"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHR a"); self.emit("SWP f")
        
        # Main Loop (Subtract and Shift Right)
        lbl_loop = self.get_new_label("DIV_LOOP")
        lbl_end = self.get_new_label("DIV_END")
        
        self.emit(f"{lbl_loop}:")
        # Check if Power (f) == 0 -> End
        self.emit("RST a"); self.emit("ADD f")
        self.emit(f"JZERO {lbl_end}")
        
        # Check if R >= D (c >= e)
        # D - R <= 0? Or R - D >= 0?
        # Use SUB: D - R. If > 0, then D > R (skip). If 0, then D <= R (subtract).
        self.emit("RST a"); self.emit("ADD e") # D
        self.emit("SUB c") # D - R
        lbl_skip = self.get_new_label("DIV_SKIP")
        self.emit(f"JPOS {lbl_skip}")
        
        # R = R - D
        self.emit("RST a"); self.emit("ADD c"); self.emit("SUB e"); self.emit("SWP c")
        
        # Q = Q + Power
        self.emit("RST a"); self.emit("ADD d"); self.emit("ADD f"); self.emit("SWP d")
        
        self.emit(f"{lbl_skip}:")
        
        # Shift D right
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHR a"); self.emit("SWP e")
        
        # Shift Power right
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHR a"); self.emit("SWP f")
        
        self.emit(f"JUMP {lbl_loop}")
        
        self.emit(f"{lbl_end}:")
        # Result Q in d -> a
        self.emit("RST a"); self.emit("ADD d")
        
        self.emit(f"{lbl_zero}:")

    def generate_modulo(self):
        # Inputs: Mem[0] (Dividend A), Mem[1] (Divisor B)
        # Output: a (Remainder)
        
        # b: Divisor (B)
        # c: Dividend (A) -> Remainder (R)
        # d: Quotient (Q)
        # e: Temp D (shifted divisor)
        # f: Shift count (power of 2)
        
        # Load B -> b
        self.emit("LOAD 1"); self.emit("SWP b")
        
        # Load A -> c
        self.emit("LOAD 0"); self.emit("SWP c")
        
        # Check B == 0
        self.emit("RST a"); self.emit("ADD b")
        lbl_zero = self.get_new_label("MOD_ZERO")
        self.emit(f"JZERO {lbl_zero}")
        
        # Init Q = 0 -> d
        self.emit("RST d")
        
        # Init Shift Count (Power) = 1 -> f
        self.emit("RST a"); self.emit("INC a"); self.emit("SWP f")
        
        # Init Shifted Divisor D = B -> e
        self.emit("RST a"); self.emit("ADD b"); self.emit("SWP e")
        
        # Align D to A (Shift Left Loop)
        lbl_align = self.get_new_label("MOD_ALIGN")
        lbl_align_end = self.get_new_label("MOD_ALIGN_END")
        
        self.emit(f"{lbl_align}:")
        # Check if D > A (e > c)
        self.emit("RST a"); self.emit("ADD e") # a = D
        self.emit("SUB c") # a = D - A
        self.emit(f"JPOS {lbl_align_end}") # If D > A, stop shifting
        
        # Shift D left
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHL a"); self.emit("SWP e")
        
        # Shift Power left
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHL a"); self.emit("SWP f")
        
        self.emit(f"JUMP {lbl_align}")
        self.emit(f"{lbl_align_end}:")
        
        # Now D > A. We went one step too far.
        # Shift back right once.
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHR a"); self.emit("SWP e")
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHR a"); self.emit("SWP f")
        
        # Main Loop (Subtract and Shift Right)
        lbl_loop = self.get_new_label("MOD_LOOP")
        lbl_end = self.get_new_label("MOD_END")
        
        self.emit(f"{lbl_loop}:")
        # Check if Power (f) == 0 -> End
        self.emit("RST a"); self.emit("ADD f")
        self.emit(f"JZERO {lbl_end}")
        
        # Check if R >= D (c >= e)
        self.emit("RST a"); self.emit("ADD e") # D
        self.emit("SUB c") # D - R
        lbl_skip = self.get_new_label("MOD_SKIP")
        self.emit(f"JPOS {lbl_skip}")
        
        # R = R - D
        self.emit("RST a"); self.emit("ADD c"); self.emit("SUB e"); self.emit("SWP c")
        
        self.emit(f"{lbl_skip}:")
        
        # Shift D right
        self.emit("RST a"); self.emit("ADD e"); self.emit("SHR a"); self.emit("SWP e")
        
        # Shift Power right
        self.emit("RST a"); self.emit("ADD f"); self.emit("SHR a"); self.emit("SWP f")
        
        self.emit(f"JUMP {lbl_loop}")
        
        self.emit(f"{lbl_end}:")
        # Result R in c -> a
        self.emit("RST a"); self.emit("ADD c")
        
        self.emit(f"{lbl_zero}:")

    def visit_ProcCall(self, node):
        # Args are passed by reference or value.
        
        proc_syms = self.symbol_table.get_all_in_scope(node.name)
        proc_info = self.symbol_table.get_procedure(node.name)
        args_info = proc_info['args'] 
        
        for i, arg_expr in enumerate(node.args):
            arg_sym = self.symbol_table.get(arg_expr)
            param_name = args_info[i][1]
            param_type = args_info[i][0]
            param_sym = proc_syms[param_name]
            
            if param_type == 'CONST': # Passed by Value (I)
                self.visit_Identifier(Identifier(arg_expr))
            else: # Passed by Reference (VAR, OUT, ARRAY)
                # Calculate address to pass
                
                if self.current_scope != 'GLOBAL':
                    # Check if arg_sym is a parameter of current scope
                    current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                    arg_param_info = next((arg for arg in current_proc_info['args'] if arg[1] == arg_sym.name), None)
                    
                    if arg_param_info:
                        # It's a parameter.
                        if arg_param_info[0] == 'CONST':
                            # It's a local value. Pass its address.
                            self.generate_constant(arg_sym.address)
                        else:
                            # It's a pointer. Load the value (which is the address).
                            self.emit(f"LOAD {arg_sym.address}")
                    else:
                        # It's a local variable. Load its address (constant).
                        self.generate_constant(arg_sym.address)
                else:
                    # Global variable. Load its address.
                    self.generate_constant(arg_sym.address)
                
                # If passing an ARRAY declared with range, adjust base.
                if arg_sym.type == 'ARRAY' and arg_sym.array_range is not None:
                    start_index = arg_sym.array_range[0]
                    # Use spill registers to allow recursion/nested calls without clobbering 0/1
                    loc_addr = self.mem_spill_start + self.stack_depth
                    loc_start = self.mem_spill_start + self.stack_depth + 1
                    
                    self.emit(f"STORE {loc_addr}") # Save address
                    self.generate_constant(start_index)
                    self.emit(f"STORE {loc_start}") # Save start_index
                    self.emit(f"LOAD {loc_addr}"); self.emit("SWP b"); self.emit(f"LOAD {loc_start}"); self.emit("SWP b"); self.emit("SUB b") # address - start_index
            
            # Store a (the address or value) into the parameter location of the callee
            self.emit(f"STORE {param_sym.address}")
            
        self.emit(f"CALL PROC_{node.name}")

    def get_new_label(self, prefix):
        if not hasattr(self, 'label_counter'):
            self.label_counter = 0
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def visit_Read(self, node):
        sym = self.symbol_table.get(node.identifier.name)
        
        if node.identifier.index is not None:
            # Array access: tab[i]
            # Calculate address into b
            
            if isinstance(node.identifier.index, int):
                self.generate_constant(node.identifier.index)
            elif isinstance(node.identifier.index, str):
                idx_sym = self.symbol_table.get(node.identifier.index)
                
                # Check if index variable is a parameter (pointer or value)
                if self.current_scope != 'GLOBAL':
                    current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                    idx_param_info = next((arg for arg in current_proc_info['args'] if arg[1] == idx_sym.name), None)
                    
                    if idx_param_info:
                        if idx_param_info[0] == 'CONST':
                            # Passed by value. Just load it.
                            self.emit(f"LOAD {idx_sym.address}")
                        else:
                            # Passed by reference. Load pointer, then value.
                            self.emit(f"LOAD {idx_sym.address}")
                            self.emit("SWP b")
                            self.emit("RLOAD b")
                    else:
                        self.emit(f"LOAD {idx_sym.address}")
                else:
                    self.emit(f"LOAD {idx_sym.address}")
            else:
                self.generate_constant(node.identifier.index)
            
            # a has index
            
            if sym.array_range is not None:
                # Declared array
                start = sym.array_range[0]
                self.emit("STORE 0") # Save index
                self.generate_constant(start)
                self.emit("SWP b")
                self.emit("LOAD 0")
                self.emit("SUB b") # index - start
                
                self.emit("SWP b")
                self.generate_constant(sym.address)
                self.emit("ADD b") # base + offset -> a
            else:
                # Parameter array
                self.emit("SWP b")
                self.emit(f"LOAD {sym.address}")
                self.emit("ADD b") # virtual_base + index -> a
                
            # Address is in a. Move to b.
            self.emit("SWP b")
            
            # READ
            self.emit("READ")
            
            # Store
            self.emit("RSTORE b")
            
        else:
            # Simple variable
            if sym.scope != 'GLOBAL' and sym.type in ['VAR', 'ARRAY', 'OUT']:
                # Check if param
                current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                param_info = next((arg for arg in current_proc_info['args'] if arg[1] == sym.name), None)
                
                if param_info:
                    if param_info[0] == 'CONST':
                        # Cannot read into CONST parameter!
                        pass
                    else:
                        # Pointer. Load address to b.
                        self.emit(f"LOAD {sym.address}")
                        self.emit("SWP b")
                        self.emit("READ")
                        self.emit("RSTORE b")
                        return

            # Normal variable
            self.emit("READ")
            self.emit(f"STORE {sym.address}")

    def visit_Write(self, node):
        # Evaluate expression to a
        self.visit(node.value)
        # WRITE prints a
        self.emit("WRITE")