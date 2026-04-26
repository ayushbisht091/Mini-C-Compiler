%{
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int temp_count = 1;
int label_count = 1;

char* new_temp() {
    char *temp = malloc(10);
    sprintf(temp, "t%d", temp_count++);
    return temp;
}

char* new_label() {
    char *lab = malloc(10);
    sprintf(lab, "L%d", label_count++);
    return lab;
}

static char* sdup(const char* s) {
    if (!s) return NULL;
    char* out = (char*)malloc(strlen(s) + 1);
    strcpy(out, s);
    return out;
}

static char* str3(const char* a, const char* b, const char* c) {
    size_t la = a ? strlen(a) : 0;
    size_t lb = b ? strlen(b) : 0;
    size_t lc = c ? strlen(c) : 0;
    char* out = (char*)malloc(la + lb + lc + 1);
    out[0] = '\0';
    if (a) strcat(out, a);
    if (b) strcat(out, b);
    if (c) strcat(out, c);
    return out;
}

static char* str4(const char* a, const char* b, const char* c, const char* d) {
    char* ab = str3(a, b, NULL);
    char* cd = str3(c, d, NULL);
    char* out = str3(ab, cd, NULL);
    free(ab);
    free(cd);
    return out;
}

typedef struct {
    char* code;   // emitted TAC lines (each ends with \n)
    char* place;  // variable/temp name or condition string
} Node;

int yylex();
void yyerror(const char *s);
%}

%union {
    int num;
    char* id;
    Node node;
}

%token <num> NUMBER
%token <id> ID
%token INT IF ELSE WHILE
%token PLUS MUL MINUS ASSIGN SEMI
%token GT
%token LPAREN RPAREN LBRACE RBRACE

%type <id> program
%type <id> stmts
%type <id> stmt
%type <node> expr cond

%%

program:
    stmts { printf("%s", $1 ? $1 : ""); }
    ;

stmts:
    stmts stmt { $$ = str3($1 ? $1 : "", $2 ? $2 : "", NULL); }
    |
    /* empty */ { $$ = sdup(""); }
    ;

stmt:
    INT ID SEMI {
        // declaration without init -> no TAC needed
        $$ = sdup("");
    }
    |
    INT ID ASSIGN expr SEMI {
        // int x = expr;
        char buf[256];
        snprintf(buf, sizeof(buf), "%s = %s\n", $2, $4.place);
        $$ = str3($4.code ? $4.code : "", buf, NULL);
    }
    |
    ID ASSIGN expr SEMI {
        // x = expr;
        char buf[256];
        snprintf(buf, sizeof(buf), "%s = %s\n", $1, $3.place);
        $$ = str3($3.code ? $3.code : "", buf, NULL);
    }
    |
    WHILE LPAREN cond RPAREN LBRACE stmts RBRACE {
        // while (cond) { stmts }
        char* Lstart = new_label();
        char* Lend = new_label();
        char head[256];
        char jf[512];
        snprintf(head, sizeof(head), "%s:\n", Lstart);
        snprintf(jf, sizeof(jf), "ifFalse %s goto %s\n", $3.place, Lend);
        char tail[256];
        snprintf(tail, sizeof(tail), "goto %s\n%s:\n", Lstart, Lend);
        $$ = str4(head, $3.code ? $3.code : "", jf, NULL);
        {
            char* mid = str3($$, $6 ? $6 : "", NULL);
            free($$);
            $$ = str3(mid, tail, NULL);
            free(mid);
        }
    }
    |
    IF LPAREN cond RPAREN LBRACE stmts RBRACE {
        // if (cond) { stmts }
        char* Lend = new_label();
        char jf[512];
        snprintf(jf, sizeof(jf), "ifFalse %s goto %s\n", $3.place, Lend);
        char lab[256];
        snprintf(lab, sizeof(lab), "%s:\n", Lend);
        $$ = str3($3.code ? $3.code : "", jf, NULL);
        {
            char* mid = str3($$, $6 ? $6 : "", NULL);
            free($$);
            $$ = str3(mid, lab, NULL);
            free(mid);
        }
    }
    |
    IF LPAREN cond RPAREN LBRACE stmts RBRACE ELSE LBRACE stmts RBRACE {
        // if (cond) { stmts } else { stmts }
        char* Lelse = new_label();
        char* Lend = new_label();
        char jf[512];
        snprintf(jf, sizeof(jf), "ifFalse %s goto %s\n", $3.place, Lelse);
        char jend[256];
        snprintf(jend, sizeof(jend), "goto %s\n", Lend);
        char lel[256];
        snprintf(lel, sizeof(lel), "%s:\n", Lelse);
        char lend[256];
        snprintf(lend, sizeof(lend), "%s:\n", Lend);
        $$ = str3($3.code ? $3.code : "", jf, NULL);
        {
            char* mid1 = str3($$, $6 ? $6 : "", NULL);
            free($$);
            char* mid2 = str4(mid1, jend, lel, NULL);
            free(mid1);
            char* mid3 = str3(mid2, $10 ? $10 : "", NULL);
            free(mid2);
            $$ = str3(mid3, lend, NULL);
            free(mid3);
        }
    }
    ;

cond:
    ID GT NUMBER {
        char buf[128];
        snprintf(buf, sizeof(buf), "%s > %d", $1, $3);
        $$.code = sdup("");
        $$.place = sdup(buf);
    }
    ;

expr:
    expr PLUS expr {
        char* t = new_temp();
        char line[256];
        snprintf(line, sizeof(line), "%s = %s + %s\n", t, $1.place, $3.place);
        char* code = str3($1.code ? $1.code : "", $3.code ? $3.code : "", line);
        $$.code = code;
        $$.place = t;
    }
    |
    expr MUL expr {
        char* t = new_temp();
        char line[256];
        snprintf(line, sizeof(line), "%s = %s * %s\n", t, $1.place, $3.place);
        char* code = str3($1.code ? $1.code : "", $3.code ? $3.code : "", line);
        $$.code = code;
        $$.place = t;
    }
    |
    expr MINUS expr {
        char* t = new_temp();
        char line[256];
        snprintf(line, sizeof(line), "%s = %s - %s\n", t, $1.place, $3.place);
        char* code = str3($1.code ? $1.code : "", $3.code ? $3.code : "", line);
        $$.code = code;
        $$.place = t;
    }
    |
    LPAREN expr RPAREN {
        $$.code = $2.code;
        $$.place = $2.place;
    }
    |
    ID {
        $$.code = sdup("");
        $$.place = $1;
    }
    |
    NUMBER {
        char buf[32];
        snprintf(buf, sizeof(buf), "%d", $1);
        $$.code = sdup("");
        $$.place = sdup(buf);
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