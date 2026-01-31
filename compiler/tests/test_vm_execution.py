
import pytest
import subprocess
import os
import sys
from pathlib import Path

# Add src directory to the path so we can import compiler modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import lexer
from parser import parser
from semantic_analysis import SemanticAnalyzer
from code_gen import CodeGenerator

def get_test_files():
    """Get all .imp test files from test_files directory"""
    test_files_dir = Path(__file__).parent.parent / 'test_files'
    test_files = sorted(test_files_dir.glob('example*.imp'))
    return test_files

def get_vm_path():
    """Get path to the virtual machine executable"""
    vm_path = Path(__file__).parent.parent / 'virtual_machine' / 'maszyna-wirtualna'
    if not vm_path.exists():
        pytest.skip("Virtual machine executable not found")
    return vm_path

class TestVMExecution:
    """Test suite for running compiled code on the virtual machine"""

    @pytest.mark.parametrize("test_file", get_test_files(), ids=lambda f: f.name)
    def test_vm_execution(self, test_file):
        """
        Test that a source file can be compiled and executed on the VM.
        Captures output and logs steps.
        """
        
        # 1. Compile the file
        with open(test_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        # Create output file path
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_filename = test_file.stem + '.mr'
        output_file = outputs_dir / output_filename
        
        # Compile
        lexer.input(source_code)
        ast = parser.parse(source_code, lexer=lexer)
        assert ast is not None, f"Parsing failed for {test_file.name}"
        
        analyzer = SemanticAnalyzer()
        symbol_table = analyzer.analyze(ast)
        
        generator = CodeGenerator(symbol_table)
        generator.generate(ast)
        code = generator.get_code()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
            
        # 2. Prepare input for the VM
        # Some programs require input (READ command).
        # We'll provide some default inputs based on the file name or content if needed.
        # For now, let's provide a sequence of numbers "10 20 30 40 50" which should cover most cases.
        # If a program needs specific input, we might need a mapping.
        
        input_data = "10\n20\n30\n40\n50\n"
        
        # 3. Run the VM
        vm_path = get_vm_path()
        
        # We use subprocess to run the VM
        # We capture stdout and stderr to log steps
        try:
            process = subprocess.run(
                [str(vm_path), str(output_file)],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=20  # Increased timeout for slower programs
            )
            
            # Extract Metrics
            def extract_value(output, pattern):
                try:
                    import re
                    # Try removing ANSI codes first for robustness
                    clean_output = re.sub(r'\x1b\[[0-9;]*m', '', output)
                    for line in clean_output.splitlines():
                        match = re.search(pattern, line)
                        if match:
                             num_str = match.group(1).replace(' ', '')
                             return int(num_str)
                except:
                    pass
                return -1

            exec_cost = extract_value(process.stdout, r'koszt: ([\d ]+)')
            instr_count = extract_value(process.stdout, r'liczba rozkazów: ([\d ]+)')
            
            print(f"\n[METRICS] {test_file.stem}:")
            print(f"  - Exec Cost: My={exec_cost}")
            print(f"  - VM Instr:  My={instr_count}")
            
            # Log the output for debugging
            print(f"\n--- VM Output for {test_file.name} ---")
            print(process.stdout)
            if process.stderr:
                print(f"--- VM Errors for {test_file.name} ---")
                print(process.stderr)
                
            # Check return code
            assert process.returncode == 0, f"VM execution failed with return code {process.returncode}"
            
        except subprocess.TimeoutExpired:
            pytest.fail(f"VM execution timed out for {test_file.name}")
        except Exception as e:
            pytest.fail(f"VM execution error for {test_file.name}: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"]) # -s to show stdout/print statements
