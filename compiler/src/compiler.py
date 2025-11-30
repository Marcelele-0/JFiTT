import sys
from lexer import lexer
from parser import parser

def main():
    if len(sys.argv) != 3:
        print("Usage: python compiler.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        with open(input_file, 'r') as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    # Lexer
    lexer.input(data)
    # for tok in lexer:
    #     print(tok)

    # Parser
    ast = parser.parse(data, lexer=lexer)
    
    if ast:
        print("Parsing successful!")
        # print(ast)
        
        from semantic_analysis import SemanticAnalyzer
        try:
            analyzer = SemanticAnalyzer()
            symbol_table = analyzer.analyze(ast)
            print("Semantic analysis successful!")
            
            # Code Generation
            from code_gen import CodeGenerator
            generator = CodeGenerator(symbol_table)
            generator.generate(ast)
            with open(output_file, 'w') as f:
                f.write(generator.get_code())
            print(f"Compilation successful! Output written to {output_file}")
        except Exception as e:
            print(f"Semantic error: {e}")
            sys.exit(1)
    else:
        print("Parsing failed.")

if __name__ == "__main__":
    main()
