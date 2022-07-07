import logging

from ruuvitag_sensor.adapters.nix_hci import BleCommunicationNix

log = logging.getLogger(__name__)


class BleCommunicationNixFile(BleCommunicationNix):
    """
    Emulate HCI communication through hcidump by reading hcidump
    output from a file
    """

    @staticmethod
    def start(bt_device=''):
        """
        Attributes:
           device (string): BLE device (default hci0).
           This is interpreted as a file to open
        """
        log.info("Start reading from file %s", bt_device)
        handle = open(bt_device, 'rb')  # pylint: disable=consider-using-with

        return (None, handle)

    @staticmethod
    def stop(hcitool, hcidump):
        log.info('Close file')
        hcidump.close()
