"""Tokenizer and AST Parser for expression evaluation."""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
import re
from typing import Any, Union


class TokenType(Enum):
    INT = auto()
    FLOAT = auto()
    IDENTIFIER = auto()
    OP = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: Any
    pos: int


class ParseError(Exception):
    def __init__(self, message: str, pos: int = 0):
        super().__init__(f"Parse error at position {pos}: {message}")
        self.message = message
        self.pos = pos


# AST Node definitions
@dataclass
class NumberNode:
    value: Union[int, float]


@dataclass
class ConstantNode:
    name: str


@dataclass
class UnaryOpNode:
    op: str
    operand: Any


@dataclass
class BinaryOpNode:
    op: str
    left: Any
    right: Any


@dataclass
class FuncCallNode:
    name: str
    args: list[Any]


ASTNode = Union[NumberNode, ConstantNode, UnaryOpNode, BinaryOpNode, FuncCallNode]


SI_MULTIPLIERS: dict[str, float] = {
    "k": 1e3,
    "K": 1e3,
    "M": 1e6,
    "G": 1e9,
    "m": 1e-3,
    "u": 1e-6,
    "n": 1e-9,
    "p": 1e-12,
}

TOKEN_SPEC = [
    ("HEX",    r"0[xX][0-9a-fA-F_]+"),
    ("BIN",    r"0[bB][01_]+"),
    ("OCT",    r"0[oO][0-7_]+"),
    # SI_NUM must come before FLOAT/INT so "1.5M" and "1k" are captured as one token
    ("SI_NUM", r"(?:\d+\.\d*|\.\d+|\d[\d_]*)(?:[kKMGmunp])"),
    ("FLOAT",  r"(?:\d+\.\d*|\.\d+)(?:[eE][+-]?\d+)?|\d+[eE][+-]?\d+"),
    ("INT",    r"\d[\d_]*"),
    ("OP_MULTI", r"\*\*|//|<<|>>"),
    ("OP_SINGLE", r"[+\-*/%&|^~]"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("IDENT", r"(?:\$|[a-zA-Z_])[a-zA-Z0-9_]*"),
    ("WS", r"\s+"),
]

MASTER_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))


def tokenize(expr: str) -> list[Token]:
    tokens: list[Token] = []
    pos = 0
    length = len(expr)

    while pos < length:
        match = MASTER_RE.match(expr, pos)
        if not match:
            raise ParseError(f"Unexpected character '{expr[pos]}'", pos)

        kind = match.lastgroup
        text = match.group()
        start = pos
        pos = match.end()

        if kind == "WS":
            continue
        elif kind == "HEX":
            clean_text = text.replace("_", "")
            tokens.append(Token(TokenType.INT, int(clean_text, 16), start))
        elif kind == "BIN":
            clean_text = text.replace("_", "")
            tokens.append(Token(TokenType.INT, int(clean_text, 2), start))
        elif kind == "OCT":
            clean_text = text.replace("_", "")
            tokens.append(Token(TokenType.INT, int(clean_text, 8), start))
        elif kind == "SI_NUM":
            suffix = text[-1]
            num_str = text[:-1].replace("_", "")
            multiplier = SI_MULTIPLIERS[suffix]
            if "." in num_str:
                tokens.append(Token(TokenType.FLOAT, float(num_str) * multiplier, start))
            else:
                raw = int(num_str) * multiplier
                if raw == int(raw):
                    tokens.append(Token(TokenType.INT, int(raw), start))
                else:
                    tokens.append(Token(TokenType.FLOAT, raw, start))
        elif kind == "FLOAT":
            tokens.append(Token(TokenType.FLOAT, float(text), start))
        elif kind == "INT":
            clean_text = text.replace("_", "")
            tokens.append(Token(TokenType.INT, int(clean_text, 10), start))
        elif kind in ("OP_MULTI", "OP_SINGLE"):
            tokens.append(Token(TokenType.OP, text, start))
        elif kind == "LPAREN":
            tokens.append(Token(TokenType.LPAREN, text, start))
        elif kind == "RPAREN":
            tokens.append(Token(TokenType.RPAREN, text, start))
        elif kind == "COMMA":
            tokens.append(Token(TokenType.COMMA, text, start))
        elif kind == "IDENT":
            tokens.append(Token(TokenType.IDENTIFIER, text, start))

    tokens.append(Token(TokenType.EOF, None, pos))
    return tokens


