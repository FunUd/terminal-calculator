import pytest
from calc.bitops import (
    to_u16,
    to_i16,
    to_u32,
    to_i32,
    to_u64,
    to_i64,
    bit_and,
    bit_or,
    bit_xor,
    bit_not,
    bit_lshift,
    bit_rshift,
    is_signed_16_overflow,
    is_unsigned_16_overflow,
    is_signed_32_overflow,
    is_unsigned_32_overflow,
    is_signed_64_overflow,
    is_unsigned_64_overflow,
    bswap16,
    bswap32,
)


def test_to_u32():
    assert to_u32(0) == 0
    assert to_u32(0xFFFFFFFF) == 0xFFFFFFFF
    assert to_u32(0x100000000) == 0
    assert to_u32(-1) == 0xFFFFFFFF
    assert to_u32(-2147483648) == 0x80000000


def test_to_i32():
    assert to_i32(0) == 0
    assert to_i32(0x7FFFFFFF) == 2147483647
    assert to_i32(0x80000000) == -2147483648
    assert to_i32(0xFFFFFFFF) == -1
    assert to_i32(0x100000000) == 0
    assert to_i32(-1) == -1


def test_to_u16():
    assert to_u16(0) == 0
    assert to_u16(0xFFFF) == 0xFFFF
    assert to_u16(0x10000) == 0
    assert to_u16(-1) == 0xFFFF
    assert to_u16(32768) == 32768


def test_to_i16():
    assert to_i16(0) == 0
    assert to_i16(0x7FFF) == 32767
    assert to_i16(0x8000) == -32768
    assert to_i16(0xFFFF) == -1
    assert to_i16(0x10000) == 0
    assert to_i16(-1) == -1


def test_to_u64():
    assert to_u64(0) == 0
    assert to_u64(0xFFFFFFFFFFFFFFFF) == 0xFFFFFFFFFFFFFFFF
    assert to_u64(0x10000000000000000) == 0
    assert to_u64(-1) == 0xFFFFFFFFFFFFFFFF


def test_to_i64():
    assert to_i64(0) == 0
    assert to_i64(0x7FFFFFFFFFFFFFFF) == 9223372036854775807
    assert to_i64(0x8000000000000000) == -9223372036854775808
    assert to_i64(0xFFFFFFFFFFFFFFFF) == -1
    assert to_i64(0x10000000000000000) == 0
    assert to_i64(-1) == -1


def test_bit_and():
    assert bit_and(0xFF, 0x0F) == 0x0F
    assert bit_and(-1, 0xFF) == 0xFF
    assert bit_and(0x10000000F, 0xF) == 0xF


def test_bit_or():
    assert bit_or(0xF0, 0x0F) == 0xFF
    assert bit_or(0x80000000, 0x00000001) == 0x80000001


def test_bit_xor():
    assert bit_xor(0xFF, 0x0F) == 0xF0
    assert bit_xor(0xFFFFFFFF, 0xFFFFFFFF) == 0


def test_bit_not():
    assert bit_not(0) == 0xFFFFFFFF
    assert bit_not(0xFFFFFFFF) == 0
    assert bit_not(0x12345678) == 0xEDCBA987


def test_bit_lshift():
    assert bit_lshift(1, 4) == 16
    assert bit_lshift(0x80000000, 1) == 0  # overflow truncated to 32-bit
    assert bit_lshift(0xFF, 0) == 0xFF

    with pytest.raises(ValueError, match="Shift amount"):
        bit_lshift(1, -1)

    with pytest.raises(ValueError, match="Shift amount"):
        bit_lshift(1, 32)


def test_bit_rshift():
    # Logical right shift
    assert bit_rshift(0x80000000, 1) == 0x40000000
    assert bit_rshift(16, 2) == 4
    assert bit_rshift(0xFFFFFFFF, 4) == 0x0FFFFFFF
    assert bit_rshift(-1, 1) == 0x7FFFFFFF

    with pytest.raises(ValueError, match="Shift amount"):
        bit_rshift(1, -1)

    with pytest.raises(ValueError, match="Shift amount"):
        bit_rshift(1, 32)


def test_overflow_checks():
    # Signed 16-bit: -32768 ~ 32767
    assert not is_signed_16_overflow(0)
    assert not is_signed_16_overflow(32767)
    assert not is_signed_16_overflow(-32768)
    assert is_signed_16_overflow(32768)
    assert is_signed_16_overflow(-32769)

    # Unsigned 16-bit: 0 ~ 65535
    assert not is_unsigned_16_overflow(0)
    assert not is_unsigned_16_overflow(65535)
    assert is_unsigned_16_overflow(-1)
    assert is_unsigned_16_overflow(65536)

    # Signed 32-bit: -2147483648 ~ 2147483647
    assert not is_signed_32_overflow(0)
    assert not is_signed_32_overflow(2147483647)
    assert not is_signed_32_overflow(-2147483648)
    assert is_signed_32_overflow(2147483648)
    assert is_signed_32_overflow(-2147483649)

    # Unsigned 32-bit: 0 ~ 4294967295
    assert not is_unsigned_32_overflow(0)
    assert not is_unsigned_32_overflow(4294967295)
    assert is_unsigned_32_overflow(-1)
    assert is_unsigned_32_overflow(4294967296)

    # Signed 64-bit: -9223372036854775808 ~ 9223372036854775807
    assert not is_signed_64_overflow(0)
    assert not is_signed_64_overflow(9223372036854775807)
    assert not is_signed_64_overflow(-9223372036854775808)
    assert is_signed_64_overflow(9223372036854775808)
    assert is_signed_64_overflow(-9223372036854775809)

    # Unsigned 64-bit: 0 ~ 18446744073709551615
    assert not is_unsigned_64_overflow(0)
    assert not is_unsigned_64_overflow(18446744073709551615)
    assert is_unsigned_64_overflow(-1)
    assert is_unsigned_64_overflow(18446744073709551616)


# bswap16 のテスト
def test_bswap16_basic():
    assert bswap16(0x1234) == 0x3412

def test_bswap16_zero():
    assert bswap16(0x0000) == 0x0000

def test_bswap16_all_ones():
    assert bswap16(0xFFFF) == 0xFFFF

def test_bswap16_low_byte():
    assert bswap16(0x00FF) == 0xFF00

def test_bswap16_high_byte():
    assert bswap16(0xFF00) == 0x00FF

def test_bswap16_invalid_negative():
    with pytest.raises(ValueError):
        bswap16(-1)

def test_bswap16_invalid_overflow():
    with pytest.raises(ValueError):
        bswap16(0x10000)

# bswap32 のテスト
def test_bswap32_basic():
    assert bswap32(0x12345678) == 0x78563412

def test_bswap32_zero():
    assert bswap32(0x00000000) == 0x00000000

def test_bswap32_all_ones():
    assert bswap32(0xFFFFFFFF) == 0xFFFFFFFF

def test_bswap32_low_byte():
    assert bswap32(0x000000FF) == 0xFF000000

def test_bswap32_high_byte():
    assert bswap32(0xFF000000) == 0x000000FF

def test_bswap32_invalid_negative():
    with pytest.raises(ValueError):
        bswap32(-1)

def test_bswap32_invalid_overflow():
    with pytest.raises(ValueError):
        bswap32(0x100000000)
