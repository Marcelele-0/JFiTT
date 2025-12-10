"""
Tests for the compiler - validates compilation of all test files
"""

import os
import sys
import tempfile
import pytest
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
    test_files = sorted(test_files_dir.glob('*.imp'))
    return test_files


class TestCompiler:
    """Test suite for the compiler"""

    @pytest.mark.parametrize("test_file", get_test_files(), ids=lambda f: f.name)
    def test_compilation(self, test_file):
        """Test that a source file can be successfully compiled"""
        
        # Read the source file
        with open(test_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Create output file path in tests/outputs directory
        outputs_dir = Path(__file__).parent / 'outputs'
        outputs_dir.mkdir(exist_ok=True)
        output_filename = test_file.stem + '.out'
        output_file = outputs_dir / output_filename
        
        # Lexical analysis
        lexer.input(source_code)
        
        # Parse
        ast = parser.parse(source_code, lexer=lexer)
        assert ast is not None, f"Parsing failed for {test_file.name}"
        
        # Semantic analysis
        try:
            analyzer = SemanticAnalyzer()
            symbol_table = analyzer.analyze(ast)
            assert symbol_table is not None, f"Semantic analysis failed for {test_file.name}"
        except Exception as e:
            pytest.fail(f"Semantic analysis error in {test_file.name}: {type(e).__name__}: {e}")
        
        # Code generation
        try:
            generator = CodeGenerator(symbol_table)
            generator.generate(ast)
            code = generator.get_code()
            assert code is not None, f"Code generation failed for {test_file.name}"
            assert len(code) > 0, f"Generated code is empty for {test_file.name}"
        except Exception as e:
            pytest.fail(f"Code generation error in {test_file.name}: {type(e).__name__}: {e}")
        
        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Verify output file was created and has content
        assert os.path.exists(output_file), f"Output file was not created for {test_file.name}"
        assert os.path.getsize(output_file) > 0, f"Output file is empty for {test_file.name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
