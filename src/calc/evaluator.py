"""Evaluator for calculator AST nodes."""

from __future__ import annotations
from enum import Enum, auto
import math
from typing import Any, Optional, Union

from calc.bitops import (
    bit_and,
    bit_or,
    bit_xor,
    bit_not,
    bit_lshift,
    bit_rshift,
    bswap16,
    bswap32,
)
from calc.parser import (
    ASTNode,
    BinaryOpNode,
    ConstantNode,
    FuncCallNode,
    NumberNode,
    Parser,
    UnaryOpNode,
)


class AngleMode(Enum):
    DEG = auto()
    RAD = auto()


class EvaluationError(Exception):
    """Exception raised during AST evaluation."""


# Safety limits
MAX_EXPONENT = 10000
MAX_FACTORIAL_N = 1000


class Evaluator:
    def __init__(
        self,
        angle_mode: AngleMode = AngleMode.DEG,
        variables: Optional[dict[str, Union[int, float]]] = None,
    ):
        self.angle_mode = angle_mode
        self.variables = variables or {}

    def evaluate_expr(self, expr: str) -> Union[int, float]:
        parser = Parser(expr)
        ast = parser.parse()
        return self.evaluate(ast)

    def evaluate(self, node: ASTNode) -> Union[int, float]:
        if isinstance(node, NumberNode):
            return node.value

        if isinstance(node, ConstantNode):
            return self._eval_constant(node.name)

        if isinstance(node, UnaryOpNode):
            return self._eval_unary(node.op, node.operand)

        if isinstance(node, BinaryOpNode):
            return self._eval_binary(node.op, node.left, node.right)

        if isinstance(node, FuncCallNode):
            return self._eval_func(node.name, node.args)

        raise EvaluationError(f"Unsupported node type: {type(node).__name__}")

    def _eval_constant(self, name: str) -> Union[int, float]:
        if self.variables and name in self.variables:
            return self.variables[name]
        if name == "pi":
            return math.pi
        elif name == "e":
            return math.e
        raise EvaluationError(f"Unknown constant or variable: '{name}'")

    def _eval_unary(self, op: str, operand_node: ASTNode) -> Union[int, float]:
        val = self.evaluate(operand_node)
        if op == "+":
            return +val
        elif op == "-":
            return -val
        elif op == "~":
            if not isinstance(val, int):
                raise EvaluationError("Bitwise NOT requires an integer")
            return bit_not(val)
        raise EvaluationError(f"Unknown unary operator: {op}")

    def _eval_binary(self, op: str, left_node: ASTNode, right_node: ASTNode) -> Union[int, float]:
        left = self.evaluate(left_node)
        right = self.evaluate(right_node)

        # Bitwise operators
        if op in ("&", "|", "^", "<<", ">>"):
            if not isinstance(left, int) or not isinstance(right, int):
                raise EvaluationError(f"Bitwise '{op}' requires integer operands")
            try:
                if op == "&":
                    return bit_and(left, right)
                elif op == "|":
                    return bit_or(left, right)
                elif op == "^":
                    return bit_xor(left, right)
                elif op == "<<":
                    return bit_lshift(left, right)
                elif op == ">>":
                    return bit_rshift(left, right)
            except ValueError as e:
                raise EvaluationError(str(e)) from e

        # Arithmetic operators
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            if right == 0:
                raise EvaluationError("Division by zero")
            return left / right
        elif op == "//":
            if right == 0:
                raise EvaluationError("Division by zero")
            return left // right
        elif op == "%":
            if right == 0:
                raise EvaluationError("Division by zero")
            return left % right
        elif op == "**":
            # Safety checks for power
            if isinstance(right, int):
                if abs(right) > MAX_EXPONENT:
                    raise EvaluationError(f"Limit exceeded: exponent exceeds maximum allowed ({MAX_EXPONENT})")
            elif isinstance(right, float):
                if abs(right) > MAX_EXPONENT:
                    raise EvaluationError(f"Limit exceeded: exponent exceeds maximum allowed ({MAX_EXPONENT})")
            try:
                return left ** right
            except OverflowError:
                raise EvaluationError("Calculation overflow")
            except ValueError as e:
                raise EvaluationError(f"Domain error in power: {e}")

        raise EvaluationError(f"Unknown binary operator: {op}")

    def _eval_func(self, name: str, arg_nodes: list[ASTNode]) -> Union[int, float]:
        args = [self.evaluate(a) for a in arg_nodes]

        if name == "sin":
            self._check_arg_count(name, args, 1)
            x = args[0]
            rad = math.radians(x) if self.angle_mode == AngleMode.DEG else x
            val = math.sin(rad)
            return 0.0 if abs(val) < 1e-15 else val

        if name == "cos":
            self._check_arg_count(name, args, 1)
            x = args[0]
            rad = math.radians(x) if self.angle_mode == AngleMode.DEG else x
            val = math.cos(rad)
            return 0.0 if abs(val) < 1e-15 else val

        if name == "tan":
            self._check_arg_count(name, args, 1)
            x = args[0]
            # Check for undefined tan at 90 + 180k degrees
            if self.angle_mode == AngleMode.DEG:
                normalized = (x - 90) % 180
                if abs(normalized) < 1e-12:
                    raise EvaluationError("Domain error: tan is undefined at 90 + 180*k degrees")
            rad = math.radians(x) if self.angle_mode == AngleMode.DEG else x
            val = math.tan(rad)
            return 0.0 if abs(val) < 1e-15 else val

        if name == "asin":
            self._check_arg_count(name, args, 1)
            x = args[0]
            if x < -1.0 or x > 1.0:
                raise EvaluationError("Domain error: asin argument must be in [-1, 1]")
            res = math.asin(x)
            return math.degrees(res) if self.angle_mode == AngleMode.DEG else res

        if name == "acos":
            self._check_arg_count(name, args, 1)
            x = args[0]
            if x < -1.0 or x > 1.0:
                raise EvaluationError("Domain error: acos argument must be in [-1, 1]")
            res = math.acos(x)
            return math.degrees(res) if self.angle_mode == AngleMode.DEG else res

        if name == "atan":
            self._check_arg_count(name, args, 1)
            x = args[0]
            res = math.atan(x)
            return math.degrees(res) if self.angle_mode == AngleMode.DEG else res

        if name == "sqrt":
            self._check_arg_count(name, args, 1)
            x = args[0]
            if x < 0:
                raise EvaluationError("Domain error: sqrt argument must be non-negative")
            # If x is an exact perfect square integer, return int
            if isinstance(x, int):
                root = math.isqrt(x)
                if root * root == x:
                    return root
            return math.sqrt(x)

        if name == "log":
            # Base 10 log per specification
            self._check_arg_count(name, args, 1)
            x = args[0]
            if x <= 0:
                raise EvaluationError("Domain error: log argument must be positive")
            return math.log10(x)

        if name == "ln":
            # Natural log (base e) per specification
            self._check_arg_count(name, args, 1)
            x = args[0]
            if x <= 0:
                raise EvaluationError("Domain error: ln argument must be positive")
            return math.log(x)

        if name == "abs":
            self._check_arg_count(name, args, 1)
            return abs(args[0])

        if name == "factorial":
            self._check_arg_count(name, args, 1)
            x = args[0]
            if not isinstance(x, int):
                raise EvaluationError("Domain error: factorial requires an integer")
            if x < 0:
                raise EvaluationError("Domain error: factorial requires a non-negative integer")
            if x > MAX_FACTORIAL_N:
                raise EvaluationError(f"Limit exceeded: factorial argument exceeds {MAX_FACTORIAL_N}")
            return math.factorial(x)

        if name == "exp":
            self._check_arg_count(name, args, 1)
            try:
                return math.exp(args[0])
            except OverflowError:
                raise EvaluationError("Calculation overflow in exp")

        if name == "bswap16":
            self._check_arg_count(name, args, 1)
            try:
                return bswap16(args[0])
            except ValueError as e:
                raise EvaluationError(str(e)) from e

        if name == "bswap32":
            self._check_arg_count(name, args, 1)
            try:
                return bswap32(args[0])
            except ValueError as e:
                raise EvaluationError(str(e)) from e

        raise EvaluationError(f"Unknown function: '{name}'")

    def _check_arg_count(self, name: str, args: list[Any], expected: int) -> None:
        if len(args) != expected:
            raise EvaluationError(f"Function '{name}' expects {expected} argument(s), got {len(args)}")
