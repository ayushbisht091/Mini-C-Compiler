import json
import re
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    pos: int


_TOKEN_SPECS: List[Tuple[str, str]] = [
    ("WHITESPACE", r"[ \t\r\n]+"),
    ("IF", r"\bif\b"),
    ("ELSE", r"\belse\b"),
    ("INT", r"\bint\b"),
    ("WHILE", r"\bwhile\b"),
    ("NUMBER", r"\b\d+\b"),
    ("ID", r"\b[a-zA-Z_][a-zA-Z0-9_]*\b"),
    ("GE", r">="),
    ("LE", r"<="),
    ("EQ", r"=="),
    ("NE", r"!="),
    ("GT", r">"),
    ("LT", r"<"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("MUL", r"\*"),
    ("DIV", r"/"),
    ("ASSIGN", r"="),
    ("SEMI", r";"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
]

_MASTER_RE = re.compile("|".join(f"(?P<{name}>{pat})" for name, pat in _TOKEN_SPECS))


def tokenize(code: str) -> List[Token]:
    tokens: List[Token] = []
    i = 0
    n = len(code)
    while i < n:
        m = _MASTER_RE.match(code, i)
        if not m:
            tokens.append(Token("UNKNOWN", code[i], i))
            i += 1
            continue
        typ = m.lastgroup or "UNKNOWN"
        val = m.group(typ)
        if typ != "WHITESPACE":
            tokens.append(Token(typ, val, i))
        i = m.end()
    tokens.append(Token("EOF", "", n))
    return tokens


class ParseError(Exception):
    pass


def _node(kind: str, value: Optional[str] = None, children: Optional[List[Any]] = None) -> dict:
    return {"kind": kind, "value": value, "children": children or []}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> Token:
        return self.tokens[self.i]

    def accept(self, t: str) -> Optional[Token]:
        if self.peek().type == t:
            tok = self.peek()
            self.i += 1
            return tok
        return None

    def expect(self, t: str) -> Token:
        tok = self.accept(t)
        if not tok:
            got = self.peek()
            raise ParseError(f"Expected {t}, got {got.type} at {got.pos}")
        return tok

    # Grammar (subset):
    # program  -> stmt* EOF
    # stmt     -> decl_assign | assign | if_stmt | while_stmt
    # decl_assign -> INT ID ASSIGN expr SEMI
    # assign   -> ID ASSIGN expr SEMI
    # if_stmt  -> IF LPAREN cond RPAREN block (ELSE block)?
    # while_stmt -> WHILE LPAREN cond RPAREN block
    # block    -> LBRACE stmt* RBRACE
    # cond     -> expr (GT|LT|GE|LE|EQ|NE) expr
    # expr     -> term ((PLUS|MINUS) term)*
    # term     -> factor ((MUL|DIV) factor)*
    # factor   -> NUMBER | ID | LPAREN expr RPAREN

    def parse_program(self) -> dict:
        stmts = []
        while self.peek().type not in ("EOF", "RBRACE"):
            stmts.append(self.parse_stmt())
        self.expect("EOF")
        return _node("Program", children=stmts)

    def parse_block(self) -> dict:
        self.expect("LBRACE")
        stmts = []
        while self.peek().type != "RBRACE":
            stmts.append(self.parse_stmt())
        self.expect("RBRACE")
        return _node("Block", children=stmts)

    def parse_stmt(self) -> dict:
        if self.peek().type == "INT":
            self.expect("INT")
            ident = self.expect("ID").value
            self.expect("ASSIGN")
            expr = self.parse_expr()
            self.expect("SEMI")
            return _node("DeclAssign", value=ident, children=[expr])

        if self.peek().type == "IF":
            return self.parse_if()

        if self.peek().type == "WHILE":
            return self.parse_while()

        # assignment
        ident = self.expect("ID").value
        self.expect("ASSIGN")
        expr = self.parse_expr()
        self.expect("SEMI")
        return _node("Assign", value=ident, children=[expr])

    def parse_if(self) -> dict:
        self.expect("IF")
        self.expect("LPAREN")
        cond = self.parse_cond()
        self.expect("RPAREN")
        then_block = _node("Then", children=[self.parse_block()])
        else_block = None
        if self.accept("ELSE"):
            else_block = _node("Else", children=[self.parse_block()])
        children = [cond, then_block] + ([else_block] if else_block else [])
        return _node("If", children=children)

    def parse_while(self) -> dict:
        self.expect("WHILE")
        self.expect("LPAREN")
        cond = self.parse_cond()
        self.expect("RPAREN")
        body = self.parse_block()
        return _node("While", children=[cond, body])

    def parse_cond(self) -> dict:
        left = self.parse_expr()
        op_tok = self.peek()
        if op_tok.type not in ("GT", "LT", "GE", "LE", "EQ", "NE"):
            raise ParseError(f"Expected comparison operator at {op_tok.pos}")
        self.i += 1
        right = self.parse_expr()
        # Store both token type and literal to make it unambiguous in UI
        op_val = op_tok.value or ""
        return _node("Cond", value=f"{op_tok.type}({op_val})", children=[left, right])

    def parse_expr(self) -> dict:
        node = self.parse_term()
        while self.peek().type in ("PLUS", "MINUS"):
            op = self.peek().value
            self.i += 1
            rhs = self.parse_term()
            node = _node("BinOp", value=op, children=[node, rhs])
        return node

    def parse_term(self) -> dict:
        node = self.parse_factor()
        while self.peek().type in ("MUL", "DIV"):
            op = self.peek().value
            self.i += 1
            rhs = self.parse_factor()
            node = _node("BinOp", value=op, children=[node, rhs])
        return node

    def parse_factor(self) -> dict:
        if self.peek().type == "NUMBER":
            return _node("Number", value=self.expect("NUMBER").value)
        if self.peek().type == "ID":
            return _node("Id", value=self.expect("ID").value)
        if self.accept("LPAREN"):
            inner = self.parse_expr()
            self.expect("RPAREN")
            return _node("Paren", children=[inner])
        tok = self.peek()
        raise ParseError(f"Unexpected token {tok.type} at {tok.pos}")


def tokens_pretty(tokens: List[Token]) -> str:
    out = []
    for t in tokens:
        if t.type == "EOF":
            break
        out.append(f"{t.type:<10}  {t.value!r}  @ {t.pos}")
    return "\n".join(out).strip()


def tree_to_steps(ast: dict) -> str:
    """
    Returns JSON string:
    { nodes: [{id, kind, value, parentId}], order: [ids...] }
    order is BFS so it "rains" top-down.
    """
    nodes = []
    order = []
    q: List[Tuple[dict, Optional[int]]] = [(ast, None)]
    next_id = 1

    # BFS: assign ids in visitation order
    while q:
        cur, parent = q.pop(0)
        cur_id = next_id
        next_id += 1
        nodes.append(
            {
                "id": cur_id,
                "kind": cur.get("kind"),
                "value": cur.get("value"),
                "parentId": parent,
            }
        )
        order.append(cur_id)
        for ch in cur.get("children", []) or []:
            if ch is None:
                continue
            q.append((ch, cur_id))

    return json.dumps({"nodes": nodes, "order": order})


def analyze(code: str) -> Tuple[str, str, str]:
    toks = tokenize(code or "")
    lex = tokens_pretty(toks)
    try:
        ast = Parser(toks).parse_program()
        tree_json = tree_to_steps(ast)
        msg = ""
    except ParseError as e:
        tree_json = tree_to_steps(_node("ParseError", value=str(e)))
        msg = str(e)
    return lex, tree_json, msg

