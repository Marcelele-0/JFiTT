import sys
import os
import pytest
import subprocess
from pathlib import Path

# Add src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from code_gen import CodeGenerator
from symbol_table import SymbolTable

# Path to the C++ VM executable
VM_DIR = Path(__file__).parent.parent / 'virtual_machine'
VM_EXEC = VM_DIR / 'maszyna-wirtualna'

class MockSymbolTable(SymbolTable):
    def __init__(self):
        super().__init__()
        self.memory_counter = 100

def run_snippet(cg_func, a, b, tmp_path):
    if sys.platform == 'win32' and not VM_EXEC.exists():
        pytest.skip("C++ VM executable not found on Windows")
        
    st = MockSymbolTable()
    cg = CodeGenerator(st)
    
    # Setup inputs in Mem[0] and Mem[1]
    cg.generate_constant(a)
    cg.emit("STORE 0")
    cg.generate_constant(b)
    cg.emit("STORE 1")
    
    # Run function
    cg_func(cg)
    
    # Write result (r_a)
    cg.emit("WRITE")
    
    cg.emit("HALT")
    
    code = cg.get_code()
    
    # Write assembly to temp file
    asm_file = tmp_path / "snippet.mr"
    asm_file.write_text(code, encoding='utf-8')
    
    # Run on C++ VM
    try:
        result = subprocess.run(
            [str(VM_EXEC), str(asm_file)],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            pytest.fail(f"VM crashed: {result.stderr}")
            
        # Parse output
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith('> '):
                return int(line.split('> ')[1].strip())
        return None
        
    except subprocess.TimeoutExpired:
        pytest.fail("VM execution timed out")
    except FileNotFoundError:
        pytest.fail(f"VM executable not found at {VM_EXEC}")

def test_multiplication_small(tmp_path):
    res = run_snippet(lambda cg: cg.generate_multiplication(), 123, 456, tmp_path)
    assert res == 123 * 456

def test_multiplication_large(tmp_path):
    a = 1234567890
    b = 987654321
    res = run_snippet(lambda cg: cg.generate_multiplication(), a, b, tmp_path)
    assert res == a * b

def test_modulo_small(tmp_path):
    res = run_snippet(lambda cg: cg.generate_modulo(), 100, 30, tmp_path)
    assert res == 100 % 30

def test_modulo_large(tmp_path):
    a = 1234567890
    b = 987654321
    res = run_snippet(lambda cg: cg.generate_modulo(), a, b, tmp_path)
    assert res == a % b

def test_modulo_example5(tmp_path):
    # pot:=a%c;
    # a = 1234567890
    # c = 987654321
    # pot = 246913569
    a = 1234567890
    c = 987654321
    res = run_snippet(lambda cg: cg.generate_modulo(), a, c, tmp_path)
    assert res == a % c

def test_multiplication_example5_step(tmp_path):
    # d:=d*pot
    # d=1, pot=246913569
    d = 1
    pot = 246913569
    res = run_snippet(lambda cg: cg.generate_multiplication(), d, pot, tmp_path)
    assert res == d * pot

def test_modulo_example5_step2(tmp_path):
    # d:=d%c
    # d=246913569, c=987654321
    d = 246913569
    c = 987654321
    res = run_snippet(lambda cg: cg.generate_modulo(), d, c, tmp_path)
    assert res == d % c

def test_division(tmp_path):
    res = run_snippet(lambda cg: cg.generate_division(), 100, 30, tmp_path)
    assert res == 100 // 30