class Parser:
    """Recursive descent parser implementing Python-like operator precedence."""

    def __init__(self, expr: str):
        self.expr = expr
        self.tokens = tokenize(expr)
        self.current_idx = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.current_idx]

    def advance(self) -> Token:
        tok = self.current
        if tok.type != TokenType.EOF:
            self.current_idx += 1
        return tok

    def match(self, token_type: TokenType, value: Any = None) -> bool:
        if self.current.type == token_type:
            if value is None or self.current.value == value:
                self.advance()
                return True
        return False

    def expect(self, token_type: TokenType, value: Any = None) -> Token:
        tok = self.current
        if tok.type != token_type or (value is not None and tok.value != value):
            expected_desc = f"{token_type.name}" + (f" ('{value}')" if value else "")
            raise ParseError(f"Expected {expected_desc}, got '{tok.value}'", tok.pos)
        return self.advance()

    def parse(self) -> ASTNode:
        if self.current.type == TokenType.EOF:
            raise ParseError("Empty expression", 0)
        node = self.expr_or()
        if self.current.type != TokenType.EOF:
            raise ParseError(f"Unexpected token '{self.current.value}'", self.current.pos)
        return node

    # Precedence hierarchy:
    # 1. bitwise OR: |
    # 2. bitwise XOR: ^
    # 3. bitwise AND: &
    # 4. shift: <<, >>
    # 5. add/sub: +, -
    # 6. mul/div/floordiv/mod: *, /, //, %
    # 7. unary: +, -, ~
    # 8. power: ** (right-associative)
    # 9. primary: literal, ident, call, (expr)

    def expr_or(self) -> ASTNode:
        left = self.expr_xor()
        while self.match(TokenType.OP, "|"):
            right = self.expr_xor()
            left = BinaryOpNode("|", left, right)
        return left

    def expr_xor(self) -> ASTNode:
        left = self.expr_and()
        while self.match(TokenType.OP, "^"):
            right = self.expr_and()
            left = BinaryOpNode("^", left, right)
        return left

    def expr_and(self) -> ASTNode:
        left = self.expr_shift()
        while self.match(TokenType.OP, "&"):
            right = self.expr_shift()
            left = BinaryOpNode("&", left, right)
        return left

    def expr_shift(self) -> ASTNode:
        left = self.expr_add()
        while True:
            if self.match(TokenType.OP, "<<"):
                right = self.expr_add()
                left = BinaryOpNode("<<", left, right)
            elif self.match(TokenType.OP, ">>"):
                right = self.expr_add()
                left = BinaryOpNode(">>", left, right)
            else:
                break
        return left

    def expr_add(self) -> ASTNode:
        left = self.expr_mul()
        while True:
            if self.match(TokenType.OP, "+"):
                right = self.expr_mul()
                left = BinaryOpNode("+", left, right)
            elif self.match(TokenType.OP, "-"):
                right = self.expr_mul()
                left = BinaryOpNode("-", left, right)
            else:
                break
        return left

    def expr_mul(self) -> ASTNode:
        left = self.expr_unary()
        while True:
            if self.match(TokenType.OP, "*"):
                right = self.expr_unary()
                left = BinaryOpNode("*", left, right)
            elif self.match(TokenType.OP, "/"):
                right = self.expr_unary()
                left = BinaryOpNode("/", left, right)
            elif self.match(TokenType.OP, "//"):
                right = self.expr_unary()
                left = BinaryOpNode("//", left, right)
            elif self.match(TokenType.OP, "%"):
                right = self.expr_unary()
                left = BinaryOpNode("%", left, right)
            else:
                break
        return left

    def expr_unary(self) -> ASTNode:
        if self.match(TokenType.OP, "+"):
            return UnaryOpNode("+", self.expr_unary())
        if self.match(TokenType.OP, "-"):
            return UnaryOpNode("-", self.expr_unary())
        if self.match(TokenType.OP, "~"):
            return UnaryOpNode("~", self.expr_unary())
        return self.expr_power()

    def expr_power(self) -> ASTNode:
        left = self.expr_primary()
        if self.match(TokenType.OP, "**"):
            # Right-associative: power can be followed by a unary expression (e.g. 2 ** -3 or 2 ** 3 ** 2)
            right = self.expr_unary()
            return BinaryOpNode("**", left, right)
        return left

    def expr_primary(self) -> ASTNode:
        tok = self.current
        if tok.type in (TokenType.INT, TokenType.FLOAT):
            self.advance()
            return NumberNode(tok.value)

        if tok.type == TokenType.LPAREN:
            self.advance()
            node = self.expr_or()
            self.expect(TokenType.RPAREN, ")")
            return node

        if tok.type == TokenType.IDENTIFIER:
            name = tok.value
            self.advance()
            if self.match(TokenType.LPAREN, "("):
                args: list[ASTNode] = []
                if not self.match(TokenType.RPAREN, ")"):
                    while True:
                        args.append(self.expr_or())
                        if self.match(TokenType.COMMA, ","):
                            continue
                        self.expect(TokenType.RPAREN, ")")
                        break
                return FuncCallNode(name, args)
            return ConstantNode(name)

        raise ParseError(f"Unexpected token '{tok.value}'", tok.pos)
