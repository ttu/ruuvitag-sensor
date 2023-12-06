def rssi_to_hex(rssi: int) -> str:
    return f"{(rssi + (1 << 8)) % (1 << 8):x}"
