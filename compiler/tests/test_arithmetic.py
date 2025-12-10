import sys
import os
import pytest

# Add src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from vm import VirtualMachine
from code_gen import CodeGenerator
from symbol_table import SymbolTable

class MockSymbolTable(SymbolTable):
    def __init__(self):
        super().__init__()
        self.memory_counter = 100

def run_snippet(cg_func, a, b):
    st = MockSymbolTable()
    cg = CodeGenerator(st)
    
    # Setup inputs in Mem[0] and Mem[1]
    cg.generate_constant(a)
    cg.emit("STORE 0")
    cg.generate_constant(b)
    cg.emit("STORE 1")
    
    # Run function
    cg_func(cg)
    
    cg.emit("HALT")
    
    code = cg.get_code()
    vm = VirtualMachine()
    vm.load_program(code)
    vm.run()
    return vm.registers[0]

def test_multiplication_small():
    res = run_snippet(lambda cg: cg.generate_multiplication(), 123, 456)
    assert res == 123 * 456

def test_multiplication_large():
    a = 1234567890
    b = 987654321
    res = run_snippet(lambda cg: cg.generate_multiplication(), a, b)
    assert res == a * b

def test_modulo_small():
    res = run_snippet(lambda cg: cg.generate_modulo(), 100, 30)
    assert res == 100 % 30

def test_modulo_large():
    a = 1234567890
    b = 987654321
    res = run_snippet(lambda cg: cg.generate_modulo(), a, b)
    assert res == a % b

def test_modulo_example5():
    # pot:=a%c;
    # a = 1234567890
    # c = 987654321
    # pot = 246913569
    a = 1234567890
    c = 987654321
    res = run_snippet(lambda cg: cg.generate_modulo(), a, c)
    assert res == a % c

def test_multiplication_example5_step():
    # d:=d*pot
    # d=1, pot=246913569
    d = 1
    pot = 246913569
    res = run_snippet(lambda cg: cg.generate_multiplication(), d, pot)
    assert res == d * pot

def test_modulo_example5_step2():
    # d:=d%c
    # d=246913569, c=987654321
    d = 246913569
    c = 987654321
    res = run_snippet(lambda cg: cg.generate_modulo(), d, c)
    assert res == d % c

def test_division():
    res = run_snippet(lambda cg: cg.generate_division(), 100, 30)
    assert res == 100 // 30
