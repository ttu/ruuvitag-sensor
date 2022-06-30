import logging

log = logging.getLogger(__name__)


class ShortDataError(Exception):
    pass


def _dechunk(raw):
    """
    Given a BLE advertisement in hex format, interpret the first
    byte as a length byte, return the data indicated by the length
    byte, and the remainder of the data in a tuple.

    The length byte itself is not included in the length.

    If the length indicated is longer than the data, raise a ValueError
    """
    if len(raw) < 2:
        raise ShortDataError("Data too short")

    dlen = int(raw[:2], 16)
    if (dlen + 1) * 2 > len(raw):
        raise ShortDataError(f"Cannot read {dlen} bytes, data too short: {raw}")

    return raw[2:(dlen * 2) + 2], raw[(dlen * 2) + 2:]


class DataFormats(object):
    """
    RuuviTag broadcasted raw data handling for each data format
    """

    # pylint: disable=too-many-return-statements
    @staticmethod
    def convert_data(raw):
        """
        Validate that data is from RuuviTag and get correct data part.

        There is a special case where this function will return
        None for the data format, and '' for the data. This indicates
        that we just heard an advertisement from a Ruuvi tag that
        doesn't contain any data, but was sent for discovery purposes
        (firmware 3.x does this).

        Returns:
            tuple (int, string): Data Format type and Sensor data
        """
        log.debug("Parsing advertisement data: %s", raw)

        try:
            # The data starts with a length byte, covering the data
            # length, minus the length byte itself. There might be additional
            # data at the end (an RSSI value) which we're ignoring
            data, _ = _dechunk(raw)

            # The remaining data is a list of length:type:data chunks.
            # We look for a chunk with vendor specific data (type 0xff),
            # used by formats 3 and 5, or a chunk with serivice data (type 0x16)
            # used by formats 2 and 4.
            #
            # Firmware 3.x also sends advertisements that contain chunks
            # of type 0x09, followed by 'Ruuvi', in ASCII encoding.
            candidate = None
            while data != '':
                cdata, data = _dechunk(data)

                ctype = cdata[:2]
                log.debug("Found chunk of type %s: %s", ctype, cdata)

                # See if we found a potential candidate. Break the loop
                if ctype in ('FF', '16', '09'):
                    candidate = cdata
                    break
        except ShortDataError as ex:
            # Data might be from RuuviTag, but received data was invalid
            # e.g. it's possile that bluetooth stack received only partial data
            # Set the format to None, and data to '', this allows the
            # caller to determine that we did indeed see a Ruuvitag.
            log.debug("Error parsing advertisement data: %s", ex)
            return (None, '')
        except Exception:
            log.exception("Invalid advertisement data: %s", raw)
            return (None, None)

        if candidate is None:
            log.debug("No candidate found")
            return (None, None)

        log.debug("Found candidate %s", candidate)

        # Ruuvi advertisements start with FF9904 (for format 3 and 5),
        # or 16AAFE (for format 2 and 4).
        if candidate.startswith("FF990403"):
            return (3, candidate[6:])

        if candidate.startswith("FF990405"):
            return (5, candidate[6:])

        if candidate.startswith("16AAFE"):
            # TODO: Check from raw data correct data format
            # Now this returns 2 also for Data Format 4
            data = DataFormats._get_data_format_2and4(DataFormats._parse_raw(raw, 2))

            if data is not None:
                return (2, data)

        elif candidate.startswith("095275757669"):
            # This is a Ruuvitag, but this advertisement does not contain any data.
            # Set the format to None, and data to '', this allows the
            # caller to determine that we did indeed see a Ruuvitag.
            return (None, '')

        return (None, None)

    @staticmethod
    def _parse_raw(raw, data_format):  # pylint: disable=unused-argument
        return raw

    @staticmethod
    def _get_data_format_2and4(raw):
        """
        Validate that data is from RuuviTag and is Data Format 2 or 4.
        Convert hexadcimal data to string.
        Encoded data part is after ruu.vi/#

        Returns:
            string: Encoded sensor data
        """
        try:
            base16_split = [raw[i:i + 2] for i in range(0, len(raw), 2)]
            selected_hexs = filter(lambda x: int(x, 16) < 128, base16_split)
            characters = [chr(int(c, 16)) for c in selected_hexs]
            data = ''.join(characters)

            # take only part after ruu.vi/#
            index = data.find('ruu.vi/#')
            if index > -1:
                return data[(index + 8):]

            return None
        except Exception:
            return None

    @staticmethod
    def _get_data_format_3(raw):
        """
        Validate that data is from RuuviTag and is Data Format 3

        Returns:
            string: Sensor data
        """
        # Search of FF990403 (Manufacturer Specific Data (FF) /
        # Ruuvi Innovations ltd (9904) / Format 3 (03))
        try:
            if 'FF990403' not in raw:
                return None

            payload_start = raw.index('FF990403') + 6
            return raw[payload_start:]
        except Exception:
            return None

    @staticmethod
    def _get_data_format_5(raw):
        """
        Validate that data is from RuuviTag and is Data Format 5

        Returns:
            string: Sensor data
        """
        # Search of FF990405 (Manufacturer Specific Data (FF) /
        # Ruuvi Innovations ltd (9904) / Format 5 (05))
        try:
            if 'FF990405' not in raw:
                return None

            payload_start = raw.index('FF990405') + 6
            return raw[payload_start:]
        except Exception:
            return None
