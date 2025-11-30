import sys
import ply.lex as lex
import ply.yacc as yacc

# ==========================================
# KONFIGURACJA MATEMATYCZNA
# ==========================================

P = 1234577

def gf_normalize(n):
    return n % P

def gf_add(a, b):
    return (a + b) % P

def gf_sub(a, b):
    return (a - b) % P

def gf_mul(a, b):
    return (a * b) % P

def gf_pow(base, exp):
    try:
        # Python handles modular inverse for negative exponents automatically
        # if the modulus (P) is provided.
        return pow(base, exp, P)
    except ValueError:
        raise ZeroDivisionError

def gf_div(a, b):
    if b % P == 0:
        raise ZeroDivisionError
    inv = pow(b, P - 2, P)
    return (a * inv) % P

# ==========================================
# LEKSER (LEX)
# ==========================================

tokens = (
    'NUM',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER',
    'LPAREN', 'RPAREN',
)

t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_POWER   = r'\^'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'

t_ignore  = ' \t'

def t_LINE_CONTINUATION(t):
    r'\\\n'
    t.lexer.lineno += 1

def t_COMMENT(t):
    r'\#.*'
    pass

def t_NUM(t):
    r'\d+'
    val = int(t.value)
    # Przechowujemy surową wartość i jej znormalizowaną wersję (mod P)
    t.value = (val, str(gf_normalize(val)))
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    raise SyntaxError

# ==========================================
# PARSER (YACC)
# ==========================================

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
    ('nonassoc', 'POWER'),
)

def p_line(p):
    '''line : expression'''
    if p[1] is not None:
        val, rpn = p[1]
        print(f"{rpn}\nWynik: {gf_normalize(val)}")

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    val1, rpn1 = p[1]
    val3, rpn3 = p[3]
    op = p[2]
    
    try:
        if op == '+':
            res = gf_add(val1, val3)
        elif op == '-':
            res = gf_sub(val1, val3)
        elif op == '*':
            res = gf_mul(val1, val3)
        elif op == '/':
            res = gf_div(val1, val3)
    except ZeroDivisionError:
        print("Błąd.")
        p[0] = None
        return

    new_rpn = f"{rpn1} {rpn3} {op}"
    p[0] = (res, new_rpn)

def p_expression_pow(p):
    '''expression : expression POWER expression'''
    val1, rpn1 = p[1]
    val3, rpn3 = p[3]
    
    try:
        res = gf_pow(val1, val3)
    except ZeroDivisionError:
        print("Błąd.")
        p[0] = None
        return

    # === KLUCZOWA POPRAWKA ===
    # Jeśli wykładnik jest stałą (liczbą), musimy skorygować jego reprezentację RPN.
    # W ciele GF(P) działania na wykładnikach odbywają się modulo P-1.
    # Wcześniej rpn3 był znormalizowany modulo P (domyślnie dla liczb).
    # Tutaj naprawiamy to, normalizując modulo P-1.
    
    # Sprawdzamy, czy rpn3 jest liczbą (wynikiem constant folding lub zwykłym NUM)
    if rpn3.isdigit():
        # Normalizacja wykładnika modulo P-1
        # P-1 = 1234576
        # -2 % 1234576 = 1234574
        corrected_exp = val3 % (P - 1)
        rpn3 = str(corrected_exp)

    new_rpn = f"{rpn1} {rpn3} ^"
    p[0] = (res, new_rpn)

def p_expression_uminus(p):
    'expression : MINUS expression %prec UMINUS'
    val2, rpn2 = p[2]
    
    # Obliczenie wartości (surowej)
    res_val = -val2
    
    # Generowanie RPN domyślnego (modulo P)
    # Dla zwykłych liczb to jest poprawne (np. 1234575 dla -2).
    # Jeśli ta liczba trafi do potęgi, zostanie poprawiona w p_expression_pow.
    res_display = gf_normalize(res_val)
    
    p[0] = (res_val, str(res_display))

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    p[0] = p[2]

def p_expression_number(p):
    'expression : NUM'
    p[0] = p[1]

def p_error(p):
    print("Błąd.")

# ==========================================
# MAIN
# ==========================================

lexer = lex.lex()
parser = yacc.yacc()

if __name__ == "__main__":
    while True:
        try:
            try:
                s = input()
            except EOFError:
                break
            
            while s.endswith('\\'):
                try:
                    s = s[:-1] + input()
                except EOFError:
                    break
            
            if not s.strip() or s.strip().startswith('#'):
                continue

            parser.parse(s + '\n', lexer=lexer)
        except SyntaxError:
            print("Błąd.")
        except Exception:
            print("Błąd.")