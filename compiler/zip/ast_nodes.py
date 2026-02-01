class Node:
    pass

class Program(Node):
    def __init__(self, procedures, main):
        self.procedures = procedures
        self.main = main
    def __repr__(self):
        return f"Program({self.procedures}, {self.main})"

class Procedure(Node):
    def __init__(self, name, args, declarations, commands):
        self.name = name
        self.args = args
        self.declarations = declarations
        self.commands = commands
    def __repr__(self):
        return f"Procedure({self.name}, {self.args}, {self.declarations}, {self.commands})"

class Main(Node):
    def __init__(self, declarations, commands):
        self.declarations = declarations
        self.commands = commands
    def __repr__(self):
        return f"Main({self.declarations}, {self.commands})"

class Command(Node):
    pass

class Assign(Command):
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression
    def __repr__(self):
        return f"Assign({self.identifier}, {self.expression})"

class If(Command):
    def __init__(self, condition, then_commands, else_commands=None):
        self.condition = condition
        self.then_commands = then_commands
        self.else_commands = else_commands
    def __repr__(self):
        return f"If({self.condition}, {self.then_commands}, {self.else_commands})"

class While(Command):
    def __init__(self, condition, commands):
        self.condition = condition
        self.commands = commands
    def __repr__(self):
        return f"While({self.condition}, {self.commands})"

class Repeat(Command):
    def __init__(self, commands, condition):
        self.commands = commands
        self.condition = condition
    def __repr__(self):
        return f"Repeat({self.commands}, {self.condition})"

class For(Command):
    def __init__(self, iterator, start_expr, end_expr, down_to, commands):
        self.iterator = iterator
        self.start_expr = start_expr
        self.end_expr = end_expr
        self.down_to = down_to # Boolean: True if DOWNTO
        self.commands = commands
    def __repr__(self):
        return f"For({self.iterator}, {self.start_expr}, {self.end_expr}, {self.down_to}, {self.commands})"

class ProcCall(Command):
    def __init__(self, name, args):
        self.name = name
        self.args = args
    def __repr__(self):
        return f"ProcCall({self.name}, {self.args})"

class Read(Command):
    def __init__(self, identifier):
        self.identifier = identifier
    def __repr__(self):
        return f"Read({self.identifier})"

class Write(Command):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Write({self.value})"

class Expression(Node):
    pass

class BinaryOp(Expression):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    def __repr__(self):
        return f"BinaryOp({self.left}, '{self.op}', {self.right})"

class Number(Expression):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Number({self.value})"

class Identifier(Expression):
    def __init__(self, name, index=None):
        self.name = name
        self.index = index # For array access: name[index]
    def __repr__(self):
        return f"Identifier({self.name}, {self.index})"

class Condition(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    def __repr__(self):
        return f"Condition({self.left}, '{self.op}', {self.right})"
