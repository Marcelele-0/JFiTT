%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define P 1234577

typedef struct {
    long long val;
    char *rpn;
} Data;

int yylex();
void yyerror(const char *s);

/* Deklaracje funkcji */
long long gf_add(long long a, long long b);
long long gf_sub(long long a, long long b);
long long gf_mul(long long a, long long b);
long long gf_div(long long a, long long b);
long long gf_pow(long long base, long long exp);
long long gf_normalize(long long val);
char* concat(char* s1, char* s2, const char* op);
char* num_to_rpn(long long val, long long modulus);

int error_flag = 0;
%}

%union {
    Data data;
}

%token <data> NUM
%token ADD SUB MUL DIV POW L_PAREN R_PAREN EOL ERR

%type <data> expr

%left ADD SUB
%left MUL DIV
%precedence NEG
%nonassoc POW

%%

input:
    /* puste */
    | input line
;

line:
    EOL { }
    | expr EOL {
        if (!error_flag) {
            printf("%s\nWynik: %lld\n", $1.rpn, gf_normalize($1.val));
        }
        if ($1.rpn) free($1.rpn);
        error_flag = 0;
    }
    | error EOL {
        yyerrok;
        error_flag = 0;
    }
;

expr:
    NUM {
        $$ = $1;
    }
    | expr ADD expr {
        $$.val = gf_add($1.val, $3.val);
        $$.rpn = concat($1.rpn, $3.rpn, "+");
        free($1.rpn); free($3.rpn);
    }
    | expr SUB expr {
        $$.val = gf_sub($1.val, $3.val);
        $$.rpn = concat($1.rpn, $3.rpn, "-");
        free($1.rpn); free($3.rpn);
    }
    | expr MUL expr {
        $$.val = gf_mul($1.val, $3.val);
        $$.rpn = concat($1.rpn, $3.rpn, "*");
        free($1.rpn); free($3.rpn);
    }
    | expr DIV expr {
        if (gf_normalize($3.val) == 0) {
            printf("Błąd.\n");
            error_flag = 1;
            $$.val = 0; 
            $$.rpn = strdup("");
        } else {
            $$.val = gf_div($1.val, $3.val);
            $$.rpn = concat($1.rpn, $3.rpn, "/");
        }
        free($1.rpn); free($3.rpn);
    }
    | expr POW expr {
        if (gf_normalize($1.val) == 0 && $3.val < 0) {
             printf("Błąd.\n");
             error_flag = 1;
             $$.val = 0;
             $$.rpn = strdup("");
        } else {
             $$.val = gf_pow($1.val, $3.val);

             char *exp_rpn = $3.rpn;
             int need_free_exp = 0;

             /* KOREKCJA WYKŁADNIKA DLA RPN (modulo P-1) */
             if ($3.val < 0) {
                 exp_rpn = num_to_rpn($3.val, P - 1);
                 need_free_exp = 1;
             }
             
             /* Sprawdzamy też, czy wykładnik nie jest za duży (powyżej P-1)
                i ewentualnie go redukujemy wizualnie, choć zadanie tego wprost nie wymaga,
                ale dla 2^-2 jest to kluczowe. */

             $$.rpn = concat($1.rpn, exp_rpn, "^");
             
             if (need_free_exp) free(exp_rpn);
        }
        free($1.rpn); free($3.rpn);
    }
    | SUB expr %prec NEG {
        $$.val = -$2.val;
        free($2.rpn);
        /* Domyślnie normalizujemy do P. Jeśli to wykładnik, POW to poprawi */
        $$.rpn = num_to_rpn($$.val, P);
    }
    | L_PAREN expr R_PAREN {
        $$ = $2;
    }
;

%%

void yyerror(const char *s) {
    if (!error_flag) {
        printf("Błąd.\n");
        error_flag = 1;
    }
}

int main() {
    return yyparse();
}

/* --- FUNKCJE MATEMATYCZNE --- */

long long gf_normalize(long long n) {
    long long res = n % P;
    if (res < 0) res += P;
    return res;
}

long long gf_add(long long a, long long b) {
    return gf_normalize(a + b);
}

long long gf_sub(long long a, long long b) {
    return gf_normalize(a - b);
}

long long gf_mul(long long a, long long b) {
    return gf_normalize(gf_normalize(a) * gf_normalize(b));
}

long long extended_gcd(long long a, long long b, long long *x, long long *y) {
    if (a == 0) { *x = 0; *y = 1; return b; }
    long long x1, y1;
    long long gcd = extended_gcd(b % a, a, &x1, &y1);
    *x = y1 - (b / a) * x1;
    *y = x1;
    return gcd;
}

long long gf_inv(long long a) {
    long long x, y;
    long long g = extended_gcd(gf_normalize(a), P, &x, &y);
    if (g != 1) return 0;
    return gf_normalize(x);
}

long long gf_div(long long a, long long b) {
    return gf_mul(a, gf_inv(b));
}

long long gf_pow(long long base, long long exp) {
    long long b = gf_normalize(base);
    if (exp < 0) {
        b = gf_inv(b);
        exp = -exp;
    }
    if (exp >= P - 1) exp %= (P - 1);
    
    long long res = 1;
    while (exp > 0) {
        if (exp % 2 == 1) res = gf_mul(res, b);
        b = gf_mul(b, b);
        exp /= 2;
    }
    return res;
}

/* --- FUNKCJE STRING --- */

char* concat(char* s1, char* s2, const char* op) {
    size_t len = strlen(s1) + strlen(s2) + strlen(op) + 3;
    char* res = (char*)malloc(len);
    if (res) sprintf(res, "%s %s %s", s1, s2, op);
    return res;
}

char* num_to_rpn(long long val, long long modulus) {
    long long res = val % modulus;
    if (res < 0) res += modulus;
    char buf[32];
    sprintf(buf, "%lld", res);
    return strdup(buf);
}