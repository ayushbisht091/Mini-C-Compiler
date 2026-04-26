%{
#include "parser.tab.h"
#include <stdlib.h>
#include <string.h>
%}

%%
"int"      { return INT; }
"if"       { return IF; }
"else"     { return ELSE; }
"while"    { return WHILE; }

">"        { return GT; }
"+"        { return PLUS; }
"-"        { return MINUS; }
"*"        { return MUL; }
"="        { return ASSIGN; }
";"        { return SEMI; }

"("        { return LPAREN; }
")"        { return RPAREN; }
"{"        { return LBRACE; }
"}"        { return RBRACE; }

[0-9]+     { yylval.num = atoi(yytext); return NUMBER; }
[a-zA-Z_][a-zA-Z0-9_]* { yylval.id = strdup(yytext); return ID; }

[ \t\n]    ;
.          ;
%%

int yywrap() { return 1; }