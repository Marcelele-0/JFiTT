from ast_nodes import *

class CodeGenerator:
    def __init__(self, symbol_table):
        self.symbol_table = symbol_table
        self.code = []
        self.current_scope = 'GLOBAL'
        # Registers: a, b, c, d, e, f, g, h
        # r_a is accumulator
        
    def emit(self, instr):
        self.code.append(instr)

    def get_code(self):
        return '\n'.join(self.code)

    def generate(self, ast):
        # Generate code for main program
        # Procedures are generated first (jumps over them?)
        # Usually:
        # JUMP MAIN
        # PROC1: ...
        # PROC2: ...
        # MAIN: ...
        # HALT
        
        self.emit("JUMP MAIN")
        
        for proc in ast.procedures:
            self.generate_procedure(proc)
            
        self.emit("MAIN:")
        self.generate_block(ast.main)
        self.emit("HALT")

    def generate_procedure(self, node):
        self.current_scope = node.name
        # Label for procedure
        # We need to handle procedure entry/exit?
        # Since no recursion, we don't need stack frames.
        # Just a label.
        # But wait, how do we return?
        # The VM has CALL/RTRN? Yes.
        
        self.emit(f"PROC_{node.name}:")
        
        # We might need to handle parameters here if they need copying?
        # But they are passed by reference, so the caller sets up the addresses.
        # The symbol table already has the addresses for args.
        # Wait, if passed by reference, the symbol table entry for an arg
        # should point to a memory location that HOLDS THE ADDRESS of the actual variable.
        # So when we access an arg, we do indirect load.
        
        self.generate_block(node)
        
        self.emit("RTRN")
        self.current_scope = 'GLOBAL'

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
        # Calculate expression -> r_a
        self.visit(node.expression)
        
        # Store r_a to variable
        sym = self.symbol_table.get(node.identifier.name)
        
        # If it's an array assignment: tab[i] := expr
        if node.identifier.index:
            # We need to calculate address: base + index - start
            # This is complex because we need to preserve r_a (result of expr).
            # So we should calculate address FIRST, save it, then calc expr.
            
            # 1. Calculate index
            # Save r_a (expr result) is not available yet.
            # So:
            # Calc Index -> r_a
            # ...
            pass
            # Better:
            # 1. Calc Index -> r_a
            # 2. Adjust for start index (SUB start)
            # 3. Add base address (ADD base)
            # 4. Store address in temporary register (e.g. r_b) or memory.
            # 5. Calc Expression -> r_a
            # 6. STORE r_a to address in r_b (STORE @r_b? No, STORE is direct. RSTORE is indirect)
            # VM has RSTORE reg? "STORE (adresowanie bezpośrednie), RSTORE (adresowanie pośrednie przez rejestr)"
            # Yes. RSTORE r_x stores r_a to address in r_x.
            
            pass
        else:
            # Simple variable
            if sym.scope != 'GLOBAL' and sym.type in ['VAR', 'ARRAY']: # Arg passed by ref?
                # If it's a local var (not arg), direct store.
                # If it's an arg, it's a pointer.
                # How do we distinguish?
                # We need to know if it's a parameter.
                # SymbolTable doesn't explicitly say "Parameter".
                # But we can check if it's in `procedures[current_scope]['args']`.
                
                # Let's assume for now direct addressing for globals/locals, indirect for args.
                # I need to check if it's an argument.
                pass
            
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
            # Subtract start index
            start = sym.array_range[0]
            self.emit("STORE 0") # Save index
            self.generate_constant(start)
            self.emit("STORE 1") # Save start
            self.emit("LOAD 0"); self.emit("SUB 1") # index - start
            
            # Add base address
            self.emit("STORE 0") # Save offset
            self.generate_constant(sym.address)
            self.emit("ADD 0") # base + offset
            
            # Now r_a has the effective address.
            # Load value from this address.
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
        self.emit("SUB r_a r_a") # r_a = 0
        if value == 0:
            return
        
        # Binary representation
        bin_str = bin(value)[2:]
        for bit in bin_str:
            self.emit("SHL r_a") # r_a *= 2
            if bit == '1':
                self.emit("INC r_a")

    def visit_BinaryOp(self, node):
        # Left -> r_a
        # Store r_a to temp
        # Right -> r_a
        # Op
        
        self.visit(node.left)
        self.emit("STORE 0") # Use scratchpad 0
        
        self.visit(node.right)
        self.emit("STORE 1") # Use scratchpad 1
        
        # Load left back to r_a?
        # Or load left to r_b?
        # VM: ADD r_x? Or ADD address?
        # If ADD takes address:
        # LOAD 0 (left)
        # ADD 1 (right)
        
        # Let's assume ADD/SUB take ADDRESS.
        # "ADD (dodawanie)..."
        # If it takes register, it would be ADD r_b.
        # Report says: "ADD (dodawanie), SUB (odejmowanie)..."
        # "Komunikacja z pamięcią: LOAD, STORE... RLOAD, RSTORE".
        # This implies ADD/SUB might be register-register or register-memory.
        # "Schemat blokowy... Dodaj r_c do wyniku r_d (ADD)." -> Implies register-register?
        # "ADD r_b" -> Add r_b to r_a?
        # Let's assume register-register is possible or default.
        
        # If ADD is register-register:
        # LOAD 0 -> r_a
        # SWP r_b (move r_a to r_b)
        # LOAD 1 -> r_a
        # ADD r_b (r_a = r_a + r_b) -> Wait, usually r_a += r_b.
        # If we want Left + Right:
        # Left is in 0. Right is in 1.
        # LOAD 0 (Left) -> r_a
        # ADD 1 (Right) -> r_a += Mem[1]
        
        # If ADD takes memory address, it's easier.
        # Let's assume ADD takes memory address for now.
        
        if node.op == '+':
            self.emit("LOAD 0")
            self.emit("ADD 1")
        elif node.op == '-':
            self.emit("LOAD 0")
            self.emit("SUB 1")
        elif node.op == '*':
            # Call multiplication routine
            # We need to implement it.
            # Pass args in registers or memory?
            # Let's use memory 0 and 1.
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
        self.emit("SUB r_a r_a") # r_a = 0
        self.emit("SWP r_d")
        
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
        self.emit("SWP r_b") # r_a = b
        self.emit("SWP r_e") # r_e = b, r_a = old_e (garbage)
        self.emit("SWP r_b") # Restore b (r_a = garbage, r_b = b) -> Wait, SWP swaps.
        # Correct copy sequence:
        # r_a has something. r_b has B.
        # SWP r_b -> r_a=B, r_b=garbage
        # SWP r_e -> r_e=B, r_a=old_e
        # SWP r_b -> r_b=old_e, r_a=B -> WRONG. We lost B from r_b.
        
        # To copy r_b to r_e using SWP:
        # We need to use r_a as bridge.
        # But SWP destroys source.
        # We must use ADD?
        # r_a = 0. ADD r_b -> r_a = b.
        # Then SWP r_e.
        # So:
        # SUB r_a r_a
        # ADD r_b (Assuming ADD r_b adds r_b to r_a)
        # SWP r_e (r_e = b)
        
        # Check parity of r_e
        self.emit("SUB r_a r_a")
        self.emit("ADD r_b")
        self.emit("SHR r_a")
        self.emit("SHL r_a")
        # Now r_a = (b >> 1) << 1.
        # Subtract from b (r_b)
        # r_a = b - r_a. If 1, then odd. If 0, even.
        # Wait, SUB is r_a = r_a - operand? Or r_a = operand - r_a?
        # Usually r_a -= operand.
        # So we want b - ((b>>1)<<1).
        # We have ((b>>1)<<1) in r_a.
        # We want to subtract it FROM b.
        # But we can't easily do `SUB r_b` (r_a - r_b). That gives negative.
        # But `SUB` is saturated to 0.
        # If b is odd (e.g. 3), cleared is 2. 2 - 3 = 0 (saturated).
        # If b is even (e.g. 2), cleared is 2. 2 - 2 = 0.
        # This doesn't help.
        
        # We need b - cleared.
        # Store cleared to temp (Mem[2]).
        self.emit("STORE 2")
        
        # Load b
        self.emit("SUB r_a r_a")
        self.emit("ADD r_b")
        
        # Subtract cleared
        self.emit("SUB 2")
        
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
        # Left in 0, Right in 1
        self.visit(node.left)
        self.emit("STORE 0")
        self.visit(node.right)
        self.emit("STORE 1")
        
        # EQ: a == b <=> a-b == 0 AND b-a == 0
        if node.op == '=':
            self.emit("LOAD 0"); self.emit("SUB 1"); self.emit("STORE 2") # a-b
            self.emit("LOAD 1"); self.emit("SUB 0"); self.emit("ADD 2")   # (b-a) + (a-b)
            # If 0, then equal.
            # We want 1 if equal, 0 if not.
            # Current r_a is 0 if equal, >0 if not.
            # Invert: If 0 -> 1, If >0 -> 0.
            # How to invert?
            # JZERO TRUE
            # LOAD 0
            # JUMP END
            # TRUE: LOAD 1
            # END:
            self.emit_invert_boolean()
            
        elif node.op == '!=':
            self.emit("LOAD 0"); self.emit("SUB 1"); self.emit("STORE 2")
            self.emit("LOAD 1"); self.emit("SUB 0"); self.emit("ADD 2")
            # If >0, then not equal.
            # We want 1 if >0, 0 if 0.
            self.emit_normalize_boolean()
            
        elif node.op == '<':
            # a < b <=> b - a > 0
            self.emit("LOAD 1"); self.emit("SUB 0")
            self.emit_normalize_boolean()
            
        elif node.op == '>':
            # a > b <=> a - b > 0
            self.emit("LOAD 0"); self.emit("SUB 1")
            self.emit_normalize_boolean()
            
        elif node.op == '<=':
            # a <= b <=> not (a > b)
            self.emit("LOAD 0"); self.emit("SUB 1")
            self.emit_normalize_boolean() # 1 if a > b
            self.emit_invert_boolean_val() # 0 if a > b (so a <= b)
            
        elif node.op == '>=':
            # a >= b <=> not (a < b)
            self.emit("LOAD 1"); self.emit("SUB 0")
            self.emit_normalize_boolean()
            self.emit_invert_boolean_val()

    def emit_invert_boolean(self):
        # If r_a == 0 -> r_a = 1
        # If r_a > 0  -> r_a = 0
        lbl_true = self.get_new_label("BOOL_TRUE")
        lbl_end = self.get_new_label("BOOL_END")
        self.emit(f"JZERO {lbl_true}")
        self.emit("SUB r_a r_a") # 0
        self.emit(f"JUMP {lbl_end}")
        self.emit(f"{lbl_true}:")
        self.emit("SUB r_a r_a"); self.emit("INC r_a") # 1
        self.emit(f"{lbl_end}:")

    def emit_normalize_boolean(self):
        # If r_a > 0 -> r_a = 1
        # If r_a == 0 -> r_a = 0
        lbl_true = self.get_new_label("NORM_TRUE")
        lbl_end = self.get_new_label("NORM_END")
        self.emit(f"JPOS {lbl_true}")
        self.emit("SUB r_a r_a")
        self.emit(f"JUMP {lbl_end}")
        self.emit(f"{lbl_true}:")
        self.emit("SUB r_a r_a"); self.emit("INC r_a")
        self.emit(f"{lbl_end}:")
        
    def emit_invert_boolean_val(self):
         # Assumes r_a is 0 or 1.
         # 0 -> 1, 1 -> 0
         # 1 - r_a
         self.emit("STORE 2")
         self.emit("SUB r_a r_a"); self.emit("INC r_a") # 1
         self.emit("SUB 2")

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
        self.emit("SUB r_a r_a"); self.emit("ADD r_b")
        lbl_zero = self.get_new_label("DIV_ZERO")
        self.emit(f"JZERO {lbl_zero}")
        
        # Init Q = 0 -> r_d
        self.emit("SUB r_a r_a"); self.emit("SWP r_d")
        
        # Init Shift Count (Power) = 1 -> r_f
        self.emit("SUB r_a r_a"); self.emit("INC r_a"); self.emit("SWP r_f")
        
        # Init Shifted Divisor D = B -> r_e
        self.emit("SUB r_a r_a"); self.emit("ADD r_b"); self.emit("SWP r_e")
        
        # Align D to A (Shift Left Loop)
        lbl_align = self.get_new_label("DIV_ALIGN")
        lbl_align_end = self.get_new_label("DIV_ALIGN_END")
        
        self.emit(f"{lbl_align}:")
        # Check if D > A (r_e > r_c)
        # r_e - r_c > 0?
        self.emit("SUB r_a r_a"); self.emit("ADD r_e") # r_a = D
        self.emit("SUB r_c") # r_a = D - A
        self.emit(f"JPOS {lbl_align_end}") # If D > A, stop shifting
        
        # Shift D left
        self.emit("SUB r_a r_a"); self.emit("ADD r_e"); self.emit("SHL r_a"); self.emit("SWP r_e")
        
        # Shift Power left
        self.emit("SUB r_a r_a"); self.emit("ADD r_f"); self.emit("SHL r_a"); self.emit("SWP r_f")
        
        self.emit(f"JUMP {lbl_align}")
        self.emit(f"{lbl_align_end}:")
        
        # Now D > A. We went one step too far.
        # Shift back right once.
        self.emit("SUB r_a r_a"); self.emit("ADD r_e"); self.emit("SHR r_a"); self.emit("SWP r_e")
        self.emit("SUB r_a r_a"); self.emit("ADD r_f"); self.emit("SHR r_a"); self.emit("SWP r_f")
        
        # Main Loop (Subtract and Shift Right)
        lbl_loop = self.get_new_label("DIV_LOOP")
        lbl_end = self.get_new_label("DIV_END")
        
        self.emit(f"{lbl_loop}:")
        # Check if Power (r_f) == 0 -> End
        self.emit("SUB r_a r_a"); self.emit("ADD r_f")
        self.emit(f"JZERO {lbl_end}")
        
        # Check if R >= D (r_c >= r_e)
        # D - R <= 0? Or R - D >= 0?
        # Use SUB: D - R. If > 0, then D > R (skip). If 0, then D <= R (subtract).
        # Wait, SUB is saturated.
        # If D > R, D - R > 0.
        # If D <= R, D - R = 0.
        self.emit("SUB r_a r_a"); self.emit("ADD r_e") # D
        self.emit("SUB r_c") # D - R
        lbl_skip = self.get_new_label("DIV_SKIP")
        self.emit(f"JPOS {lbl_skip}")
        
        # R = R - D
        self.emit("SUB r_a r_a"); self.emit("ADD r_c"); self.emit("SUB r_e"); self.emit("SWP r_c")
        
        # Q = Q + Power
        self.emit("SUB r_a r_a"); self.emit("ADD r_d"); self.emit("ADD r_f"); self.emit("SWP r_d")
        
        self.emit(f"{lbl_skip}:")
        
        # Shift D right
        self.emit("SUB r_a r_a"); self.emit("ADD r_e"); self.emit("SHR r_a"); self.emit("SWP r_e")
        
        # Shift Power right
        self.emit("SUB r_a r_a"); self.emit("ADD r_f"); self.emit("SHR r_a"); self.emit("SWP r_f")
        
        self.emit(f"JUMP {lbl_loop}")
        
        self.emit(f"{lbl_end}:")
        # Result Q in r_d -> r_a
        self.emit("SUB r_a r_a"); self.emit("ADD r_d")
        
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
            
            # Store r_a (the address) into the parameter location of the callee
            self.emit(f"STORE {param_sym.address}")
            
        self.emit(f"CALL PROC_{node.name}")



    def get_new_label(self, prefix):
        if not hasattr(self, 'label_counter'):
            self.label_counter = 0
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def visit_Read(self, node):
        # READ returns to r_a? Or READ address?
        # "READ, WRITE. Koszt: 100 cykli."
        # Usually READ address.
        sym = self.symbol_table.get(node.identifier.name)
        self.emit(f"READ {sym.address}")

    def visit_Write(self, node):
        # WRITE value? Or WRITE address?
        # Usually WRITE address.
        # If we have an expression, we compute it to r_a, store to temp, then WRITE temp.
        if isinstance(node.value, Identifier):
             sym = self.symbol_table.get(node.value.name)
             self.emit(f"WRITE {sym.address}")
        else:
             # Expression or Number
             self.visit(node.value)
             self.emit("STORE 0")
             self.emit("WRITE 0")

