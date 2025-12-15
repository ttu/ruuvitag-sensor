"""
Decoder utilities and backward compatibility module.

This module contains decoder utility functions (get_decoder, parse_mac) and
re-exports all decoder classes from the decoders package for backward compatibility.
"""

from __future__ import annotations

import logging

# Re-export all decoder classes from the decoders package for backward compatibility.
# Existing code that imports from ruuvitag_sensor.decoder will continue to work.
# New code should import directly from ruuvitag_sensor.decoders for better clarity.
from ruuvitag_sensor.decoders import (
    AirHistoryDecoder,
    Df3Decoder,
    Df5Decoder,
    Df6Decoder,
    DfE1Decoder,
    HistoryDecoder,
    UrlDecoder,
)

log = logging.getLogger(__name__)


__all__ = [
    # Decoder classes (re-exported from ruuvitag_sensor.decoders)
    "AirHistoryDecoder",
    "Df3Decoder",
    "Df5Decoder",
    "Df6Decoder",
    "DfE1Decoder",
    "HistoryDecoder",
    "UrlDecoder",
    # Utility functions (defined in this module)
    "get_decoder",
    "parse_mac",
]


def get_decoder(data_format: int | str) -> UrlDecoder | Df3Decoder | Df5Decoder | Df6Decoder | DfE1Decoder:
    """
    Get correct decoder for Data Format.

    Args:
        data_format: The data format number (2, 3, 4, 5, 6, or "E1")

    Returns:
        object: Data decoder instance

    Raises:
        ValueError: If data_format is not a recognized format
    """
    # Data formats are ordered by priority, so the most common formats are at the top.
    match data_format:
        case 5:
            # https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-5-rawv2
            return Df5Decoder()
        case 6:
            # https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-6
            return Df6Decoder()
        case "E1":
            # https://docs.ruuvi.com/communication/bluetooth-advertisements/data-format-e1.md
            return DfE1Decoder()
        case 2:
            log.warning("DATA TYPE 2 IS OBSOLETE. UPDATE YOUR TAG")
            # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_04.md
            return UrlDecoder()
        case 3:
            log.warning("DATA TYPE 3 IS DEPRECATED - UPDATE YOUR TAG")
            # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_03.md
            return Df3Decoder()
        case 4:
            log.warning("DATA TYPE 4 IS OBSOLETE. UPDATE YOUR TAG")
            # https://github.com/ruuvi/ruuvi-sensor-protocols/blob/master/dataformat_04.md
            return UrlDecoder()
        case _:
            # This should never happen in normal operation since DataFormats.convert_data()
            # already validates and identifies the data format. If we reach here, it indicates
            # a programming error (e.g., convert_data was bypassed or returned an unhandled format).
            raise ValueError(f"Unknown data format: {data_format}")


def parse_mac(data_format: int | str, payload_mac: str) -> str:
    """
    Parse MAC address from payload data.

    Data format 5 payload contains MAC-address in format e.g. e62eb92e73e5

    Args:
        data_format: The data format number
        payload_mac: MAC address string from payload

    Returns:
        string: MAC separated and in upper case e.g. E6:2E:B9:2E:73:E5
    """
    match data_format:
        case 5:
            return ":".join(payload_mac[i : i + 2] for i in range(0, 12, 2)).upper()
        case _:
            return payload_mac
