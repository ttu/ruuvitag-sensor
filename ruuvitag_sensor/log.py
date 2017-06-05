import logging


def configureLog(enable_console=False):
    logger = logging.getLogger('ruuvitag_sensor')
    logger.setLevel(logging.INFO)

    # create a file handler
    file_handler = logging.FileHandler('ruuvitag_sensor.log')
    file_handler.setLevel(logging.ERROR)

    # create a logging format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(file_handler)

    if enable_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

