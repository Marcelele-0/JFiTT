import pytest
import subprocess
import os
import sys
import re
from pathlib import Path

# Add src directory to the path so we can import compiler modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from lexer import lexer
from parser import parser
from semantic_analysis import SemanticAnalyzer
from code_gen import CodeGenerator

def get_vm_path():
    """Get path to the virtual machine executable"""
    vm_path = Path(__file__).parent.parent / 'virtual_machine' / 'maszyna-wirtualna'
    if not vm_path.exists():
        pytest.skip("Virtual machine executable not found")
    return vm_path

class TestSpecificOutputs:
    """Test suite for verifying specific outputs of compiled programs"""

    def compile_file(self, source_path, output_path):
        """Helper to compile a source file to an output path"""
        with open(source_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
            
        lexer.input(source_code)
        ast = parser.parse(source_code, lexer=lexer)
        assert ast is not None, f"Parsing failed for {source_path}"
        
        analyzer = SemanticAnalyzer()
        symbol_table = analyzer.analyze(ast)
        
        generator = CodeGenerator(symbol_table)
        generator.generate(ast)
        code = generator.get_code()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(code)

    def parse_vm_output(self, stdout):
        """
        Parses VM output to extract printed values.
        Handles lines that may be prefixed with input prompts '? '.
        Examples:
        '> 123'
        '? > 123'
        '? ? > 123'
        """
        values = []
        for line in stdout.splitlines():
            line = line.strip()
            # Match '> ' optionally preceded by any number of '? ' patterns
            match = re.search(r'(?:\? )*> (-?\d+)', line)
            if match:
                try:
                    values.append(int(match.group(1)))
                except ValueError:
                    pass
        return values


    def test_example0_binary_conversion(self):
        """
        Test example0.imp which converts number to binary (LSB first).
        Input: 13
        Expected Output: 1, 0, 1, 1
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example0.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        # Prepare outputs dir
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example0_test.mr'

        # Compile
        self.compile_file(test_file, output_mr)

        # Run VM
        vm_path = get_vm_path()
        input_val = "13\n"
        
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_val,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"\n--- VM Output ---\n{process.stdout}")
            if process.stderr:
                print(f"--- VM Errors ---\n{process.stderr}")

            assert process.returncode == 0, "VM execution failed"

            # Parse and verify output
            outputs = self.parse_vm_output(process.stdout)
            
            # 13 in binary is 1101.
            # The program prints LSB first: 1, 0, 1, 1
            expected = [1, 0, 1, 1]
            
            assert outputs == expected, f"Expected outputs {expected}, got {outputs}"

        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")


    def test_example1_euclidean(self):
        """
        Test example1.imp which uses Diophantine equation/Euclidean algorithm.
        Input: 26, 7
        Expected Output: 3, 11, 1
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example1.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        # Prepare outputs dir
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example1_test.mr'

        # Compile
        self.compile_file(test_file, output_mr)

        # Run VM
        vm_path = get_vm_path()
        input_val = "26\n7\n"
        
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_val,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"\n--- VM Output ---\n{process.stdout}")
            if process.stderr:
                print(f"--- VM Errors ---\n{process.stderr}")

            assert process.returncode == 0, "VM execution failed"

            # Parse and verify output
            outputs = self.parse_vm_output(process.stdout)
            
            # Expected outputs: x=3, y=11, nwd=1
            expected = [3, 11, 1]
            
            assert outputs == expected, f"Expected outputs {expected}, got {outputs}"

        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")


    def test_example2_fibonacci_procedures(self):
        """
        Test example2.imp which uses nested procedures to calculate Fibonacci numbers.
        Input: 0, 1
        Expected Output: 46368, 28657
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example2.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        # Prepare outputs dir
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example2_test.mr'

        # Compile
        self.compile_file(test_file, output_mr)

        # Run VM
        vm_path = get_vm_path()
        input_val = "0\n1\n"
        
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_val,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"\n--- VM Output ---\n{process.stdout}")
            if process.stderr:
                print(f"--- VM Errors ---\n{process.stderr}")

            assert process.returncode == 0, "VM execution failed"

            # Parse and verify output
            outputs = self.parse_vm_output(process.stdout)
            
            # Expected outputs from comments in example2.imp
            expected = [46368, 28657]
            
            assert outputs == expected, f"Expected outputs {expected}, got {outputs}"

        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")


    def test_example3_many_variables(self):
        """
        Test example3.imp which uses many variables to calculate Fibonacci numbers.
        Input: 1
        Expected Output: 121393
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example3.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        # Prepare outputs dir
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example3_test.mr'

        # Compile
        self.compile_file(test_file, output_mr)

        # Run VM
        vm_path = get_vm_path()
        input_val = "1\n"
        
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_val,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"\n--- VM Output ---\n{process.stdout}")
            if process.stderr:
                print(f"--- VM Errors ---\n{process.stderr}")

            assert process.returncode == 0, "VM execution failed"

            # Parse and verify output
            outputs = self.parse_vm_output(process.stdout)
            
            # Expected outputs from comments in example3.imp
            expected = [121393]
            
            assert outputs == expected, f"Expected outputs {expected}, got {outputs}"

        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")

    def test_example4_combinations(self):
        """
        Test example4.imp which calculates Combinations C(n,k).
        Input: 20, 9
        Expected Output: 167960
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example4.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        # Prepare outputs dir
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example4_test.mr'

        # Compile
        self.compile_file(test_file, output_mr)

        # Run VM
        vm_path = get_vm_path()
        input_val = "20\n9\n"
        
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_val,
                capture_output=True,
                text=True,
                timeout=60  # Increased timeout for computationally intensive example4
            )
            
            print(f"\n--- VM Output ---\n{process.stdout}")
            if process.stderr:
                print(f"--- VM Errors ---\n{process.stderr}")

            assert process.returncode == 0, "VM execution failed"

            # Parse and verify output
            outputs = self.parse_vm_output(process.stdout)
            
            # Expected output: 167960
            expected = [167960]
            
            assert outputs == expected, f"Expected outputs {expected}, got {outputs}"

        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")

            assert outputs == expected, f"Expected outputs {expected}, got {outputs}"

        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")

    def test_example5_mod_pow(self):
        """
        Test example5.imp (Modular Exponentiation).
        Input: 1234567890
               1234567890987654321
               987654321
        Output: 674106858
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example5.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        input_str = "1234567890\n1234567890987654321\n987654321\n"
        expected = [674106858]

        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example5_test.mr'

        self.compile_file(test_file, output_mr)
        
        vm_path = get_vm_path()
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=20
            )
            assert process.returncode == 0, "VM execution failed"
            outputs = self.parse_vm_output(process.stdout)
            assert outputs == expected, f"Expected {expected}, got {outputs}"
        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")

    def test_example6_factorial_fibonacci(self):
        """
        Test example6.imp (Factorial + Fibonacci).
        Input: 20
        Output: 
        20! = 2432902008176640000
        F_20 = 6765
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example6.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        input_str = "20\n"
        expected = [2432902008176640000, 6765]

        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example6_test.mr'

        self.compile_file(test_file, output_mr)
        
        vm_path = get_vm_path()
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=30 # Factorial might be heavy?
            )
            assert process.returncode == 0, "VM execution failed"
            outputs = self.parse_vm_output(process.stdout)
            assert outputs == expected, f"Expected {expected}, got {outputs}"
        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")

    def test_example7_nested_loops(self):
        """
        Test example7.imp (Nested Loops).
        Two cases from comments.
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example7.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example7_test.mr'
        self.compile_file(test_file, output_mr)
        vm_path = get_vm_path()

        # Case 1
        input_str1 = "0\n0\n0\n"
        expected1 = [31000, 40900, 2222010]
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_str1,
                capture_output=True,
                text=True,
                timeout=30
            )
            assert process.returncode == 0
            outputs = self.parse_vm_output(process.stdout)
            assert outputs == expected1, f"Case 1: Expected {expected1}, got {outputs}"
        except subprocess.TimeoutExpired:
            pytest.fail("Case 1 timed out")

        # Case 2
        input_str2 = "1\n0\n2\n"
        expected2 = [31001, 40900, 2222012]
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_str2,
                capture_output=True,
                text=True,
                timeout=30
            )
            assert process.returncode == 0
            outputs = self.parse_vm_output(process.stdout)
            assert outputs == expected2, f"Case 2: Expected {expected2}, got {outputs}"
        except subprocess.TimeoutExpired:
            pytest.fail("Case 2 timed out")


    def test_example8_sort(self):
        """
        Test example8.imp which performs insertion sort.
        No input.
        Output:
        1. Shuffled numbers (generated by PRNG logic in shuffle procedure)
        2. Separator 1234567890
        3. Sorted numbers 0..22 (except for 0 which is at t[23])
        Wait, let's analyze logic:
        shuffle(t, 23):
          q=5, w=1
          for i from 1 to 23:
            w = (w * 5) % 23
            t[i] = w
          t[23] = 0
        
        So t[1]..t[22] are permuted 1..22. t[23] = 0.
        Then write(t, 23).
        Then separator.
        Then sort(t, 23).
        Then write(t, 23).
        
        Sorted: 0, 1, 2... 22?
        Wait, sort runs for i FROM 2 TO n.
        Let's reproduce expected output in python.
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example8.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")

        # Emulate shuffle logic to get expected first part of output
        n = 23
        t = [0] * (n + 1) # 1-indexed
        q = 5
        w = 1
        expected_shuffle = []
        for i in range(1, n + 1):
            w = (w * q) % n
            t[i] = w
            if i < n: # The loop in IMP goes 1 TO n, setting t[i]
                pass 
        t[n] = 0 # Explicitly set last to 0
        
        # In the IMP loop 'FOR i FROM 1 TO n DO ... t[i]:=w ENDFOR'
        # Then 't[n]:=0' overwrites the last one.
        # Let's run exact logic:
        w = 1
        t_sim = [0] * (n + 1)
        for i in range(1, n + 1):
            w = (w * 5) % 23
            t_sim[i] = w
        t_sim[n] = 0
        
        expected_shuffle = t_sim[1:]
        
        expected_sorted = sorted(expected_shuffle)
        
        expected_full = expected_shuffle + [1234567890] + expected_sorted

        # Prepare outputs dir
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example8_test.mr'

        # Compile
        self.compile_file(test_file, output_mr)

        # Run VM
        vm_path = get_vm_path()
        # No input expected
        
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                capture_output=True,
                text=True,
                timeout=20 # Sorting might take a bit
            )
            
            print(f"\n--- VM Output ---\n{process.stdout}")
            if process.stderr:
                print(f"--- VM Errors ---\n{process.stderr}")

            assert process.returncode == 0, "VM execution failed"

            # Parse and verify output
            outputs = self.parse_vm_output(process.stdout)
            
            assert outputs == expected_full, f"Expected outputs {expected_full}, got {outputs}"

        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")

    def test_example9_bc(self):
        """
        Test example9.imp (Binomial Coefficient).
        Inputs: n=20, k=9
        Expected Output: 167960
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'example9.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")
    
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'example9_test.mr'
        self.compile_file(test_file, output_mr)
        
        input_str = "20\n9\n"
        expected = [167960]
        
        vm_path = get_vm_path()
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                input=input_str,
                capture_output=True,
                text=True,
                timeout=10
            )
            assert process.returncode == 0
            outputs = self.parse_vm_output(process.stdout)
            assert outputs == expected, f"Expected {expected}, got {outputs}"
        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")

    def test_exampleA_downto(self):
        """
        Test exampleA.imp (FOR DOWNTO and Arrays).
        Calculates tc[i] = (i+1) * (25-i) for i in 0..24
        """
        test_file = Path(__file__).parent.parent / 'test_files' / 'exampleA.imp'
        if not test_file.exists():
             pytest.fail(f"Test file {test_file} not found")
    
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_mr = outputs_dir / 'exampleA_test.mr'
        self.compile_file(test_file, output_mr)
        
        # Calculate expected output python side
        expected = []
        for i in range(0, 25):
            val = (i + 1) * (25 - i)
            expected.append(val)
            
        vm_path = get_vm_path()
        try:
            process = subprocess.run(
                [str(vm_path), str(output_mr)],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert process.returncode == 0
            outputs = self.parse_vm_output(process.stdout)
            assert outputs == expected, f"Expected {expected}, got {outputs}"
        except subprocess.TimeoutExpired:
            pytest.fail("VM execution timed out")
