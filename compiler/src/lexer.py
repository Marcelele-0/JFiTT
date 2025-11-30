import ply.lex as lex
import sys

tokens = (
    'NUM', 'PIDENTIFIER',
    'PLUS', 'MINUS', 'TIMES', 'DIV', 'MOD',
    'ASSIGN', 'EQ', 'NEQ', 'LEQ', 'GEQ', 'LT', 'GT',
    'IF', 'THEN', 'ELSE', 'ENDIF',
    'WHILE', 'DO', 'ENDWHILE',
    'REPEAT', 'UNTIL',
    'FOR', 'FROM', 'TO', 'DOWNTO', 'ENDFOR',
    'READ', 'WRITE',
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET',
    'COLON', 'SEMICOLON', 'COMMA',
    'PROCEDURE', 'IS', 'IN', 'END', 'PROGRAM',
    'T' 
)

reserved = {
    'IF': 'IF', 'THEN': 'THEN', 'ELSE': 'ELSE', 'ENDIF': 'ENDIF',
    'WHILE': 'WHILE', 'DO': 'DO', 'ENDWHILE': 'ENDWHILE',
    'REPEAT': 'REPEAT', 'UNTIL': 'UNTIL',
    'FOR': 'FOR', 'FROM': 'FROM', 'TO': 'TO', 'DOWNTO': 'DOWNTO', 'ENDFOR': 'ENDFOR',
    'READ': 'READ', 'WRITE': 'WRITE',
    'PROCEDURE': 'PROCEDURE', 'IS': 'IS', 'IN': 'IN', 'END': 'END',
    'PROGRAM': 'PROGRAM',
    'T': 'T'
}

def t_PIDENTIFIER(t):
    r'[_a-zA-Z]+'
    t.type = reserved.get(t.value, 'PIDENTIFIER')
    return t

def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIV     = r'/'
t_MOD     = r'%'
t_ASSIGN  = r':='
t_EQ      = r'='
t_NEQ     = r'!='
t_LEQ     = r'<='
t_GEQ     = r'>='
t_LT      = r'<'
t_GT      = r'>'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COLON   = r':'
t_SEMICOLON = r';'
t_COMMA   = r','

def t_COMMENT(t):
    r'\#.*'
    pass

t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Nierozpoznany znak '{t.value[0]}' w linii {t.lineno}")
    t.lexer.skip(1)
    sys.exit(1)

lexer = lex.lex()
