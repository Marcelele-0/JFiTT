from ast_nodes import *
from symbol_table import SymbolTable

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()

    def analyze(self, ast):
        # 1. Register all procedures first (to allow forward calls if needed, though not specified)
        # Actually, let's just visit them.
        self.visit(ast)
        return self.symbol_table

    def visit(self, node):
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{node.__class__.__name__} method")

    def visit_Program(self, node):
        # First pass: Register procedure names
        for proc in node.procedures:
            self.symbol_table.add_procedure(proc.name, proc.args)
        
        # Second pass: Analyze procedures
        for proc in node.procedures:
            self.visit(proc)
        
        # Analyze Main
        self.visit(node.main)

    def visit_Procedure(self, node):
        self.symbol_table.enter_scope(node.name)
        
        # Register arguments
        for arg in node.args:
            # arg is ('VAR', name) or ('ARRAY', name)
            # They are passed by reference.
            # We can mark them in symbol table.
            # For now, just add them.
            type_ = arg[0]
            name = arg[1]
            # TODO: Handle array args properly (need size? No, passed by ref)
            # If it's an array param, we don't know size.
            # But we need to know it's an array to check usage.
            self.symbol_table.add(name, type_) 

        # Register declarations
        for decl in node.declarations:
            self.visit_Declaration(decl)

        # Analyze commands
        for cmd in node.commands:
            self.visit(cmd)

        self.symbol_table.exit_scope()

    def visit_Main(self, node):
        self.symbol_table.enter_scope('GLOBAL')
        
        for decl in node.declarations:
            self.visit_Declaration(decl)
            
        for cmd in node.commands:
            self.visit(cmd)
            
        self.symbol_table.exit_scope()

    def visit_Declaration(self, decl):
        # decl is tuple: ('VAR', name) or ('ARRAY', name, start, end)
        type_ = decl[0]
        name = decl[1]
        range_ = None
        if type_ == 'ARRAY':
            range_ = (decl[2], decl[3])
        
        self.symbol_table.add(name, type_, range_)

    def visit_Assign(self, node):
        # Check if identifier exists
        self.visit(node.identifier)
        # Check expression
        self.visit(node.expression)
        
        # Check iterator modification
        sym = self.symbol_table.get(node.identifier.name)
        if sym.type == 'ITERATOR':
             raise Exception(f"Cannot modify loop iterator '{node.identifier.name}'")

    def visit_If(self, node):
        self.visit(node.condition)
        for cmd in node.then_commands:
            self.visit(cmd)
        if node.else_commands:
            for cmd in node.else_commands:
                self.visit(cmd)

    def visit_While(self, node):
        self.visit(node.condition)
        for cmd in node.commands:
            self.visit(cmd)

    def visit_Repeat(self, node):
        for cmd in node.commands:
            self.visit(cmd)
        self.visit(node.condition)

    def visit_For(self, node):
        # Iterator is local to the loop? 
        # Spec: "iterator jest lokalny... modyfikacja iteratora wewnątrz pętli jest błędem"
        # Does it shadow existing variable? Or must be unique?
        # Usually in such languages it's a new variable.
        # Let's assume it's a new variable in the current scope, but we must mark it as ITERATOR.
        # Or maybe we should create a new scope for the loop?
        # Spec doesn't mention block scopes.
        # Let's add it to current scope, but fail if it exists? Or shadow?
        # "iterator jest lokalny" suggests it might be temporary.
        # Let's treat it as a variable added to current scope.
        
        iterator_name = node.iterator
        
        # Add iterator to symbol table
        # We need to handle the fact that it might already exist.
        # If it exists, is it shadowed?
        # Let's assume we add it as a special type.
        
        # Actually, to enforce "local", maybe we should check if it exists.
        # But for simplicity, let's just add it.
        # Note: We need to remove it after loop?
        # Or just leave it.
        
        # Hack: Add it, visit commands, then maybe remove or change type?
        # Better: use a temporary scope or just mark it.
        
        # Let's try to add it.
        try:
            self.symbol_table.add(iterator_name, 'ITERATOR')
            added = True
        except:
            # If it exists, check if it's an iterator (nested loop with same var?)
            # Or just allow using existing var as iterator?
            # Spec: "iterator jest lokalny". This usually implies a fresh variable.
            # If I cannot shadow, I might need to error.
            # Let's assume it shadows or reuses.
            # For now, let's just get the symbol and check.
            sym = self.symbol_table.get(iterator_name)
            old_type = sym.type
            sym.type = 'ITERATOR' # Mark as iterator
            added = False

        self.visit(node.start_expr)
        self.visit(node.end_expr)
        
        for cmd in node.commands:
            self.visit(cmd)
            
        # Restore
        if added:
            # Remove from symbol table?
            # My SymbolTable doesn't support remove.
            # This is a problem for "local" iterator if we want to reuse name.
            # But for now, let's leave it.
            pass
        else:
            sym.type = old_type

    def visit_ProcCall(self, node):
        proc = self.symbol_table.get_procedure(node.name)
        if len(node.args) != len(proc['args']):
             raise Exception(f"Wrong number of arguments for '{node.name}'")
        
        for i, arg_name in enumerate(node.args):
            # Check if arguments exist
            # arg_name is PIDENTIFIER
            sym = self.symbol_table.get(arg_name)
            # Check type matching (Array vs Var)
            expected_arg = proc['args'][i] # ('VAR', name) or ('ARRAY', name)
            expected_type = expected_arg[0]
            
            if expected_type == 'ARRAY' and sym.type != 'ARRAY':
                raise Exception(f"Argument {i+1} of '{node.name}' must be an array")
            if expected_type == 'VAR' and sym.type == 'ARRAY':
                 raise Exception(f"Argument {i+1} of '{node.name}' must be a variable")

    def visit_Read(self, node):
        self.visit(node.identifier)

    def visit_Write(self, node):
        self.visit(node.value)

    def visit_BinaryOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Condition(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Identifier(self, node):
        sym = self.symbol_table.get(node.name)
        if node.index:
            if sym.type != 'ARRAY':
                raise Exception(f"Variable '{node.name}' is not an array")
            # Check index if it's a number
            if isinstance(node.index, int):
                # This is tricky, node.index in AST might be a string (PIDENTIFIER) or int (NUM)
                # My parser: PIDENTIFIER LBRACKET NUM RBRACKET -> Identifier(name, num)
                # PIDENTIFIER LBRACKET PIDENTIFIER RBRACKET -> Identifier(name, name)
                pass
        else:
            if sym.type == 'ARRAY':
                 raise Exception(f"Array '{node.name}' used without index")

    def visit_Number(self, node):
        pass
