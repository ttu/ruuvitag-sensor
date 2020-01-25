"""
ruuvitag_sensor module level logging
"""

import logging

log = logging.getLogger('ruuvitag_sensor')
log.setLevel(logging.INFO)

# create a file handler
file_handler = logging.FileHandler('ruuvitag_sensor.log')
file_handler.setLevel(logging.ERROR)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler.setFormatter(formatter)

# add the handlers to the logger
log.addHandler(file_handler)


def enable_console():
    if len(log.handlers) != 2:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        log.addHandler(console_handler)
