"""16/32/64-bit Bitwise operations and conversions."""

MASK_16 = 0xFFFF
MASK_32 = 0xFFFFFFFF
MASK_64 = 0xFFFFFFFFFFFFFFFF

INT16_MIN = -32768
INT16_MAX = 32767
UINT16_MIN = 0
UINT16_MAX = 65535

INT32_MIN = -2147483648
INT32_MAX = 2147483647
UINT32_MIN = 0
UINT32_MAX = 4294967295

INT64_MIN = -9223372036854775808
INT64_MAX = 9223372036854775807
UINT64_MIN = 0
UINT64_MAX = 18446744073709551615


def to_u16(val: int) -> int:
    """Normalize an integer to an unsigned 16-bit integer (0 ~ 0xFFFF)."""
    return val & MASK_16


def to_i16(val: int) -> int:
    """Interpret the lower 16 bits of an integer as a two's complement signed 16-bit integer."""
    u = val & MASK_16
    if u >= 0x8000:
        return u - 0x10000
    return u


def to_u32(val: int) -> int:
    """Normalize an integer to an unsigned 32-bit integer (0 ~ 0xFFFFFFFF)."""
    return val & MASK_32


def to_i32(val: int) -> int:
    """Interpret the lower 32 bits of an integer as a two's complement signed 32-bit integer."""
    u = val & MASK_32
    if u >= 0x80000000:
        return u - 0x100000000
    return u


def to_u64(val: int) -> int:
    """Normalize an integer to an unsigned 64-bit integer (0 ~ 0xFFFFFFFFFFFFFFFF)."""
    return val & MASK_64


def to_i64(val: int) -> int:
    """Interpret the lower 64 bits of an integer as a two's complement signed 64-bit integer."""
    u = val & MASK_64
    if u >= 0x8000000000000000:
        return u - 0x10000000000000000
    return u


def _validate_shift_amount(shift: int) -> None:
    if shift < 0 or shift > 31:
        raise ValueError(f"Shift amount must be between 0 and 31, got {shift}")


def bit_and(a: int, b: int) -> int:
    """Bitwise AND restricted to 32-bit."""
    return (to_u32(a) & to_u32(b)) & MASK_32


def bit_or(a: int, b: int) -> int:
    """Bitwise OR restricted to 32-bit."""
    return (to_u32(a) | to_u32(b)) & MASK_32


def bit_xor(a: int, b: int) -> int:
    """Bitwise XOR restricted to 32-bit."""
    return (to_u32(a) ^ to_u32(b)) & MASK_32


def bit_not(a: int) -> int:
    """Bitwise NOT restricted to 32-bit."""
    return (~to_u32(a)) & MASK_32


def bit_lshift(a: int, shift: int) -> int:
    """Bitwise logical left shift restricted to 32-bit."""
    _validate_shift_amount(shift)
    return (to_u32(a) << shift) & MASK_32


def bit_rshift(a: int, shift: int) -> int:
    """Bitwise logical right shift restricted to 32-bit (unsigned right shift)."""
    _validate_shift_amount(shift)
    return (to_u32(a) >> shift) & MASK_32


def is_signed_16_overflow(val: int) -> bool:
    """Check if an exact integer overflows signed 16-bit range."""
    return val < INT16_MIN or val > INT16_MAX


def is_unsigned_16_overflow(val: int) -> bool:
    """Check if an exact integer overflows unsigned 16-bit range."""
    return val < UINT16_MIN or val > UINT16_MAX


def is_signed_32_overflow(val: int) -> bool:
    """Check if an exact integer overflows signed 32-bit range."""
    return val < INT32_MIN or val > INT32_MAX


def is_unsigned_32_overflow(val: int) -> bool:
    """Check if an exact integer overflows unsigned 32-bit range."""
    return val < UINT32_MIN or val > UINT32_MAX


def is_signed_64_overflow(val: int) -> bool:
    """Check if an exact integer overflows signed 64-bit range."""
    return val < INT64_MIN or val > INT64_MAX


def is_unsigned_64_overflow(val: int) -> bool:
    """Check if an exact integer overflows unsigned 64-bit range."""
    return val < UINT64_MIN or val > UINT64_MAX


MASK_16 = 0xFFFF
UINT16_MIN = 0
UINT16_MAX = 65535


def bswap16(x: int) -> int:
    """Swap the byte order of a 16-bit unsigned integer.

    bswap16(0x1234) -> 0x3412
    Raises ValueError if x is outside [0, 0xFFFF].
    """
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"bswap16 requires an integer, got {type(x).__name__}")
    if x < 0 or x > UINT16_MAX:
        raise ValueError(f"bswap16 argument must be in [0, 0xFFFF], got {x}")
    return ((x & 0x00FF) << 8) | ((x & 0xFF00) >> 8)


def bswap32(x: int) -> int:
    """Swap the byte order of a 32-bit unsigned integer.

    bswap32(0x12345678) -> 0x78563412
    Raises ValueError if x is outside [0, 0xFFFFFFFF].
    """
    if not isinstance(x, int) or isinstance(x, bool):
        raise ValueError(f"bswap32 requires an integer, got {type(x).__name__}")
    if x < 0 or x > UINT32_MAX:
        raise ValueError(f"bswap32 argument must be in [0, 0xFFFFFFFF], got {x}")
    return (
        ((x & 0x000000FF) << 24)
        | ((x & 0x0000FF00) << 8)
        | ((x & 0x00FF0000) >> 8)
        | ((x & 0xFF000000) >> 24)
    )
