class DataFormats(object):
    """
    RuuviTag broadcasted raw data handling for each data format
    """

    @staticmethod
    def convert_data(raw):
        """
        Validate that data is from RuuviTag and get correct data part.

        Returns:
            tuple (int, string): Data Format type and Sensor data
        """
        data = DataFormats._get_data_format_3(raw)

        if data is not None:
            return (3, data)

        data = DataFormats._get_data_format_5(raw)

        if data is not None:
            return (5, data)

        # TODO: Check from raw data correct data format
        # Now this returns 2 also for Data Format 4
        data = DataFormats._get_data_format_2and4(raw)

        if data is not None:
            return (2, data)

        return (None, None)

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
        except:
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
        except:
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
        except:
            return None
