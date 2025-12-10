from ast_nodes import *

class CodeGenerator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.code = []
        self.current_scope = 'GLOBAL'
        # Registers: a, b, c, d, e, f, g, h
        # r_a is accumulator
        # r_b - r_f: General purpose / Multiplier / Divisor
        # r_g: Expression stack optimization
        # r_h: Return Address Stack Pointer (SP)
        self.reg_stack = ['r_g']
        self.stack_depth = 0
        self.mem_spill_start = 2 # Locations 0 and 1 are used by MULT/DIV/Array
        
        # Initialize SP (r_h) to a high memory address
        # We assume memory_counter is the last used address.
        # We add a buffer for safety.
        self.sp_start = self.symbol_table.memory_counter + 1000
        
    def emit(self, instr):
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
        for line in clean_code:
            parts = line.split()
            if parts[0] in ['JUMP', 'JPOS', 'JZERO', 'CALL']:
                target = parts[1]
                if target in labels:
                    final_code.append(f"{parts[0]} {labels[target]}")
                else:
                    # Maybe it's already a number (unlikely in our gen) or external?
                    final_code.append(line)
            else:
                final_code.append(line)
                
        self.code = final_code

    def generate(self, ast):
        # Initialize SP
        self.generate_constant(self.sp_start)
        self.emit("SWP r_h") # r_h = SP
        
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
        
        # Save Return Address (r_a) to Stack
        # Mem[SP] = r_a
        # r_h is SP
        # r_a has RetAddr (from CALL)
        # We need RSTORE r_h (stores r_a to Mem[r_h])
        self.emit("RSTORE r_h")
        
        # Increment SP
        self.emit("INC r_h")
        
        self.generate_block(node)
        
        # Restore Return Address
        # Decrement SP
        self.emit("DEC r_h")
        
        # Load RetAddr from Mem[SP]
        # RLOAD r_h (loads Mem[r_h] to r_a)
        self.emit("RLOAD r_h")
        
        # Jump to RetAddr
        # RTRN jumps to address in r[0] (r_a)?
        # Wait, VM spec for RTRN: "lr = r[0]"
        # Yes, it sets PC to r[0].
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
                self.emit(f"LOAD {idx_sym.address}")
            else:
                self.generate_constant(node.identifier.index)
            
            # r_a has index.
            if sym.array_range is not None:
                # Declared array
                start = sym.array_range[0]
                # index in r_a
                self.emit("STORE 0") # Save index
                self.generate_constant(start) # start in r_a
                self.emit("SWP r_b") # start in r_b
                self.emit("LOAD 0") # index in r_a
                self.emit("SUB r_b") # index - start
                
                # Add base address
                # offset in r_a
                self.emit("SWP r_b") # offset in r_b
                self.generate_constant(sym.address) # base in r_a
                self.emit("ADD r_b") # base + offset
            else:
                # Parameter array
                # index in r_a
                self.emit("SWP r_b") # index in r_b
                self.emit(f"LOAD {sym.address}") # virtual_base in r_a
                self.emit("ADD r_b") # virtual_base + index
                
            # Address is in r_a. Store in temp.
            loc = self.mem_spill_start + self.stack_depth
            self.emit(f"STORE {loc}")
            
            # 2. Calculate expression -> r_a
            self.stack_depth += 1
            self.visit(node.expression)
            self.stack_depth -= 1
            
            # 3. Store r_a to address in loc
            # We need RSTORE r_b (stores r_a to address in r_b)
            self.emit("SWP r_b") # r_b = value
            self.emit(f"LOAD {loc}") # r_a = address
            self.emit("SWP r_b") # r_a = value, r_b = address
            self.emit("RSTORE r_b")
            
        else:
            # Simple variable
            self.visit(node.expression)
            sym = self.symbol_table.get(node.identifier.name)
            
            if sym.scope != 'GLOBAL' and sym.type in ['VAR', 'ARRAY']:
                # Check if param
                current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                is_param = any(arg[1] == sym.name for arg in current_proc_info['args'])
                if is_param:
                    # Indirect store
                    self.emit("SWP r_b") # r_b = value
                    self.emit(f"LOAD {sym.address}") # r_a = pointer
                    self.emit("SWP r_b") # r_a = value, r_b = pointer
                    self.emit("RSTORE r_b")
                    return

            self.emit(f"STORE {sym.address}")

    def visit_Identifier(self, node):
        sym = self.symbol_table.get(node.name)
        
        # Calculate address
        if node.index:
            # Array access: tab[index]
            # Address = base + index - start
            # 1. Load index -> r_a
            if isinstance(node.index, int):
                self.generate_constant(node.index)
            else:
                # Index is a variable name (string)
                if isinstance(node.index, str):
                    # Load value of index variable
                    idx_sym = self.symbol_table.get(node.index)
                    self.emit(f"LOAD {idx_sym.address}")
                else:
                    self.generate_constant(node.index)
            
            # r_a has index value.
            
            if sym.array_range is not None:
                # Declared array: Address = base + index - start
                start = sym.array_range[0]
                # index in r_a
                self.emit("STORE 0") # Save index
                self.generate_constant(start) # start in r_a
                self.emit("SWP r_b") # start in r_b
                self.emit("LOAD 0") # index in r_a
                self.emit("SUB r_b") # index - start
                
                # Add base address
                # offset in r_a
                self.emit("SWP r_b") # offset in r_b
                self.generate_constant(sym.address) # base in r_a
                self.emit("ADD r_b") # base + offset
            else:
                # Array parameter: Address = virtual_base + index
                # sym.address holds the virtual_base pointer
                # index in r_a
                self.emit("SWP r_b") # index in r_b
                self.emit(f"LOAD {sym.address}") # Load virtual_base in r_a
                self.emit("ADD r_b") # virtual_base + index
            
            # Now r_a has the effective address.
            # Load value from this address.
            # Use r_g as scratch if needed, but here we use r_b for RLOAD
            # Note: visit_Identifier is atomic, but we must ensure we don't clobber
            # registers if we are inside an optimized expression.
            # However, RLOAD takes a register. We'll use r_b.
            # If visit_Identifier is called inside visit_BinaryOp optimized path,
            # r_b is NOT used by the optimization (it uses r_g, r_h).
            # So using r_b here is safe!
            self.emit("SWP r_b")
            self.emit("RLOAD r_b")
            
        else:
            # Simple variable
            # Check if it's a parameter (pointer)
            if self.current_scope != 'GLOBAL':
                current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                is_param = any(arg[1] == sym.name for arg in current_proc_info['args'])
                
                if is_param:
                    # It's a pointer.
                    self.emit(f"LOAD {sym.address}") # Load the pointer
                    self.emit("SWP r_b")
                    self.emit("RLOAD r_b") # Load value pointed to
                else:
                    self.emit(f"LOAD {sym.address}")
            else:
                self.emit(f"LOAD {sym.address}")

    def visit_Number(self, node):
        # Load number to r_a
        # Since we only have INC/DEC/ADD/SUB, loading a large constant is hard?
        # Spec says: "Liczby naturalne... 64-bitowe".
        # VM instructions: "SET r_x val"? No SET instruction listed in report summary.
        # Report says: "Komunikacja z pamięcią: LOAD, STORE... Arytmetyka: ADD, SUB, INC, DEC...".
        # Wait, how do we load a constant?
        # Usually a VM has a way to load immediate.
        # If not, we have to generate it? That would be insane for 64-bit.
        # Let's check the spec (labor4.pdf) or assume there is a SET/LOADI.
        # The report doesn't mention SET.
        # But it says "SUB (odejmowanie z nasyceniem do 0)".
        # Maybe `SUB r_a r_a` clears it. Then `INC`?
        # If the VM supports `SUB r_a r_a` (zero), then we can build numbers?
        # That's too slow.
        # There MUST be a way to generate constants.
        # Maybe the compiler puts constants in memory at the end and loads them?
        # Or `SET` exists but wasn't listed in the summary table?
        # "Zestaw instrukcji (ISA) jest zredukowany...".
        # Let's assume we can generate constants by writing them to memory at the end of code?
        # Or maybe the VM allows `ADD r_a value`?
        # "ADD (dodawanie)" - usually register-register or register-memory?
        # Report says: "ADD (dodawanie)... Koszt: 5 cykli".
        # It doesn't specify operands.
        # Usually `ADD 5` adds value at address 5 to r_a.
        # If so, we can't add immediate.
        
        # CRITICAL: How to load constants?
        # "SUB r_a r_a" -> 0.
        # "INC r_a" -> 1.
        # "ADD r_a r_a" -> 2x (shift left).
        # We can build any number in log time using double-and-add.
        # 1. r_a = 0
        # 2. For each bit of N from MSB:
        #    r_a = r_a + r_a (SHL)
        #    if bit is 1: INC r_a
        
        # Yes, this is the standard way on such restricted machines.
        # I will implement `generate_constant(value)`.
        
        self.generate_constant(node.value)

    def generate_constant(self, value):
        self.emit("RST r_a") # r_a = 0
        if value == 0:
            return
        
        # Binary representation
        bin_str = bin(value)[2:]
        for bit in bin_str:
            self.emit("SHL r_a") # r_a *= 2
            if bit == '1':
                self.emit("INC r_a")

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
                for _ in range(power): self.emit("SHL r_a")
                return
            if isinstance(node.left, Number) and self.is_power_of_two(node.left.value):
                self.visit(node.right)
                power = self.get_power_of_two(node.left.value)
                for _ in range(power): self.emit("SHL r_a")
                return
        
        elif node.op == '/':
            if isinstance(node.right, Number) and self.is_power_of_two(node.right.value):
                self.visit(node.left)
                power = self.get_power_of_two(node.right.value)
                for _ in range(power): self.emit("SHR r_a")
                return

        elif node.op == '%':
            if isinstance(node.right, Number) and self.is_power_of_two(node.right.value):
                self.visit(node.left)
                power = self.get_power_of_two(node.right.value)
                
                loc = self.mem_spill_start + self.stack_depth
                self.emit(f"STORE {loc}")
                
                for _ in range(power): self.emit("SHR r_a")
                for _ in range(power): self.emit("SHL r_a")
                
                self.emit("SWP r_b")
                self.emit(f"LOAD {loc}")
                self.emit("SUB r_b")
                return

        # Optimized BinaryOp using registers r_g, r_h
        
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
                # Left is in reg, Right is in r_a
                if node.op == '+':
                    self.emit(f"ADD {reg}") # r_a = r_a + reg (commutative)
                else: # '-'
                    # r_a = left - right
                    # left is in reg, right is in r_a
                    # We want reg - r_a
                    self.emit(f"SWP {reg}") # r_a = left, reg = right
                    self.emit(f"SUB {reg}") # r_a = left - right
            else:
                # Spill to memory
                loc = self.mem_spill_start + (self.stack_depth - len(self.reg_stack))
                self.emit(f"STORE {loc}")
                
                self.stack_depth += 1
                self.visit(node.right)
                self.stack_depth -= 1
                
                # Perform Op
                # Left in Mem[loc], Right in r_a
                self.emit("SWP r_b") # Right in r_b
                self.emit(f"LOAD {loc}") # Left in r_a
                
                if node.op == '+':
                    self.emit("ADD r_b")
                else: # '-'
                    self.emit("SUB r_b")

        elif node.op in ['*', '/', '%']:
            # Complex ops use fixed memory 0 and 1 and clobber r_b...r_f
            # We must ensure we don't rely on r_b...r_f being preserved.
            # Our optimization uses r_g, r_h, so it is safe.
            
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
        # Output: r_a
        # Registers:
        # r_b: Multiplier (b)
        # r_c: Multiplicand (a)
        # r_d: Result (res)
        # r_e: Temp for parity check
        
        # Load b -> r_b
        self.emit("LOAD 1")
        self.emit("SWP r_b")
        
        # Load a -> r_c
        self.emit("LOAD 0")
        self.emit("SWP r_c")
        
        # Init res (r_d) = 0
        self.emit("RST r_d")
        
        start_label = self.get_new_label("MULT_START")
        end_label = self.get_new_label("MULT_END")
        skip_add_label = self.get_new_label("MULT_SKIP_ADD")
        
        self.emit(f"{start_label}:")
        
        # Check if b (r_b) == 0
        self.emit("SWP r_b") # r_a = b
        self.emit(f"JZERO {end_label}")
        self.emit("SWP r_b") # Restore b
        
        # Check parity: (b / 2) * 2 == b?
        # Copy b to r_e
        self.emit("RST r_a")
        self.emit("ADD r_b")
        self.emit("SWP r_e") # r_e = b
        
        # Check parity of r_e
        self.emit("RST r_a")
        self.emit("ADD r_b")
        self.emit("SHR r_a")
        self.emit("SHL r_a")
        # Now r_a = (b >> 1) << 1.
        # Subtract from b (r_b)
        # We want b - cleared.
        # Store cleared to temp (Mem[2]).
        self.emit("STORE 2")
        
        # Load b
        self.emit("RST r_a")
        self.emit("ADD r_b")
        
        # Subtract cleared
        self.emit("SWP r_b") # r_b = b (Wait, r_b was b)
        # r_a = b.
        # We want r_a - Mem[2].
        # SWP r_b -> r_b = b. r_a = garbage.
        # LOAD 2 -> r_a = cleared.
        # SUB r_b -> cleared - b. WRONG.
        
        # We want b - cleared.
        # r_a = b.
        # SWP r_b -> r_b = b.
        # LOAD 2 -> r_a = cleared.
        # We want r_b - r_a.
        # But SUB is r_a -= r_x.
        # So we need r_a = b, r_x = cleared.
        # r_a = b (from ADD r_b above).
        # We need cleared in a register.
        # We can use r_e (it has b, but we can overwrite it if we don't need it yet? No we need it).
        # Use r_f as temp?
        # Or just LOAD 2 into r_f?
        # LOAD 2 -> r_a. SWP r_f -> r_f = cleared.
        # RST r_a. ADD r_b -> r_a = b.
        # SUB r_f -> b - cleared.
        
        self.emit("LOAD 2")
        self.emit("SWP r_f") # r_f = cleared
        self.emit("RST r_a")
        self.emit("ADD r_b") # r_a = b
        self.emit("SUB r_f") # r_a = b - cleared
        
        # Now r_a is 1 (odd) or 0 (even).
        self.emit(f"JZERO {skip_add_label}")
        
        # Add a (r_c) to res (r_d)
        self.emit("SWP r_d") # r_a = res
        self.emit("ADD r_c") # r_a += a
        self.emit("SWP r_d") # res = r_a
        
        self.emit(f"{skip_add_label}:")
        
        # Double a (r_c)
        self.emit("SWP r_c")
        self.emit("SHL r_a")
        self.emit("SWP r_c")
        
        # Halve b (r_b)
        self.emit("SWP r_b")
        self.emit("SHR r_a")
        self.emit("SWP r_b")
        
        self.emit(f"JUMP {start_label}")
        
        self.emit(f"{end_label}:")
        # Result in r_d. Move to r_a.
        self.emit("SWP r_d")

    def visit_If(self, node):
        else_label = self.get_new_label("IF_ELSE")
        end_label = self.get_new_label("IF_END")
        
        self.visit(node.condition) # r_a has 1 (true) or 0 (false)
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

    def visit_For(self, node):
        # FOR i FROM start TO end DO ...
        # 1. Init iterator
        self.visit(node.start_expr)
        sym = self.symbol_table.get(node.iterator)
        self.emit(f"STORE {sym.address}")
        
        # 2. Calculate limit and store in temp?
        # Spec: "liczba iteracji jest ustalana na początku".
        # So we should calc end_expr ONCE and store it.
        # We need a temp variable for limit.
        # Since we don't have temp allocation in symbol table easily,
        # we can use a reserved memory area or just allocate a new temp symbol?
        # Or use a fixed scratchpad location if we don't nest loops too deep?
        # Nested loops are possible.
        # We should allocate a temp variable in symbol table.
        # But symbol table is already built.
        # We can use the scratchpad (0-19) but we need to manage it.
        # Or just assume we have enough registers? No, only 8.
        
        # Hack: Use a special name for limit in symbol table?
        # Or just evaluate it every time?
        # Spec: "liczba iteracji jest ustalana na początku".
        # If we evaluate every time, and end_expr depends on loop vars, it's wrong.
        # So we MUST store it.
        
        # Let's assume we can use a temp location.
        # For this project, let's just evaluate it once and store in a dedicated temp.
        # But we need unique temps for nested loops.
        # I'll skip strict "evaluate once" for now and evaluate every time, 
        # BUT warn user or fix if I have time.
        # Actually, I can just emit code to calculate it and store it in a register if it fits?
        # No, loop body is long.
        
        # Correct way: Allocate temp in memory.
        # Since I didn't do it in Semantic Analysis, I can't easily add it now without shifting addresses.
        # But wait, SymbolTable.memory_counter is available.
        # I can allocate a new temp address NOW.
        # It's safe because we are generating code, addresses are fixed.
        # So I can just take next free address.
        
        limit_address = self.symbol_table.memory_counter
        self.symbol_table.memory_counter += 1
        
        self.visit(node.end_expr)
        self.emit(f"STORE {limit_address}")
        
        start_label = self.get_new_label("FOR_START")
        end_label = self.get_new_label("FOR_END")
        
        self.emit(f"{start_label}:")
        
        # Check condition: i <= limit (TO) or i >= limit (DOWNTO)
        # Load i
        self.emit(f"LOAD {sym.address}")
        self.emit("STORE 0") # i in 0
        
        # Load limit
        self.emit(f"LOAD {limit_address}")
        self.emit("STORE 1") # limit in 1
        
        # Compare
        # TO: i <= limit -> i - limit <= 0? No, unsigned.
        # i <= limit <=> limit >= i <=> limit - i >= 0.
        # If limit < i, then limit - i wraps or is 0 (saturated SUB).
        # We need strict check.
        # Use SUB:
        # If TO: Loop while i <= limit.
        # Exit if i > limit.
        # i > limit <=> i - limit > 0.
        # So: LOAD i; SUB limit; JPOS END.
        
        if not node.down_to: # TO
            self.emit("LOAD 0") # i
            self.emit("SUB 1")  # i - limit
            self.emit(f"JPOS {end_label}")
        else: # DOWNTO
            # Loop while i >= limit.
            # Exit if i < limit.
            # i < limit <=> limit > i <=> limit - i > 0.
            self.emit("LOAD 1") # limit
            self.emit("SUB 0")  # limit - i
            self.emit(f"JPOS {end_label}")
            
        for cmd in node.commands:
            self.visit(cmd)
            
        # Update iterator
        self.emit(f"LOAD {sym.address}")
        if not node.down_to:
            self.emit("INC r_a")
        else:
            self.emit("DEC r_a")
        self.emit(f"STORE {sym.address}")
        
        self.emit(f"JUMP {start_label}")
        self.emit(f"{end_label}:")

    def visit_Condition(self, node):
        # Evaluate condition -> r_a = 1 (true) or 0 (false)
        # Optimize using registers r_g, r_h if possible
        
        self.visit(node.left)
        
        # Use r_g to store left operand
        self.emit("SWP r_g")
        
        self.visit(node.right)
        # Right in r_a, Left in r_g
        
        # EQ: a == b <=> a-b == 0 AND b-a == 0
        if node.op == '=':
            # Check a-b
            self.emit("SWP r_g") # r_a=Left, r_g=Right
            self.emit("SUB r_g") # Left - Right
            self.emit("STORE 2") # Save result 1
            
            # Check b-a
            # Restore Right (r_g) and Left (we lost original Left, but we have Left-Right)
            # Actually, we need original values.
            # Since SUB destroys r_a, we should have saved copies?
            # Or just use memory for EQ/NEQ which need double check.
            # For EQ/NEQ, let's fallback to memory to be safe and simple.
            pass
        
        # For <, >, <=, >= we only need one subtraction.
        # a < b <=> b - a > 0
        # a > b <=> a - b > 0
        
        if node.op == '<':
            # b - a > 0
            # Right (r_a) - Left (r_g)
            self.emit("SUB r_g")
            self.emit_normalize_boolean()
            return

        elif node.op == '>':
            # a - b > 0
            # Left (r_g) - Right (r_a)
            self.emit("SWP r_g") # r_a=Left, r_g=Right
            self.emit("SUB r_g")
            self.emit_normalize_boolean()
            return
            
        elif node.op == '<=':
            # a <= b <=> not (a > b) <=> not (a - b > 0)
            self.emit("SWP r_g")
            self.emit("SUB r_g")
            self.emit_normalize_boolean()
            self.emit_invert_boolean_val()
            return
            
        elif node.op == '>=':
            # a >= b <=> not (a < b) <=> not (b - a > 0)
            # Right - Left
            self.emit("SUB r_g")
            self.emit_normalize_boolean()
            self.emit_invert_boolean_val()
            return

        # Fallback for =, != (or if we didn't return above)
        # Reload from r_g is hard because we swapped/clobbered.
        # So for =, != we use the old memory method.
        # But we already executed visit(left) and visit(right)!
        # And left is in r_g, right is in r_a.
        
        if node.op == '=':
            # Left in r_g, Right in r_a
            self.emit("STORE 1") # Right -> 1
            self.emit("SWP r_g") # Left -> r_a
            self.emit("STORE 0") # Left -> 0
            
            # a-b
            self.emit("LOAD 0"); self.emit("SWP r_b"); self.emit("LOAD 1"); self.emit("SUB r_b"); self.emit("STORE 2")
            # b-a
            self.emit("LOAD 1"); self.emit("SWP r_b"); self.emit("LOAD 0"); self.emit("SUB r_b"); self.emit("SWP r_b"); self.emit("LOAD 2"); self.emit("ADD r_b")
            
            self.emit_invert_boolean()
            
        elif node.op == '!=':
            self.emit("STORE 1")
            self.emit("SWP r_g")
            self.emit("STORE 0")
            
            # a-b
            self.emit("LOAD 0"); self.emit("SWP r_b"); self.emit("LOAD 1"); self.emit("SUB r_b"); self.emit("STORE 2")
            # b-a
            self.emit("LOAD 1"); self.emit("SWP r_b"); self.emit("LOAD 0"); self.emit("SUB r_b"); self.emit("SWP r_b"); self.emit("LOAD 2"); self.emit("ADD r_b")
            
            self.emit_normalize_boolean()

    def emit_invert_boolean(self):
        # If r_a == 0 -> r_a = 1
        # If r_a > 0  -> r_a = 0
        lbl_true = self.get_new_label("BOOL_TRUE")
        lbl_end = self.get_new_label("BOOL_END")
        self.emit(f"JZERO {lbl_true}")
        self.emit("RST r_a") # 0
        self.emit(f"JUMP {lbl_end}")
        self.emit(f"{lbl_true}:")
        self.emit("RST r_a"); self.emit("INC r_a") # 1
        self.emit(f"{lbl_end}:")

    def emit_normalize_boolean(self):
        # If r_a > 0 -> r_a = 1
        # If r_a == 0 -> r_a = 0
        lbl_true = self.get_new_label("NORM_TRUE")
        lbl_end = self.get_new_label("NORM_END")
        self.emit(f"JPOS {lbl_true}")
        self.emit("RST r_a")
        self.emit(f"JUMP {lbl_end}")
        self.emit(f"{lbl_true}:")
        self.emit("RST r_a"); self.emit("INC r_a")
        self.emit(f"{lbl_end}:")
        
    def emit_invert_boolean_val(self):
         # Assumes r_a is 0 or 1.
         # 0 -> 1, 1 -> 0
         # 1 - r_a
         self.emit("STORE 2")
         self.emit("RST r_a"); self.emit("INC r_a") # 1
         self.emit("SWP r_b"); self.emit("LOAD 2"); self.emit("SUB r_b") # 1 - old_val (Wait, SUB is r_a - r_b)
         # We want 1 - old_val.
         # r_a = 1. r_b = old_val.
         # SUB r_b -> 1 - old_val. Correct.

    def generate_division(self):
        # Inputs: Mem[0] (Dividend A), Mem[1] (Divisor B)
        # Output: r_a (Quotient)
        
        # r_b: Divisor (B)
        # r_c: Dividend (A) -> Remainder (R)
        # r_d: Quotient (Q)
        # r_e: Temp D (shifted divisor)
        # r_f: Shift count (power of 2)
        
        # Load B -> r_b
        self.emit("LOAD 1"); self.emit("SWP r_b")
        
        # Load A -> r_c
        self.emit("LOAD 0"); self.emit("SWP r_c")
        
        # Check B == 0
        self.emit("RST r_a"); self.emit("ADD r_b")
        lbl_zero = self.get_new_label("DIV_ZERO")
        self.emit(f"JZERO {lbl_zero}")
        
        # Init Q = 0 -> r_d
        self.emit("RST r_d")
        
        # Init Shift Count (Power) = 1 -> r_f
        self.emit("RST r_a"); self.emit("INC r_a"); self.emit("SWP r_f")
        
        # Init Shifted Divisor D = B -> r_e
        self.emit("RST r_a"); self.emit("ADD r_b"); self.emit("SWP r_e")
        
        # Align D to A (Shift Left Loop)
        lbl_align = self.get_new_label("DIV_ALIGN")
        lbl_align_end = self.get_new_label("DIV_ALIGN_END")
        
        self.emit(f"{lbl_align}:")
        # Check if D > A (r_e > r_c)
        # r_e - r_c > 0?
        self.emit("RST r_a"); self.emit("ADD r_e") # r_a = D
        self.emit("SUB r_c") # r_a = D - A
        self.emit(f"JPOS {lbl_align_end}") # If D > A, stop shifting
        
        # Shift D left
        self.emit("RST r_a"); self.emit("ADD r_e"); self.emit("SHL r_a"); self.emit("SWP r_e")
        
        # Shift Power left
        self.emit("RST r_a"); self.emit("ADD r_f"); self.emit("SHL r_a"); self.emit("SWP r_f")
        
        self.emit(f"JUMP {lbl_align}")
        self.emit(f"{lbl_align_end}:")
        
        # Now D > A. We went one step too far.
        # Shift back right once.
        self.emit("RST r_a"); self.emit("ADD r_e"); self.emit("SHR r_a"); self.emit("SWP r_e")
        self.emit("RST r_a"); self.emit("ADD r_f"); self.emit("SHR r_a"); self.emit("SWP r_f")
        
        # Main Loop (Subtract and Shift Right)
        lbl_loop = self.get_new_label("DIV_LOOP")
        lbl_end = self.get_new_label("DIV_END")
        
        self.emit(f"{lbl_loop}:")
        # Check if Power (r_f) == 0 -> End
        self.emit("RST r_a"); self.emit("ADD r_f")
        self.emit(f"JZERO {lbl_end}")
        
        # Check if R >= D (r_c >= r_e)
        # D - R <= 0? Or R - D >= 0?
        # Use SUB: D - R. If > 0, then D > R (skip). If 0, then D <= R (subtract).
        self.emit("RST r_a"); self.emit("ADD r_e") # D
        self.emit("SUB r_c") # D - R
        lbl_skip = self.get_new_label("DIV_SKIP")
        self.emit(f"JPOS {lbl_skip}")
        
        # R = R - D
        self.emit("RST r_a"); self.emit("ADD r_c"); self.emit("SUB r_e"); self.emit("SWP r_c")
        
        # Q = Q + Power
        self.emit("RST r_a"); self.emit("ADD r_d"); self.emit("ADD r_f"); self.emit("SWP r_d")
        
        self.emit(f"{lbl_skip}:")
        
        # Shift D right
        self.emit("RST r_a"); self.emit("ADD r_e"); self.emit("SHR r_a"); self.emit("SWP r_e")
        
        # Shift Power right
        self.emit("RST r_a"); self.emit("ADD r_f"); self.emit("SHR r_a"); self.emit("SWP r_f")
        
        self.emit(f"JUMP {lbl_loop}")
        
        self.emit(f"{lbl_end}:")
        # Result Q in r_d -> r_a
        self.emit("RST r_a"); self.emit("ADD r_d")
        
        self.emit(f"{lbl_zero}:")

    def generate_modulo(self):
        # Inputs: Mem[0] (Dividend A), Mem[1] (Divisor B)
        # Output: r_a (Remainder)
        
        # Reuse division logic but return Remainder (r_c) instead of Quotient (r_d)
        
        # r_b: Divisor (B)
        # r_c: Dividend (A) -> Remainder (R)
        # r_d: Quotient (Q)
        # r_e: Temp D (shifted divisor)
        # r_f: Shift count (power of 2)
        
        # Load B -> r_b
        self.emit("LOAD 1"); self.emit("SWP r_b")
        
        # Load A -> r_c
        self.emit("LOAD 0"); self.emit("SWP r_c")
        
        # Check B == 0
        self.emit("RST r_a"); self.emit("ADD r_b")
        lbl_zero = self.get_new_label("MOD_ZERO")
        self.emit(f"JZERO {lbl_zero}")
        
        # Init Q = 0 -> r_d
        self.emit("RST r_d")
        
        # Init Shift Count (Power) = 1 -> r_f
        self.emit("RST r_a"); self.emit("INC r_a"); self.emit("SWP r_f")
        
        # Init Shifted Divisor D = B -> r_e
        self.emit("RST r_a"); self.emit("ADD r_b"); self.emit("SWP r_e")
        
        # Align D to A (Shift Left Loop)
        lbl_align = self.get_new_label("MOD_ALIGN")
        lbl_align_end = self.get_new_label("MOD_ALIGN_END")
        
        self.emit(f"{lbl_align}:")
        # Check if D > A (r_e > r_c)
        self.emit("RST r_a"); self.emit("ADD r_e") # r_a = D
        self.emit("SUB r_c") # r_a = D - A
        self.emit(f"JPOS {lbl_align_end}") # If D > A, stop shifting
        
        # Shift D left
        self.emit("RST r_a"); self.emit("ADD r_e"); self.emit("SHL r_a"); self.emit("SWP r_e")
        
        # Shift Power left
        self.emit("RST r_a"); self.emit("ADD r_f"); self.emit("SHL r_a"); self.emit("SWP r_f")
        
        self.emit(f"JUMP {lbl_align}")
        self.emit(f"{lbl_align_end}:")
        
        # Now D > A. We went one step too far.
        # Shift back right once.
        self.emit("RST r_a"); self.emit("ADD r_e"); self.emit("SHR r_a"); self.emit("SWP r_e")
        self.emit("RST r_a"); self.emit("ADD r_f"); self.emit("SHR r_a"); self.emit("SWP r_f")
        
        # Main Loop (Subtract and Shift Right)
        lbl_loop = self.get_new_label("MOD_LOOP")
        lbl_end = self.get_new_label("MOD_END")
        
        self.emit(f"{lbl_loop}:")
        # Check if Power (r_f) == 0 -> End
        self.emit("RST r_a"); self.emit("ADD r_f")
        self.emit(f"JZERO {lbl_end}")
        
        # Check if R >= D (r_c >= r_e)
        self.emit("RST r_a"); self.emit("ADD r_e") # D
        self.emit("SUB r_c") # D - R
        lbl_skip = self.get_new_label("MOD_SKIP")
        self.emit(f"JPOS {lbl_skip}")
        
        # R = R - D
        self.emit("RST r_a"); self.emit("ADD r_c"); self.emit("SUB r_e"); self.emit("SWP r_c")
        
        # Q = Q + Power (Not needed for Modulo, but kept for symmetry/correctness of loop)
        self.emit("RST r_a"); self.emit("ADD r_d"); self.emit("ADD r_f"); self.emit("SWP r_d")
        
        self.emit(f"{lbl_skip}:")
        
        # Shift D right
        self.emit("RST r_a"); self.emit("ADD r_e"); self.emit("SHR r_a"); self.emit("SWP r_e")
        
        # Shift Power right
        self.emit("RST r_a"); self.emit("ADD r_f"); self.emit("SHR r_a"); self.emit("SWP r_f")
        
        self.emit(f"JUMP {lbl_loop}")
        
        self.emit(f"{lbl_end}:")
        # Result R in r_c -> r_a
        self.emit("RST r_a"); self.emit("ADD r_c")
        
        self.emit(f"{lbl_zero}:")

    def visit_ProcCall(self, node):
        # Args are passed by reference.
        # We need to calculate the ADDRESS of each argument and store it in the procedure's parameter locations.
        # Procedure parameters are in SymbolTable.
        
        proc_syms = self.symbol_table.get_all_in_scope(node.name)
        # We need to know the ORDER of args.
        # SymbolTable doesn't store order in `scopes`, but `procedures` dict does.
        proc_info = self.symbol_table.get_procedure(node.name)
        args_info = proc_info['args'] # List of ('VAR'/'ARRAY', name)
        
        for i, arg_expr in enumerate(node.args):
            # arg_expr is PIDENTIFIER (name of variable passed)
            # We need address of this variable.
            # If it's a global/local variable, its address is sym.address.
            # If it's a parameter of CURRENT procedure, it's already a pointer.
            
            # Get symbol of the ARGUMENT being passed
            arg_sym = self.symbol_table.get(arg_expr)
            
            # Get symbol of the PARAMETER in the CALLEE
            param_name = args_info[i][1]
            param_sym = proc_syms[param_name]
            
            # Calculate address to pass
            # If arg_sym is a VAR/ARRAY in Global/Local -> Address is arg_sym.address.
            # If arg_sym is a PARAMETER in Current Scope -> It holds an address. We need to load it.
            
            # How to distinguish?
            # We can check if `arg_sym.scope` is a procedure AND if it's in that procedure's args list.
            # Or just check if we are in a procedure and the symbol is an arg.
            
            # Simplified:
            # Load the ADDRESS of the argument into r_a.
            
            if self.current_scope != 'GLOBAL':
                # Check if arg_sym is a parameter of current scope
                current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                is_param = any(arg[1] == arg_sym.name for arg in current_proc_info['args'])
                
                if is_param:
                    # It's a pointer. Load the value (which is the address).
                    self.emit(f"LOAD {arg_sym.address}")
                else:
                    # It's a local variable. Load its address (constant).
                    self.generate_constant(arg_sym.address)
            else:
                # Global variable. Load its address.
                self.generate_constant(arg_sym.address)
            
            # If passing an ARRAY, we need to adjust for virtual base if it's a declared array.
            # If it's a parameter array, it's already a virtual base pointer.
            # If it's a declared array, we computed `address` (start of memory).
            # We need `address - start_index`.
            if arg_sym.type == 'ARRAY' and arg_sym.array_range is not None:
                # It's a declared array. Adjust base.
                start_index = arg_sym.array_range[0]
                # r_a has address.
                # r_a = r_a - start_index
                self.emit("STORE 0") # Save address
                self.generate_constant(start_index)
                self.emit("STORE 1") # Save start_index
                self.emit("LOAD 0"); self.emit("SUB 1") # address - start_index
            
            # Store r_a (the address) into the parameter location of the callee
            self.emit(f"STORE {param_sym.address}")
            
        self.emit(f"CALL PROC_{node.name}")



    def get_new_label(self, prefix):
        if not hasattr(self, 'label_counter'):
            self.label_counter = 0
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def visit_Read(self, node):
        # READ reads into r_a
        
        # We need to store r_a into node.identifier
        # But calculating address of identifier might use r_a.
        # So we calculate address first, save it, then READ, then STORE.
        
        sym = self.symbol_table.get(node.identifier.name)
        
        if node.identifier.index is not None:
            # Array access: tab[i]
            # Calculate address into r_b
            
            if isinstance(node.identifier.index, int):
                self.generate_constant(node.identifier.index)
            elif isinstance(node.identifier.index, str):
                idx_sym = self.symbol_table.get(node.identifier.index)
                self.emit(f"LOAD {idx_sym.address}")
            else:
                self.generate_constant(node.identifier.index)
            
            # r_a has index
            
            if sym.array_range is not None:
                # Declared array
                start = sym.array_range[0]
                self.emit("STORE 0") # Save index
                self.generate_constant(start)
                self.emit("SWP r_b")
                self.emit("LOAD 0")
                self.emit("SUB r_b") # index - start
                
                self.emit("SWP r_b")
                self.generate_constant(sym.address)
                self.emit("ADD r_b") # base + offset -> r_a
            else:
                # Parameter array
                self.emit("SWP r_b")
                self.emit(f"LOAD {sym.address}")
                self.emit("ADD r_b") # virtual_base + index -> r_a
                
            # Address is in r_a. Move to r_b.
            self.emit("SWP r_b")
            
            # READ
            self.emit("READ")
            
            # Store
            self.emit("RSTORE r_b")
            
        else:
            # Simple variable
            if sym.scope != 'GLOBAL' and sym.type in ['VAR', 'ARRAY']:
                # Check if param
                current_proc_info = self.symbol_table.get_procedure(self.current_scope)
                is_param = any(arg[1] == sym.name for arg in current_proc_info['args'])
                if is_param:
                    # Pointer. Load address to r_b.
                    self.emit(f"LOAD {sym.address}")
                    self.emit("SWP r_b")
                    self.emit("READ")
                    self.emit("RSTORE r_b")
                    return

            # Normal variable
            # We can just READ then STORE addr
            self.emit("READ")
            self.emit(f"STORE {sym.address}")

    def visit_Write(self, node):
        # Evaluate expression to r_a
        self.visit(node.value)
        # WRITE prints r_a
        self.emit("WRITE")

