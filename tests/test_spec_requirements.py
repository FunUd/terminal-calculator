"""Tests verifying all specific requirements and examples from spec.md Section 7."""

import pytest
from calc.evaluator import Evaluator, AngleMode
from calc.formatter import format_result


def test_spec_arithmetic_examples():
    ev = Evaluator()
    assert ev.evaluate_expr("2 + 3 * 4") == 14
    assert ev.evaluate_expr("(2 + 3) * 4") == 20
    assert ev.evaluate_expr("2 ** 3 ** 2") == 512
    assert ev.evaluate_expr("0xFF + 10") == 265


def test_spec_bitwise_examples():
    ev = Evaluator()
    assert ev.evaluate_expr("0xFF & 0x0F") == 0x0F
    assert ev.evaluate_expr("0xF0 | 0x0F") == 0xFF
    assert ev.evaluate_expr("0xFF ^ 0x0F") == 0xF0
    assert ev.evaluate_expr("~0") == 0xFFFFFFFF
    assert ev.evaluate_expr("0x80000000 >> 1") == 0x40000000


def test_spec_sign_and_range():
    # 0x7FFFFFFF -> Signed 2147483647
    r1 = format_result(0x7FFFFFFF)
    assert r1.signed_32 == 2147483647
    assert r1.unsigned_32 == 2147483647
    assert not r1.signed_overflow
    assert not r1.unsigned_overflow

    # 0x80000000 -> Signed -2147483648
    r2 = format_result(0x80000000)
    assert r2.signed_32 == -2147483648
    assert r2.unsigned_32 == 2147483648
    assert r2.signed_overflow  # 2147483648 exceeds INT32_MAX
    assert not r2.unsigned_overflow

    # 0xFFFFFFFF -> Signed -1, Unsigned 4294967295
    r3 = format_result(0xFFFFFFFF)
    assert r3.signed_32 == -1
    assert r3.unsigned_32 == 4294967295
    assert r3.signed_overflow
    assert not r3.unsigned_overflow

    # 0xFFFFFFFF + 1 -> 4294967296, Signed 0, Unsigned 0, both overflow
    r4 = format_result(0xFFFFFFFF + 1)
    assert r4.dec == "4294967296"
    assert r4.hex == "0x100000000"
    assert r4.signed_32 == 0
    assert r4.unsigned_32 == 0
    assert r4.signed_overflow
    assert r4.unsigned_overflow

    # -2147483649 -> Signed overflow, Unsigned overflow
    r5 = format_result(-2147483649)
    assert r5.signed_overflow
    assert r5.unsigned_overflow

    # 4294967295 -> Unsigned fits, Signed overflow
    r6 = format_result(4294967295)
    assert not r6.unsigned_overflow
    assert r6.signed_overflow


def test_spec_functions():
    ev_deg = Evaluator(angle_mode=AngleMode.DEG)
    assert pytest.approx(ev_deg.evaluate_expr("sin(30)"), abs=1e-9) == 0.5
    assert ev_deg.evaluate_expr("sqrt(16)") == 4
    assert pytest.approx(ev_deg.evaluate_expr("log(100)"), abs=1e-9) == 2.0
    assert pytest.approx(ev_deg.evaluate_expr("ln(e)"), abs=1e-9) == 1.0

    ev_rad = Evaluator(angle_mode=AngleMode.RAD)
    assert pytest.approx(ev_rad.evaluate_expr("sin(pi / 6)"), abs=1e-9) == 0.5


def test_spec_mixed_radix_examples():
    ev = Evaluator()
    assert ev.evaluate_expr("0xFF + 10") == 265
    assert ev.evaluate_expr("0b1010 * 2") == 20
    assert ev.evaluate_expr("sqrt(16) + 0x10") == 20
    assert ev.evaluate_expr("0o17 + 1") == 16
