# Mini C Compiler 🚀

A simple compiler that converts C code into:
- Python Code
- Three Address Code (3AC)
- Lexical Analysis
- Parse Tree

---

## 🔧 Features
- Lexical Analyzer (Flex)
- Syntax Parser (Bison)
- Intermediate Code Generation (3AC)
- Parse Tree Visualization
- C to Python Conversion

---

## 🛠 Technologies Used
- C (Flex & Bison)
- Python (Flask)
- HTML, CSS

---

## ▶️ How to Run

### Step 1: Compile
```bash
win_flex lexer.l
win_bison -d parser.y
gcc lex.yy.c parser.tab.c -o compiler
