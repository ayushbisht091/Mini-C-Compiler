%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int temp_count = 1;
int label_count = 1;
int label_stack[256];
int label_stack_top = 0;

char* new_temp() {
    char *temp = malloc(10);
    sprintf(temp, "t%d", temp_count++);
    return temp;
}

int new_label() {
    return label_count++;
}

void push_label(int l) {
    if (label_stack_top < 256) label_stack[label_stack_top++] = l;
}

int pop_label() {
    if (label_stack_top > 0) return label_stack[--label_stack_top];
    return -1;
}

int peek_label() {
    if (label_stack_top > 0) return label_stack[label_stack_top - 1];
    return -1;
}

int yylex();
void yyerror(const char *s);
%}

%union {
    int num;
    char* id;
}

%token <num> NUMBER
%token <id> ID
%token INT WHILE IF ELSE
%token PLUS MUL MINUS ASSIGN SEMI
%token GT LT
%token LPAREN RPAREN LBRACE RBRACE

%type <id> expr cond

%left PLUS MINUS
%left MUL

%nonassoc IF_NO_ELSE
%nonassoc ELSE

%%

program: stmts ;

stmts:
    stmts stmt
    |
    ;

block:
    LBRACE stmts RBRACE {
        /* stmts already emitted output while parsing */
    }
    ;

stmt:
    INT ID ASSIGN expr SEMI {
        printf("%s = %s\n", $2, $4);
    }
    |
    ID ASSIGN expr SEMI {
        printf("%s = %s\n", $1, $3);
    }
    |
    while_stmt
    |
    if_stmt
    ;

while_stmt:
    WHILE
    {
        $<num>$ = new_label();
        printf("L%d:\n", $<num>$);
    }
    LPAREN cond RPAREN
    {
        $<num>$ = new_label();
        printf("ifFalse %s goto L%d\n", $4, $<num>$);
    }
    block
    {
        printf("goto L%d\n", $<num>2);
        printf("L%d:\n", $<num>6);
    }
    ;

if_stmt:
    IF LPAREN cond RPAREN
    {
        int elseLabel = new_label();
        int endLabel = new_label();
        push_label(endLabel);
        $<num>$ = elseLabel;
        printf("ifFalse %s goto L%d\n", $3, elseLabel);
    }
    block
    {
        int endLabel = peek_label();
        printf("goto L%d\n", endLabel);
        printf("L%d:\n", $<num>5);
    }
    opt_else
    {
        int endLabel = pop_label();
        printf("L%d:\n", endLabel);
    }
    ;

opt_else:
    /* empty */ %prec IF_NO_ELSE
    |
    ELSE block
    ;

cond:
    ID GT NUMBER {
        $$ = malloc(50);
        sprintf($$, "%s > %d", $1, $3);
    }
    |
    ID LT NUMBER {
        $$ = malloc(50);
        sprintf($$, "%s < %d", $1, $3);
    }
;

expr:
    expr PLUS expr {
        char* t = new_temp();
        printf("%s = %s + %s\n", t, $1, $3);
        $$ = t;
    }
    |
    expr MUL expr {
        char* t = new_temp();
        printf("%s = %s * %s\n", t, $1, $3);
        $$ = t;
    }
    |
    expr MINUS expr {
        char* t = new_temp();
        printf("%s = %s - %s\n", t, $1, $3);
        $$ = t;
    }
    |
    LPAREN expr RPAREN {   // 🔥 THIS WAS MISSING
        $$ = $2;
    }
    |
    ID { $$ = $1; }
    |
    NUMBER {
        char* t = malloc(10);
        sprintf(t, "%d", $1);
        $$ = t;
    }
    ;

%%

int main() {
    yyparse();
    return 0;
}

void yyerror(const char *s) {
    printf("Error: %s\n", s);
}