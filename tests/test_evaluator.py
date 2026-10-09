import math
import pytest
from calc.evaluator import Evaluator, AngleMode, EvaluationError


def test_basic_arithmetic():
    ev = Evaluator()
    assert ev.evaluate_expr("2 + 3 * 4") == 14
    assert ev.evaluate_expr("(2 + 3) * 4") == 20
    assert ev.evaluate_expr("10 - 3 - 2") == 5
    assert ev.evaluate_expr("2 ** 3 ** 2") == 512
    assert ev.evaluate_expr("-2 ** 2") == -4
    assert ev.evaluate_expr("(-2) ** 2") == 4
    assert ev.evaluate_expr("7 // 3") == 2
    assert ev.evaluate_expr("7 % 3") == 1
    assert ev.evaluate_expr("7 / 2") == 3.5


def test_arbitrary_precision_integer():
    ev = Evaluator()
    huge = 10**50
    assert ev.evaluate_expr(f"{huge} + 1") == huge + 1
    assert ev.evaluate_expr("0xFFFFFFFF + 1") == 4294967296


def test_bitwise_operations():
    ev = Evaluator()
    assert ev.evaluate_expr("0xFF & 0x0F") == 0x0F
    assert ev.evaluate_expr("0xF0 | 0x0F") == 0xFF
    assert ev.evaluate_expr("0xFF ^ 0x0F") == 0xF0
    assert ev.evaluate_expr("~0") == 0xFFFFFFFF
    assert ev.evaluate_expr("0x80000000 >> 1") == 0x40000000
    assert ev.evaluate_expr("1 << 4") == 16


def test_bitwise_errors():
    ev = Evaluator()
    with pytest.raises(EvaluationError, match="integer"):
        ev.evaluate_expr("3.14 & 1")

    with pytest.raises(EvaluationError, match="Shift amount"):
        ev.evaluate_expr("1 << 32")


def test_division_by_zero():
    ev = Evaluator()
    with pytest.raises(EvaluationError, match="Division by zero"):
        ev.evaluate_expr("1 / 0")

    with pytest.raises(EvaluationError, match="Division by zero"):
        ev.evaluate_expr("1 // 0")

    with pytest.raises(EvaluationError, match="Division by zero"):
        ev.evaluate_expr("1 % 0")


def test_functions_and_constants_deg():
    ev = Evaluator(angle_mode=AngleMode.DEG)
    assert pytest.approx(ev.evaluate_expr("sin(30)"), abs=1e-9) == 0.5
    assert pytest.approx(ev.evaluate_expr("cos(60)"), abs=1e-9) == 0.5
    assert pytest.approx(ev.evaluate_expr("sin(90)"), abs=1e-9) == 1.0
    assert pytest.approx(ev.evaluate_expr("cos(90)"), abs=1e-9) == 0.0
    assert pytest.approx(ev.evaluate_expr("tan(45)"), abs=1e-9) == 1.0
    assert pytest.approx(ev.evaluate_expr("asin(0.5)"), abs=1e-9) == 30.0
    assert pytest.approx(ev.evaluate_expr("acos(0.5)"), abs=1e-9) == 60.0
    assert pytest.approx(ev.evaluate_expr("atan(1)"), abs=1e-9) == 45.0

    # sqrt with integer return for perfect squares
    assert ev.evaluate_expr("sqrt(16)") == 4
    assert pytest.approx(ev.evaluate_expr("sqrt(2)"), abs=1e-9) == math.sqrt(2)

    # log (base 10) and ln (base e)
    assert pytest.approx(ev.evaluate_expr("log(100)"), abs=1e-9) == 2.0
    assert pytest.approx(ev.evaluate_expr("ln(e)"), abs=1e-9) == 1.0

    # abs and factorial
    assert ev.evaluate_expr("abs(-42)") == 42
    assert ev.evaluate_expr("factorial(5)") == 120
    assert ev.evaluate_expr("factorial(0)") == 1

    # spec example
    assert ev.evaluate_expr("sqrt(16) + 0x10") == 20


