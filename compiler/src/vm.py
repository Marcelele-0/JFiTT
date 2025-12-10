import sys
import re

class VirtualMachine:
    def __init__(self):
        self.registers = {
            0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0
        }
        self.memory = {}
        self.program = []
        self.pc = 0 # Program Counter
        self.cost = 0
        
    def load_program(self, code_str):
        lines = code_str.strip().split('\n')
        self.program = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            cmd = parts[0]
            arg = None
            if len(parts) > 1:
                arg = parts[1]
                # Try to parse arg as register or number
                if arg in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
                    arg = ord(arg) - ord('a') # 0-7
                elif arg.startswith('r_') and len(arg) == 3 and arg[2] in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
                     arg = ord(arg[2]) - ord('a')
                else:
                    try:
                        arg = int(arg)
                    except ValueError:
                        pass # Keep as string if it's a label (shouldn't happen after fix)
            
            self.program.append((cmd, arg))

    def run(self, inputs=None):
        if inputs is None:
            inputs = []
        input_idx = 0
        output = []
        
        self.pc = 0
        self.cost = 0
        
        # Limit execution to prevent infinite loops during tests
        max_steps = 1000000 
        steps = 0
        
        while self.pc < len(self.program):
            if steps > max_steps:
                raise Exception("Time Limit Exceeded")
            steps += 1
            
            cmd, arg = self.program[self.pc]
            
            if cmd == 'HALT':
                break
                
            elif cmd == 'READ':
                if input_idx < len(inputs):
                    val = inputs[input_idx]
                    input_idx += 1
                    self.registers[0] = val # Read to r_a? Spec says "READ". Usually to r_a or address?
                    # VM code: "cin >> r[0];" -> Yes, reads to r_a (accumulator)
                    self.cost += 100
                else:
                    raise Exception("Input exhausted")
                self.pc += 1
                
            elif cmd == 'WRITE':
                # VM code: "cout << r[0]"
                output.append(self.registers[0])
                self.cost += 100
                self.pc += 1
                
            elif cmd == 'LOAD':
                # LOAD addr -> r[0] = mem[addr]
                addr = arg
                self.registers[0] = self.memory.get(addr, 0)
                self.cost += 50
                self.pc += 1
                
            elif cmd == 'STORE':
                # STORE addr -> mem[addr] = r[0]
                addr = arg
                self.memory[addr] = self.registers[0]
                self.cost += 50
                self.pc += 1
                
            elif cmd == 'RLOAD':
                # RLOAD reg -> r[0] = mem[r[reg]]
                reg = arg
                addr = self.registers[reg]
                self.registers[0] = self.memory.get(addr, 0)
                self.cost += 50
                self.pc += 1
                
            elif cmd == 'RSTORE':
                # RSTORE reg -> mem[r[reg]] = r[0]
                reg = arg
                addr = self.registers[reg]
                self.memory[addr] = self.registers[0]
                self.cost += 50
                self.pc += 1
                
            elif cmd == 'ADD':
                # ADD reg -> r[0] += r[reg]
                reg = arg
                self.registers[0] += self.registers[reg]
                self.cost += 5
                self.pc += 1
                
            elif cmd == 'SUB':
                # SUB reg -> r[0] = max(0, r[0] - r[reg])
                reg = arg
                val = self.registers[0] - self.registers[reg]
                self.registers[0] = max(0, val)
                self.cost += 5
                self.pc += 1
                
            elif cmd == 'SWP':
                # SWP reg -> swap(r[0], r[reg])
                reg = arg
                self.registers[0], self.registers[reg] = self.registers[reg], self.registers[0]
                self.cost += 5
                self.pc += 1
                
            elif cmd == 'RST':
                # RST reg -> r[reg] = 0
                reg = arg
                self.registers[reg] = 0
                self.cost += 1
                self.pc += 1
                
            elif cmd == 'INC':
                # INC reg -> r[reg]++
                reg = arg
                self.registers[reg] += 1
                self.cost += 1
                self.pc += 1
                
            elif cmd == 'DEC':
                # DEC reg -> if r[reg]>0 r[reg]--
                reg = arg
                if self.registers[reg] > 0:
                    self.registers[reg] -= 1
                self.cost += 1
                self.pc += 1
                
            elif cmd == 'SHL':
                # SHL reg -> r[reg] <<= 1
                reg = arg
                self.registers[reg] <<= 1
                self.cost += 1
                self.pc += 1
                
            elif cmd == 'SHR':
                # SHR reg -> r[reg] >>= 1
                reg = arg
                self.registers[reg] >>= 1
                self.cost += 1
                self.pc += 1
                
            elif cmd == 'JUMP':
                # JUMP line
                self.pc = arg
                self.cost += 1
                
            elif cmd == 'JPOS':
                # JPOS line -> if r[0] > 0 jump
                if self.registers[0] > 0:
                    self.pc = arg
                else:
                    self.pc += 1
                self.cost += 1
                
            elif cmd == 'JZERO':
                # JZERO line -> if r[0] == 0 jump
                if self.registers[0] == 0:
                    self.pc = arg
                else:
                    self.pc += 1
                self.cost += 1
                
            elif cmd == 'CALL':
                # CALL addr -> r[0] = pc+1; jump addr
                # Note: VM spec says r[0] gets return address
                self.registers[0] = self.pc + 1
                self.pc = arg
                self.cost += 1
                
            elif cmd == 'RTRN':
                # RTRN -> jump r[0]
                # Note: VM spec says jump to address in r[0]
                # Wait, spec says: "lr = r[0]" (lr is PC)
                # But wait, CALL sets r[0] to return address.
                # But if we use r[0] for calculations inside procedure, we lose return address!
                # The compiler must save r[0] (return address) somewhere if it uses r[0].
                # My compiler currently does NOT save return address!
                # Procedures use r_a (r[0]) heavily.
                # This is a BUG in procedure generation.
                # We must save r[0] to memory at start of procedure and restore it before RTRN?
                # Or assume r[0] is preserved? No, r[0] is accumulator.
                # We need to fix this in CodeGen too.
                
                self.pc = self.registers[0]
                self.cost += 1
                
            else:
                raise Exception(f"Unknown command: {cmd}")
                
        return output, self.cost
