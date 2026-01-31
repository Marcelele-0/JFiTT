import pytest
import subprocess
import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import lexer
from parser import parser
from semantic_analysis import SemanticAnalyzer
from code_gen import CodeGenerator
print(f"DEBUG: CodeGenerator imported from {CodeGenerator.__module__}")
import code_gen
print(f"DEBUG: code_gen file: {code_gen.__file__}")

def get_program_files():
    """Get program*.imp files that have corresponding assertions in test_assertions/"""
    test_files_dir = Path(__file__).parent.parent / 'test_files'
    assertions_dir = Path(__file__).parent.parent / 'test_assertions'
    
    # We look for programX.imp
    files = sorted(test_files_dir.glob('program*.imp'))
    
    test_pairs = []
    
    for f in files:
        # Check if corresponding .mr exists
        assertion_file = assertions_dir / (f.stem + '.mr')
        if assertion_file.exists():
            test_pairs.append((f, assertion_file))
        else:
            # Special case? Or just skip?
            # User said "programX to te a asseriotn".
            # If program3 has no program3.mr, we skip it.
            pass
            
    return test_pairs

def get_vm_path():
    vm_path = Path(__file__).parent.parent / 'virtual_machine' / 'maszyna-wirtualna'
    if not vm_path.exists():
        pytest.skip("Virtual machine executable not found")
    return vm_path

class TestProgramComparison:
    @pytest.mark.parametrize("test_file, assertion_file", get_program_files(), ids=lambda x: x.stem)
    def test_compare_outputs(self, test_file, assertion_file):
        # 1. Compile test_file
        with open(test_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        lexer.input(source_code)
        ast = parser.parse(source_code, lexer=lexer)
        assert ast is not None, f"Parsing failed for {test_file.name}"
        
        analyzer = SemanticAnalyzer()
        symbol_table = analyzer.analyze(ast)
        
        generator = CodeGenerator(symbol_table)
        generator.generate(ast)
        compiled_code = generator.get_code()
        
        # Write compiled code to temp file
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        compiled_file = outputs_dir / (test_file.stem + '.compiled.mr')
        
        with open(compiled_file, 'w', encoding='utf-8') as f:
            f.write(compiled_code)
            
        # 2. Run both on VM with same input
        # Input numbers: 10, 20, 30, 40, 50, 5, 2
        input_data = "10\n20\n30\n40\n50\n5\n2\n"
        vm_path = get_vm_path()
        
        # Run Actual
        proc_actual = subprocess.run(
            [str(vm_path), str(compiled_file)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert proc_actual.returncode == 0, f"Actual execution failed: {proc_actual.stderr}"
        
        # Run Expected
        proc_expected = subprocess.run(
            [str(vm_path), str(assertion_file)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        assert proc_expected.returncode == 0, f"Expected execution failed: {proc_expected.stderr}"
        
        # 3. Compare Stdout
        def extract_value(output, pattern):
            try:
                import re
                # Try removing ANSI codes first for robustness
                clean_output = re.sub(r'\x1b\[[0-9;]*m', '', output)
                for line in clean_output.splitlines():
                    # Match 'koszt: 12 345;' or 'koszt: 123;'
                    # Regex: koszt: ([\d ]+)
                    match = re.search(pattern, line)
                    if match:
                        num_str = match.group(1).replace(' ', '')
                        return int(num_str)
            except:
                pass
            return -1

        # Metrics 1: Dynamic Execution Cost (Instructions Executed)
        actual_cost = extract_value(proc_actual.stdout, r'koszt: ([\d ]+)')
        expected_cost = extract_value(proc_expected.stdout, r'koszt: ([\d ]+)')
        
        # Metrics 2: Static Instruction Count (Code Size in VM)
        actual_instr_count = extract_value(proc_actual.stdout, r'liczba rozkazów: ([\d ]+)')
        expected_instr_count = extract_value(proc_expected.stdout, r'liczba rozkazów: ([\d ]+)')
        
        # Metrics 3: Lines of Code (Source Assembly)
        def count_lines(path):
            with open(path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        
        actual_loc = count_lines(compiled_file)
        expected_loc = count_lines(assertion_file)
        
        print(f"\n[METRICS] {test_file.stem}:")
        print(f"  - Exec Cost: My={actual_cost} vs Ref={expected_cost} (Diff: {actual_cost - expected_cost})")
        print(f"  - VM Instr:  My={actual_instr_count} vs Ref={expected_instr_count} (Diff: {actual_instr_count - expected_instr_count})")
        print(f"  - LOC:       My={actual_loc} vs Ref={expected_loc} (Diff: {actual_loc - expected_loc})")

        def clean_output(output):
            lines = output.splitlines()
            # Filter out VM status lines
            filtered = [
                line for line in lines 
                if "Czytanie kodu" not in line 
                and "Skończono czytanie kodu" not in line
                and "Uruchamianie programu" not in line
                and "Skończono program" not in line
            ]
            return "\n".join(filtered)

        assert clean_output(proc_actual.stdout) == clean_output(proc_expected.stdout), "Outputs do not match!"
