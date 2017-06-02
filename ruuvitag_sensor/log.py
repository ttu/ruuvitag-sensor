import logging

logger = logging.getLogger('ruuvitag_sensor')
logger.setLevel(logging.INFO)

# create a file handler
fh = logging.FileHandler('ruuvitag_sensor.log')
fh.setLevel(logging.ERROR)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(fh)


def printToConsole():
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
