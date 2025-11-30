all: calc

calc: calc.l calc.y
	bison -d calc.y
	lex calc.l
	gcc -o calc calc.tab.c lex.yy.c -lm

clean:
	rm -f calc calc.tab.c calc.tab.h lex.yy.c