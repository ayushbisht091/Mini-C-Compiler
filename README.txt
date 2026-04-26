STEPS TO RUN:

1. Install tools:
   - flex (or win_flex)
   - bison (or win_bison)
   - gcc (MinGW)

2. Compile compiler:
   yacc -d parser.y
   lex lexer.l
   gcc lex.yy.c y.tab.c -o compiler

   (On Windows it creates compiler.exe)

3. Run Flask:
   pip install flask
   python app.py

4. Open browser:
   http://127.0.0.1:5000

INPUT EXAMPLE:
a = b + c * d;

OUTPUT:
t1 = c * d
t2 = b + t1
a = t2
