def decode_9bit(high_bits: int, flags: int, flag_bit: int) -> int | None:
    """Decode 9-bit unsigned value: `high_bits` holds bits [8:1], the selected `flags` bit holds bit [0] (LSB)."""
    value = (high_bits << 1) | ((flags >> flag_bit) & 0x01)
    return None if value == 0x1FF else value
