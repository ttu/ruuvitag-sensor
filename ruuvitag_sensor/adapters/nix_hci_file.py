import logging

import Path

from ruuvitag_sensor.adapters.nix_hci import BleCommunicationNix

log = logging.getLogger(__name__)


class BleCommunicationNixFile(BleCommunicationNix):
    """
    Emulate HCI communication through hcidump by reading hcidump
    output from a file
    """

    @staticmethod
    def start(bt_device=""):
        """
        Attributes:
           device (string): BLE device (default hci0).
           This is interpreted as a file to open
        """
        log.info("Start reading from file %s", bt_device)
        handle = Path.open(bt_device, "rb")

        return (None, handle)

    @staticmethod
    def stop(_hcitool, hcidump):
        log.info("Close file")
        hcidump.close()
