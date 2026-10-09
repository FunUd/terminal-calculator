import pytest
from calc.formatter import format_result, format_bin_grouped


def test_format_bin_grouped():
    assert format_bin_grouped(0) == "0b0"
    assert format_bin_grouped(265) == "0b1_0000_1001"
    assert format_bin_grouped(15) == "0b1111"
    assert format_bin_grouped(16) == "0b1_0000"
    assert format_bin_grouped(-10) == "-0b1010"


def test_format_integer_normal():
    # 0xFF + 10 = 265
    res = format_result(265)
    assert res.is_integer is True
    assert res.dec == "265"
    assert res.hex == "0x109"
    assert res.bin == "0b1_0000_1001"
    assert res.oct == "0o411"
    assert res.signed_16 == 265
    assert res.unsigned_16 == 265
    assert res.signed_32 == 265
    assert res.unsigned_32 == 265
    assert res.signed_64 == 265
    assert res.unsigned_64 == 265
    assert res.warning == ""


def test_format_overflow_32bit():
    # 0xFFFFFFFF + 1 = 4294967296
    res = format_result(4294967296)
    assert res.is_integer is True
    assert res.dec == "4294967296"
    assert res.hex == "0x100000000"
    assert res.signed_16 == 0
    assert res.unsigned_16 == 0
    assert res.signed_32 == 0
    assert res.unsigned_32 == 0
    assert res.signed_64 == 4294967296
    assert res.unsigned_64 == 4294967296
    assert "Signed 16-bit overflow" in res.warning
    assert "Unsigned 16-bit overflow" in res.warning
    assert "Signed 32-bit overflow" in res.warning
    assert "Unsigned 32-bit overflow" in res.warning


def test_format_unsigned_only_overflow():
    # 3000000000: fits in unsigned 32-bit, but signed 32-bit overflow
    val = 3000000000
    res = format_result(val)
    assert "Signed 16-bit overflow" in res.warning
    assert "Unsigned 16-bit overflow" in res.warning
    assert "Signed 32-bit overflow" in res.warning
    assert "Unsigned 32-bit overflow" not in res.warning


def test_format_negative_integer():
    res = format_result(-1)
    assert res.dec == "-1"
    assert res.hex == "-0x1"
    assert res.signed_16 == -1
    assert res.unsigned_16 == 65535
    assert res.signed_32 == -1
    assert res.unsigned_32 == 4294967295
    assert res.signed_64 == -1
    assert res.unsigned_64 == 18446744073709551615
    assert "Unsigned 16-bit overflow" in res.warning
    assert "Unsigned 32-bit overflow" in res.warning
    assert "Unsigned 64-bit overflow" in res.warning


def test_format_float():
    res = format_result(3.14)
    assert res.is_integer is False
    assert res.dec == "3.14"
    assert res.hex == "N/A"
    assert res.bin == "N/A"
    assert res.oct == "N/A"
    assert res.signed_16 is None
    assert res.unsigned_16 is None
    assert res.signed_32 is None
    assert res.unsigned_32 is None
    assert res.signed_64 is None
    assert res.unsigned_64 is None
    assert res.warning == ""


def test_format_bit_grid():
    from calc.formatter import format_bit_grid
    # None returns dashes for 64-bit
    lines_none = format_bit_grid(None)
    assert len(lines_none) == 4
    assert "[63..48] ---- ---- ---- ----" in lines_none[0]

    # 265 = 0x0109 -> w0 is 0x0109 (0000 0001 0000 1001)
    lines = format_bit_grid(265)
    assert len(lines) == 4
    assert "[63..48] 0000 0000 0000 0000  (0x0000)" in lines[0]
    assert "[47..32] 0000 0000 0000 0000  (0x0000)" in lines[1]
    assert "[31..16] 0000 0000 0000 0000  (0x0000)" in lines[2]
    assert "[15..00] 0000 0001 0000 1001  (0x0109)" in lines[3]

    # 64-bit value test: 0x8000_0000_0000_0000
    lines_64 = format_bit_grid(0x8000000000000000)
    assert "[63..48] 1000 0000 0000 0000  (0x8000)" in lines_64[0]


def test_format_64bit_overflow():
    # Value larger than 64-bit unsigned
    val = 2**64  # 18446744073709551616
    res = format_result(val)
    assert res.signed_16 == 0
    assert res.unsigned_16 == 0
    assert res.signed_32 == 0
    assert res.unsigned_32 == 0
    assert res.signed_64 == 0
    assert res.unsigned_64 == 0
    assert "Signed 16-bit overflow" in res.warning
    assert "Unsigned 16-bit overflow" in res.warning
    assert "Signed 32-bit overflow" in res.warning
    assert "Unsigned 32-bit overflow" in res.warning
    assert "Signed 64-bit overflow" in res.warning
    assert "Unsigned 64-bit overflow" in res.warning


