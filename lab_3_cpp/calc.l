%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "calc.tab.h"

/* P = 1234577 */
#define P 1234577

/* Funkcja pomocnicza do normalizacji wyświetlania w RPN */
void create_number_token(long long val);

/* Ręczna obsługa numeru linii dla klasycznego lexa (opcjonalne, ale bezpieczne) */
int my_lineno = 1;
%}

%%

^#.*\n      { /* Ignoruj komentarz na początku linii */ my_lineno++; return 0; }
[ \t]+#.* { /* Ignoruj komentarz na końcu linii */ }

\\\n        { /* Ignoruj kontynuację linii */ my_lineno++; }
[ \t]+      { /* Ignoruj białe znaki */ }

[0-9]+      {
                long long val = atoll(yytext);
                create_number_token(val);
                return NUM;
            }

"+"         { return ADD; }
"-"         { return SUB; }
"*"         { return MUL; }
"/"         { return DIV; }
"^"         { return POW; }
"("         { return L_PAREN; }
")"         { return R_PAREN; }
\n          { my_lineno++; return EOL; }

.           { return ERR; }

%%

/* W klasycznym LEX-ie musimy sami zdefiniować tę funkcję */
int yywrap(void) {
    return 1;
}

void create_number_token(long long val) {
    yylval.data.val = val;
    
    long long norm = val % P;
    if (norm < 0) norm += P;
    
    char buf[32];
    sprintf(buf, "%lld", norm);
    yylval.data.rpn = strdup(buf);
}