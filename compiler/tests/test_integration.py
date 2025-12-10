import os
import sys
import pytest
from pathlib import Path

# Add src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import lexer
from parser import parser
from semantic_analysis import SemanticAnalyzer
from code_gen import CodeGenerator
from vm import VirtualMachine

def get_test_files():
    """Get all .imp test files from test_files directory"""
    test_files_dir = Path(__file__).parent.parent / 'test_files'
    test_files = sorted(test_files_dir.glob('*.imp'))
    return test_files

def parse_test_spec(file_path):
    """Parse expected inputs and outputs from comments in .imp file"""
    
    # Manual overrides for files without spec comments
    MANUAL_TEST_SPECS = {
        "example1.imp": ([26, 7], [3, 11, 1]),
        "example7.imp": ([0, 0, 0], [31000, 40900, 2222010]),
    }
    
    if file_path.name in MANUAL_TEST_SPECS:
        return MANUAL_TEST_SPECS[file_path.name]

    inputs = []
    outputs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('# ?'):
                inputs.append(int(line.split('?')[1].strip()))
            elif line.startswith('# >'):
                outputs.append(int(line.split('>')[1].strip()))
    return inputs, outputs

class TestIntegration:
    """Integration tests running compiled code on Python VM"""

    @pytest.mark.parametrize("test_file", get_test_files(), ids=lambda f: f.name)
    def test_execution(self, test_file):
        """Compile and run test file, verifying output against spec"""
        
        # 1. Parse spec
        inputs, expected_outputs = parse_test_spec(test_file)
        
        # 2. Compile
        with open(test_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        lexer.input(source_code)
        ast = parser.parse(source_code, lexer=lexer)
        
        analyzer = SemanticAnalyzer()
        symbol_table = analyzer.analyze(ast)
        
        generator = CodeGenerator(symbol_table)
        generator.generate(ast)
        code = generator.get_code()
        
        # 3. Run on VM
        vm = VirtualMachine()
        vm.load_program(code)
        
        try:
            actual_outputs, cost = vm.run(inputs)
        except Exception as e:
            pytest.fail(f"VM Runtime Error in {test_file.name}: {e}")
            
        # 4. Verify
        # If no expected outputs specified, we can't verify correctness, but at least it ran.
        if expected_outputs:
            assert actual_outputs == expected_outputs, f"Output mismatch for {test_file.name}"
            
        print(f"\n{test_file.name}: Cost = {cost} cycles")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
