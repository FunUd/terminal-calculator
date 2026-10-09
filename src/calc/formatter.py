"""Formatting functions for calculator display."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Union

from calc.bitops import (
    to_i32,
    to_u32,
    is_signed_32_overflow,
    is_unsigned_32_overflow,
)


@dataclass
class FormatResult:
    is_integer: bool
    dec: str
    hex: str
    bin: str
    oct: str
    signed_32: Optional[int]
    unsigned_32: Optional[int]
    signed_overflow: bool
    unsigned_overflow: bool
    warning: str


def format_bin_grouped(val: int) -> str:
    """Format an integer as binary with 4-digit groups (e.g. 0b1_0000_1001)."""
    if val < 0:
        sign = "-"
        abs_val = -val
    else:
        sign = ""
        abs_val = val

    b_str = bin(abs_val)[2:]  # Remove '0b'
    # Group in 4s from the right
    chunks = []
    while b_str:
        chunks.append(b_str[-4:])
        b_str = b_str[:-4]
    chunks.reverse()
    return f"{sign}0b{'_'.join(chunks)}"


def format_result(val: Union[int, float]) -> FormatResult:
    """Format a calculation result into multiple base representations and 32-bit interpretations."""
    if isinstance(val, int):
        s_overflow = is_signed_32_overflow(val)
        u_overflow = is_unsigned_32_overflow(val)
        s32 = to_i32(val)
        u32 = to_u32(val)

        warnings = []
        if s_overflow:
            warnings.append("Signed 32-bit overflow")
        if u_overflow:
            warnings.append("Unsigned 32-bit overflow")

        warning_text = " / ".join(warnings) if warnings else ""

        # Exact HEX format
        if val < 0:
            hex_str = f"-0x{abs(val):X}"
            oct_str = f"-0o{abs(val):o}"
        else:
            hex_str = f"0x{val:X}"
            oct_str = f"0o{val:o}"

        return FormatResult(
            is_integer=True,
            dec=str(val),
            hex=hex_str,
            bin=format_bin_grouped(val),
            oct=oct_str,
            signed_32=s32,
            unsigned_32=u32,
            signed_overflow=s_overflow,
            unsigned_overflow=u_overflow,
            warning=warning_text,
        )
    else:
        # Float result
        # Check if float is close to integer or format nicely
        return FormatResult(
            is_integer=False,
            dec=f"{val:.10g}" if abs(val) < 1e15 and abs(val) > 1e-10 else str(val),
            hex="N/A",
            bin="N/A",
            oct="N/A",
            signed_32=None,
            unsigned_32=None,
            signed_overflow=False,
            unsigned_overflow=False,
            warning="",
        )


def format_bit_grid(val: Optional[int]) -> list[str]:
    """Format integer as a 64-bit 4-line bit visualizer showing 16 bits per line."""
    if val is None:
        return [
            "[63..48] ---- ---- ---- ----",
            "[47..32] ---- ---- ---- ----",
            "[31..16] ---- ---- ---- ----",
            "[15..00] ---- ---- ---- ----",
        ]
    u = val & 0xFFFFFFFFFFFFFFFF
    bits = f"{u:064b}"

    lines = []
    ranges = [(63, 48), (47, 32), (31, 16), (15, 0)]
    for i, (hi, lo) in enumerate(ranges):
        chunk = bits[i * 16 : (i + 1) * 16]
        g0, g1, g2, g3 = chunk[0:4], chunk[4:8], chunk[8:12], chunk[12:16]
        hex_val = (u >> lo) & 0xFFFF
        lines.append(f"[{hi:02d}..{lo:02d}] {g0} {g1} {g2} {g3}  (0x{hex_val:04X})")
    return lines
