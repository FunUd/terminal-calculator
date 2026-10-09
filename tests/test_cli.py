"""Tests for command-line mode functionality."""

import pytest
from calc.evaluator import Evaluator, AngleMode
from calc.formatter import format_result
from calc.cli import cli_main, BaseOption


def test_base_option_enum():
    """Test BaseOption enum values."""
    assert BaseOption.DEC.value == "dec"
    assert BaseOption.HEX.value == "hex"
    assert BaseOption.BIN.value == "bin"
    assert BaseOption.OCT.value == "oct"


def test_evaluate_expression_simple():
    """Test simple arithmetic evaluation."""
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    result = evaluator.evaluate_expr("1 + 2 * 3")
    assert result == 7


def test_evaluate_expression_with_variables():
    """Test evaluation with history variables."""
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    evaluator.variables = {"ans": 10, "h1": 20}
    
    result = evaluator.evaluate_expr("ans + h1")
    assert result == 30


def test_evaluate_expression_hex_literal():
    """Test evaluation with hex literal."""
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    result = evaluator.evaluate_expr("0xFF + 10")
    assert result == 265


def test_format_result_dec():
    """Test formatting result in DEC base."""
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    result = evaluator.evaluate_expr("1 + 2 * 3")
    formatted = format_result(result)
    
    assert formatted.dec == "7"
    assert formatted.hex == "0x7"
    assert formatted.bin == "0b111"


def test_format_result_hex():
    """Test formatting result in HEX base."""
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    result = evaluator.evaluate_expr("0xFF + 10")
    formatted = format_result(result)
    
    assert formatted.dec == "265"
    assert formatted.hex == "0x109"
    assert formatted.bin == "0b1_0000_1001"


def test_cli_get_result_by_base_dec():
    """Test getting result value by base option (DEC)."""
    from calc.cli import get_result_by_base
    
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    result = evaluator.evaluate_expr("0xFF + 10")
    formatted = format_result(result)
    
    value = get_result_by_base(formatted, BaseOption.DEC)
    assert value == "265"


def test_cli_get_result_by_base_hex():
    """Test getting result value by base option (HEX)."""
    from calc.cli import get_result_by_base
    
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    result = evaluator.evaluate_expr("0xFF + 10")
    formatted = format_result(result)
    
    value = get_result_by_base(formatted, BaseOption.HEX)
    assert value == "0x109"


def test_cli_get_result_by_base_bin():
    """Test getting result value by base option (BIN)."""
    from calc.cli import get_result_by_base
    
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    result = evaluator.evaluate_expr("0xFF + 10")
    formatted = format_result(result)
    
    value = get_result_by_base(formatted, BaseOption.BIN)
    assert value == "0b1_0000_1001"


def test_cli_get_result_by_base_oct():
    """Test getting result value by base option (OCT)."""
    from calc.cli import get_result_by_base
    
    evaluator = Evaluator(angle_mode=AngleMode.DEG)
    result = evaluator.evaluate_expr("0xFF + 10")
    formatted = format_result(result)
    
    value = get_result_by_base(formatted, BaseOption.OCT)
    assert value == "0o411"


def test_cli_main_with_expression(capsys, monkeypatch):
    """Print the decimal result and copy it to the clipboard by default."""
    import sys
    import calc.cli as cli
    copied = []
    monkeypatch.setattr(sys, "argv", ["tc", "1+2*3"])
    monkeypatch.setattr(
        cli, "copy_to_clipboard", lambda text, app=None: copied.append(text) or True
    )

    cli.cli_main()

    captured = capsys.readouterr()
    assert captured.out == "7\n"
    assert copied == ["7"]
    assert "[Copied to clipboard: 7]" in captured.err


def test_cli_main_with_hex_option(capsys, monkeypatch):
    """Print and copy the result in the selected base."""
    import sys
    import calc.cli as cli
    copied = []
    monkeypatch.setattr(sys, "argv", ["tc", "-b", "hex", "0xFF + 10"])
    monkeypatch.setattr(
        cli, "copy_to_clipboard", lambda text, app=None: copied.append(text) or True
    )

    cli.cli_main()

    captured = capsys.readouterr()
    assert captured.out == "0x109\n"
    assert copied == ["0x109"]


def test_cli_main_no_copy_option(capsys, monkeypatch):
    """Print the result without copying when --no-copy is specified."""
    import sys
    import calc.cli as cli

    def unexpected_copy(*args, **kwargs):
        pytest.fail("clipboard should not be accessed with --no-copy")

    monkeypatch.setattr(sys, "argv", ["tc", "--no-copy", "1+2*3"])
    monkeypatch.setattr(cli, "copy_to_clipboard", unexpected_copy)

    cli.cli_main()

    assert capsys.readouterr().out == "7\n"


def test_cli_main_with_invalid_expression(capsys):
    """Test CLI main with invalid expression."""
    from calc.cli import cli_main
    import sys
    
    old_argv = sys.argv
    try:
        sys.argv = ["tc", "1 / 0"]
        with pytest.raises(SystemExit):
            cli_main()
        
        captured = capsys.readouterr()
        # Error message should be in stderr
        assert captured.err != ""
    finally:
        sys.argv = old_argv


def test_cli_main_no_args_starts_tui(capsys):
    """Test CLI main with no arguments starts TUI mode (no output to stdout)."""
    from calc.cli import cli_main
    from calc.app import CalculatorApp
    import sys
    
    old_argv = sys.argv
    try:
        sys.argv = ["tc"]
        
        # Mock the run method to prevent actual TUI launch
        import unittest.mock as mock
        with mock.patch.object(CalculatorApp, 'run', return_value=None):
            cli_main()
        
        # Should not print anything to stdout in TUI mode
        captured = capsys.readouterr()
        assert captured.out == ""
    finally:
        sys.argv = old_argv
