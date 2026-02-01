import ply.yacc as yacc
from lexer import tokens
from ast_nodes import *

# Precedence rules
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIV', 'MOD'),
)

def p_program(p):
    '''program_all : procedures main'''
    p[0] = Program(p[1], p[2])

def p_procedures(p):
    '''procedures : procedures PROCEDURE proc_head IS declarations IN commands END
                  | procedures PROCEDURE proc_head IS IN commands END
                  | empty'''
    if len(p) == 2: # empty
        p[0] = []
    else:
        if len(p) == 9: # with declarations
            proc = Procedure(p[3]['name'], p[3]['args'], p[5], p[7])
        else: # without declarations (len=8)
            proc = Procedure(p[3]['name'], p[3]['args'], [], p[6])
        p[0] = p[1] + [proc]

def p_proc_head(p):
    '''proc_head : PIDENTIFIER LPAREN args_decl RPAREN'''
    p[0] = {'name': p[1], 'args': p[3]}

def p_args_decl(p):
    '''args_decl : args_decl COMMA type PIDENTIFIER
                 | type PIDENTIFIER
                 | empty'''
    if len(p) == 2: # empty
        p[0] = []
    elif len(p) == 3: # type PIDENTIFIER
        p[0] = [(p[1], p[2])]
    elif len(p) == 5: # args_decl COMMA type PIDENTIFIER
        p[0] = p[1] + [(p[3], p[4])]

def p_type(p):
    '''type : T
            | I
            | O
            | empty'''
    if p[1] is None:
        p[0] = 'VAR' # Default type (IN-OUT)
    elif p[1] == 'T':
        p[0] = 'ARRAY'
    elif p[1] == 'I':
        p[0] = 'CONST' # Read-only
    elif p[1] == 'O':
        p[0] = 'OUT' # Write-first


def p_main(p):
    '''main : PROGRAM IS declarations IN commands END
            | PROGRAM IS IN commands END'''
    if len(p) == 7:
        p[0] = Main(p[3], p[5])
    else:
        p[0] = Main([], p[4])

def p_declarations(p):
    '''declarations : declarations COMMA PIDENTIFIER
                    | declarations COMMA PIDENTIFIER LBRACKET NUM COLON NUM RBRACKET
                    | PIDENTIFIER
                    | PIDENTIFIER LBRACKET NUM COLON NUM RBRACKET'''
    if len(p) == 2: # PIDENTIFIER
        p[0] = [('VAR', p[1])]
    elif len(p) == 4: # declarations COMMA PIDENTIFIER
        p[0] = p[1] + [('VAR', p[3])]
    elif len(p) == 7: # PIDENTIFIER [ N : N ]
        p[0] = [('ARRAY', p[1], p[3], p[5])]
    elif len(p) == 9: # declarations COMMA PIDENTIFIER [ N : N ]
        p[0] = p[1] + [('ARRAY', p[3], p[5], p[7])]

def p_commands(p):
    '''commands : commands command
                | command'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_command_assign(p):
    '''command : identifier ASSIGN expression SEMICOLON'''
    p[0] = Assign(p[1], p[3])

def p_command_if(p):
    '''command : IF condition THEN commands ELSE commands ENDIF
               | IF condition THEN commands ENDIF'''
    if len(p) == 8:
        p[0] = If(p[2], p[4], p[6])
    else:
        p[0] = If(p[2], p[4])

def p_command_while(p):
    '''command : WHILE condition DO commands ENDWHILE'''
    p[0] = While(p[2], p[4])

def p_command_repeat(p):
    '''command : REPEAT commands UNTIL condition SEMICOLON'''
    p[0] = Repeat(p[2], p[4])

def p_command_for(p):
    '''command : FOR PIDENTIFIER FROM value TO value DO commands ENDFOR
               | FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR'''
    down_to = (p[5] == 'DOWNTO')
    p[0] = For(p[2], p[4], p[6], down_to, p[8])

def p_command_proc_call(p):
    '''command : proc_call SEMICOLON'''
    p[0] = p[1]

def p_command_io(p):
    '''command : READ identifier SEMICOLON
               | WRITE value SEMICOLON'''
    if p[1] == 'READ':
        p[0] = Read(p[2])
    else:
        p[0] = Write(p[2])

def p_proc_call(p):
    '''proc_call : PIDENTIFIER LPAREN args RPAREN'''
    p[0] = ProcCall(p[1], p[3])

def p_args(p):
    '''args : args COMMA PIDENTIFIER
            | PIDENTIFIER'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_expression_binop(p):
    '''expression : value PLUS value
                  | value MINUS value
                  | value TIMES value
                  | value DIV value
                  | value MOD value'''
    p[0] = BinaryOp(p[1], p[2], p[3])

def p_expression_value(p):
    '''expression : value'''
    p[0] = p[1]

def p_condition(p):
    '''condition : value EQ value
                 | value NEQ value
                 | value LT value
                 | value GT value
                 | value LEQ value
                 | value GEQ value'''
    p[0] = Condition(p[1], p[2], p[3])

def p_value(p):
    '''value : NUM
             | identifier'''
    if isinstance(p[1], int):
        p[0] = Number(p[1])
    else:
        p[0] = p[1] # identifier is already an Identifier node

def p_identifier(p):
    '''identifier : PIDENTIFIER
                  | PIDENTIFIER LBRACKET PIDENTIFIER RBRACKET
                  | PIDENTIFIER LBRACKET NUM RBRACKET'''
    if len(p) == 2:
        p[0] = Identifier(p[1])
    else:
        p[0] = Identifier(p[1], p[3])

def p_empty(p):
    '''empty :'''
    pass

def p_error(p):
    if p:
        print(f"Błąd składniowy przy tokenie '{p.value}' w linii {p.lineno}")
    else:
        print("Błąd składniowy na końcu pliku")

parser = yacc.yacc()
