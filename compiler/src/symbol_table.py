class Symbol:
    def __init__(self, name, address, type, scope, array_range=None, is_initialized=False):
        self.name = name
        self.address = address
        self.type = type # 'VAR', 'ARRAY', 'ITERATOR'
        self.scope = scope # 'GLOBAL' or procedure name
        self.array_range = array_range # (start, end) for arrays
        self.is_initialized = is_initialized
    
    def __repr__(self):
        return f"Symbol({self.name}, addr={self.address}, type={self.type}, scope={self.scope})"

class SymbolTable:
    def __init__(self):
        self.scopes = {'GLOBAL': {}}
        self.procedures = {} # name -> {args: [], ...}
        self.memory_counter = 20 # Start after scratchpad (0-19)
        self.current_scope = 'GLOBAL'

    def add_procedure(self, name, args):
        if name in self.procedures:
            raise Exception(f"Redeclaration of procedure '{name}'")
        self.procedures[name] = {'args': args}

    def get_procedure(self, name):
        if name not in self.procedures:
            raise Exception(f"Undeclared procedure '{name}'")
        return self.procedures[name]

    def enter_scope(self, scope_name):
        if scope_name not in self.scopes:
            self.scopes[scope_name] = {}
        self.current_scope = scope_name

    def exit_scope(self):
        self.current_scope = 'GLOBAL'

    def add(self, name, type, array_range=None):
        scope_dict = self.scopes[self.current_scope]
        if name in scope_dict:
            raise Exception(f"Redeclaration of variable '{name}' in scope '{self.current_scope}'")
        
        size = 1
        if type == 'ARRAY':
            if array_range is not None:
                start, end = array_range
                if start > end:
                    raise Exception(f"Invalid array range for '{name}': {start} > {end}")
                size = end - start + 1
            else:
                # Array parameter (pointer), size unknown but treated as 1 (pointer size)
                pass
        
        address = self.memory_counter
        self.memory_counter += size
        
        sym = Symbol(name, address, type, self.current_scope, array_range)
        scope_dict[name] = sym
        return sym

    def get(self, name):
        # If in a procedure, look in local scope ONLY (unless we decide otherwise, but report says strict)
        # Report: "zmienne używane w procedurze muszą być jej parametrami formalnymi lub być zadeklarowane wewnątrz procedury"
        # So we ONLY look in current_scope.
        
        scope_dict = self.scopes[self.current_scope]
        if name in scope_dict:
            return scope_dict[name]
        
        # If we are in GLOBAL scope, obviously look there.
        # If we are in a procedure, we DO NOT look in GLOBAL.
        
        raise Exception(f"Undeclared variable '{name}' in scope '{self.current_scope}'")

    def get_all_in_scope(self, scope_name):
        return self.scopes.get(scope_name, {})