def test_functions_rad():
    ev = Evaluator(angle_mode=AngleMode.RAD)
    assert pytest.approx(ev.evaluate_expr("sin(pi / 6)"), abs=1e-9) == 0.5
    assert pytest.approx(ev.evaluate_expr("cos(pi / 3)"), abs=1e-9) == 0.5


def test_domain_and_safety_limits():
    ev = Evaluator()
    with pytest.raises(EvaluationError, match="Domain error"):
        ev.evaluate_expr("sqrt(-1)")

    with pytest.raises(EvaluationError, match="Domain error"):
        ev.evaluate_expr("log(0)")

    with pytest.raises(EvaluationError, match="Domain error"):
        ev.evaluate_expr("factorial(-1)")

    with pytest.raises(EvaluationError, match="Domain error"):
        ev.evaluate_expr("factorial(3.5)")

    with pytest.raises(EvaluationError, match="Limit exceeded"):
        ev.evaluate_expr("factorial(1001)")

    with pytest.raises(EvaluationError, match="Limit exceeded"):
        ev.evaluate_expr("2 ** 10001")

    with pytest.raises(EvaluationError, match="Unknown function"):
        ev.evaluate_expr("unknown_func(1)")

    with pytest.raises(EvaluationError, match="Unknown constant"):
        ev.evaluate_expr("foo + 1")


def test_bswap16_integration():
    ev = Evaluator()
    assert ev.evaluate_expr("bswap16(0x1234)") == 0x3412
    assert ev.evaluate_expr("bswap16(0x0000)") == 0x0000
    assert ev.evaluate_expr("bswap16(0xFFFF)") == 0xFFFF
    assert ev.evaluate_expr("bswap16(0x00FF)") == 0xFF00

    with pytest.raises(EvaluationError):
        ev.evaluate_expr("bswap16(-1)")

    with pytest.raises(EvaluationError):
        ev.evaluate_expr("bswap16(3.14)")


def test_bswap32_integration():
    ev = Evaluator()
    assert ev.evaluate_expr("bswap32(0x12345678)") == 0x78563412
    assert ev.evaluate_expr("bswap32(0x00000000)") == 0x00000000
    assert ev.evaluate_expr("bswap32(0xFFFFFFFF)") == 0xFFFFFFFF
    assert ev.evaluate_expr("bswap32(0x000000FF)") == 0xFF000000

    with pytest.raises(EvaluationError):
        ev.evaluate_expr("bswap32(-1)")

    with pytest.raises(EvaluationError):
        ev.evaluate_expr("bswap32(3.14)")


def test_variables_and_history_references():
    vars_dict = {
        "ans": 42,
        "h1": 100,
        "$1": 100,
        "h2": 0xFF,
    }
    ev = Evaluator(variables=vars_dict)
    assert ev.evaluate_expr("ans + 8") == 50
    assert ev.evaluate_expr("h1 * 2") == 200
    assert ev.evaluate_expr("$1 - 50") == 50
    assert ev.evaluate_expr("h2 + 1") == 256


def test_si_prefix_integration():
    """End-to-end SI prefix evaluation through the Evaluator."""
    ev = Evaluator()
    # kilo
    assert ev.evaluate_expr("10k * 2") == 20000
    assert ev.evaluate_expr("1K + 500") == 1500
    # mega
    assert ev.evaluate_expr("1.5M / 100") == pytest.approx(15000.0)
    assert ev.evaluate_expr("2M + 500k") == 2_500_000
    # giga
    assert ev.evaluate_expr("1G / 1k") == pytest.approx(1_000_000.0)
    # milli
    assert ev.evaluate_expr("1m * 1000") == pytest.approx(1.0)
    # micro
    assert ev.evaluate_expr("10u * 1k") == pytest.approx(0.01)
    assert ev.evaluate_expr("10u + 5u") == pytest.approx(15e-6)
    # nano
    assert ev.evaluate_expr("100n * 1M") == pytest.approx(0.1)
    # pico
    assert ev.evaluate_expr("1p * 1G") == pytest.approx(1e-3)
    # underscore separator
    assert ev.evaluate_expr("10_000k") == 10_000_000
    # mixed SI and plain numbers
    assert ev.evaluate_expr("1k + 1") == 1001

