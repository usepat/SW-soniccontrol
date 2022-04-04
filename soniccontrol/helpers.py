import logging

logger = logging.getLogger("soniccontrol")
logger.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(funcName)s:%(message)s')
file_handler = logging.FileHandler('soniccontrol.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
