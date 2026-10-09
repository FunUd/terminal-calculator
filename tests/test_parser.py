import pytest
from calc.parser import (
    Parser,
    NumberNode,
    BinaryOpNode,
    UnaryOpNode,
    FuncCallNode,
    ConstantNode,
    ParseError,
    tokenize,
    TokenType,
)


def test_tokenize_numbers():
    tokens = tokenize("123 0xFF 0b1010 0o17 3.14 1.2e-3")
    assert tokens[0].type == TokenType.INT and tokens[0].value == 123
    assert tokens[1].type == TokenType.INT and tokens[1].value == 255
    assert tokens[2].type == TokenType.INT and tokens[2].value == 10
    assert tokens[3].type == TokenType.INT and tokens[3].value == 15
    assert tokens[4].type == TokenType.FLOAT and tokens[4].value == 3.14
    assert tokens[5].type == TokenType.FLOAT and tokens[5].value == 0.0012


def test_tokenize_operators_and_punctuation():
    tokens = tokenize("+ - * / // % ** & | ^ ~ << >> ( ) ,")
    ops = [t.value for t in tokens if t.type != TokenType.EOF]
    assert ops == ["+", "-", "*", "/", "//", "%", "**", "&", "|", "^", "~", "<<", ">>", "(", ")", ","]


def test_tokenize_identifiers_and_history_vars():
    tokens = tokenize("ans + h1 * $2")
    names = [t.value for t in tokens if t.type == TokenType.IDENTIFIER]
    assert names == ["ans", "h1", "$2"]



def test_parse_simple_arithmetic():
    parser = Parser("2 + 3 * 4")
    ast = parser.parse()
    # 2 + (3 * 4)
    assert isinstance(ast, BinaryOpNode)
    assert ast.op == "+"
    assert isinstance(ast.left, NumberNode) and ast.left.value == 2
    assert isinstance(ast.right, BinaryOpNode)
    assert ast.right.op == "*"
    assert ast.right.left.value == 3
    assert ast.right.right.value == 4


def test_parse_parentheses():
    parser = Parser("(2 + 3) * 4")
    ast = parser.parse()
    assert isinstance(ast, BinaryOpNode)
    assert ast.op == "*"
    assert isinstance(ast.left, BinaryOpNode)
    assert ast.left.op == "+"


def test_parse_power_right_associative():
    parser = Parser("2 ** 3 ** 2")
    ast = parser.parse()
    # 2 ** (3 ** 2)
    assert isinstance(ast, BinaryOpNode)
    assert ast.op == "**"
    assert ast.left.value == 2
    assert isinstance(ast.right, BinaryOpNode)
    assert ast.right.op == "**"
    assert ast.right.left.value == 3
    assert ast.right.right.value == 2


def test_parse_unary_and_power_precedence():
    # In Python: -2 ** 2 == -(2 ** 2) == -4
    parser = Parser("-2 ** 2")
    ast = parser.parse()
    assert isinstance(ast, UnaryOpNode)
    assert ast.op == "-"
    assert isinstance(ast.operand, BinaryOpNode)
    assert ast.operand.op == "**"


def test_parse_bitwise_precedence():
    # 1 + 2 << 3 & 4 | 5
    # Evaluated as: (((1 + 2) << 3) & 4) | 5
    parser = Parser("1 + 2 << 3 & 4 | 5")
    ast = parser.parse()
    assert isinstance(ast, BinaryOpNode) and ast.op == "|"
    assert isinstance(ast.left, BinaryOpNode) and ast.left.op == "&"
    assert isinstance(ast.left.left, BinaryOpNode) and ast.left.left.op == "<<"
    assert isinstance(ast.left.left.left, BinaryOpNode) and ast.left.left.left.op == "+"


def test_parse_functions_and_constants():
    parser = Parser("sin(pi / 2) + sqrt(16)")
    ast = parser.parse()
    assert isinstance(ast, BinaryOpNode)
    assert ast.op == "+"
    assert isinstance(ast.left, FuncCallNode)
    assert ast.left.name == "sin"
    assert len(ast.left.args) == 1
    assert isinstance(ast.left.args[0], BinaryOpNode)
    assert isinstance(ast.left.args[0].left, ConstantNode)
    assert ast.left.args[0].left.name == "pi"


def test_parse_errors():
    with pytest.raises(ParseError):
        Parser("2 +").parse()

    with pytest.raises(ParseError):
        Parser("(2 + 3").parse()

    with pytest.raises(ParseError):
        Parser("2 + * 3").parse()

    with pytest.raises(ParseError):
        Parser("").parse()


# ---------------------------------------------------------------------------
# SI prefix tests
# ---------------------------------------------------------------------------

def test_tokenize_si_prefix_integers():
    """Integer × large multiplier → INT token."""
    tokens = tokenize("1k")
    assert tokens[0].type == TokenType.INT and tokens[0].value == 1000

    tokens = tokenize("1K")
    assert tokens[0].type == TokenType.INT and tokens[0].value == 1000

    tokens = tokenize("1M")
    assert tokens[0].type == TokenType.INT and tokens[0].value == 1_000_000

    tokens = tokenize("1G")
    assert tokens[0].type == TokenType.INT and tokens[0].value == 1_000_000_000


def test_tokenize_si_prefix_small():
    """Integer × small multiplier → FLOAT token."""
    tokens = tokenize("10u")
    assert tokens[0].type == TokenType.FLOAT
    assert tokens[0].value == pytest.approx(1e-5)

    tokens = tokenize("100n")
    assert tokens[0].type == TokenType.FLOAT
    assert tokens[0].value == pytest.approx(1e-7)

    tokens = tokenize("1m")
    assert tokens[0].type == TokenType.FLOAT
    assert tokens[0].value == pytest.approx(1e-3)

    tokens = tokenize("1p")
    assert tokens[0].type == TokenType.FLOAT
    assert tokens[0].value == pytest.approx(1e-12)


def test_tokenize_si_prefix_float():
    """Float literal × multiplier → FLOAT token."""
    tokens = tokenize("1.5k")
    assert tokens[0].type == TokenType.FLOAT
    assert tokens[0].value == pytest.approx(1500.0)

    tokens = tokenize("2.2M")
    assert tokens[0].type == TokenType.FLOAT
    assert tokens[0].value == pytest.approx(2_200_000.0)


def test_si_prefix_in_expression():
    """10k * 2 evaluates to 20000."""
    from calc.evaluator import Evaluator
    ev = Evaluator()
    assert ev.evaluate_expr("10k * 2") == 20000
    assert ev.evaluate_expr("1.5M / 100") == pytest.approx(15000.0)


def test_si_prefix_no_collision():
    """Bare identifier 'k' (without a leading number) is an IDENTIFIER, not a SI prefix."""
    tokens = tokenize("k")
    assert tokens[0].type == TokenType.IDENTIFIER and tokens[0].value == "k"


def test_si_prefix_case_sensitive():
    """'m' (milli, ×1e-3) and 'M' (mega, ×1e6) must be distinct."""
    tokens_m = tokenize("1m")
    assert tokens_m[0].type == TokenType.FLOAT
    assert tokens_m[0].value == pytest.approx(1e-3)

    tokens_M = tokenize("1M")
    assert tokens_M[0].type == TokenType.INT
    assert tokens_M[0].value == 1_000_000
