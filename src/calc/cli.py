"""Command-line interface for calculator with clipboard support."""

from __future__ import annotations
import sys
import argparse
from enum import Enum
from typing import Optional

from calc.evaluator import Evaluator, AngleMode, EvaluationError
from calc.formatter import format_result, FormatResult
from calc.parser import ParseError
from calc.clipboard import copy_to_clipboard


class BaseOption(Enum):
    """Base options for copying results."""
    DEC = "dec"
    HEX = "hex"
    BIN = "bin"
    OCT = "oct"


def get_result_by_base(formatted: FormatResult, base: BaseOption) -> str:
    """Get the result value in the specified base."""
    if base == BaseOption.DEC:
        return formatted.dec
    elif base == BaseOption.HEX:
        return formatted.hex
    elif base == BaseOption.BIN:
        return formatted.bin
    elif base == BaseOption.OCT:
        return formatted.oct
    else:
        return formatted.dec


def cli_main() -> None:
    """Main entry point for CLI mode."""
    parser = argparse.ArgumentParser(
        description="Terminal Calculator - TUI and CLI mode",
        allow_abbrev=False
    )
    parser.add_argument(
        "expression",
        nargs="?",
        help="Mathematical expression to evaluate (e.g., '1 + 2 * 3')"
    )
    parser.add_argument(
        "-b", "--base",
        choices=["dec", "hex", "bin", "oct"],
        default="dec",
        help="Base for copying result (default: dec)"
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Do not copy result to clipboard"
    )
    
    args = parser.parse_args()
    
    # If no expression provided, start TUI mode
    if not args.expression:
        from calc.app import CalculatorApp
        app = CalculatorApp()
        app.run()
        return
    
    # CLI mode: evaluate expression
    try:
        evaluator = Evaluator(angle_mode=AngleMode.DEG)
        result = evaluator.evaluate_expr(args.expression)
        formatted = format_result(result)
        
        base_option = BaseOption(args.base)
        result_value = get_result_by_base(formatted, base_option)
        
        # Print result to stdout
        print(result_value)
        
        # Copy to clipboard unless --no-copy is specified
        if not args.no_copy:
            success = copy_to_clipboard(result_value, app=None)
            if success:
                print(f"[Copied to clipboard: {result_value}]", file=sys.stderr)
            else:
                print("[Failed to copy to clipboard]", file=sys.stderr)
        
    except (ParseError, EvaluationError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
