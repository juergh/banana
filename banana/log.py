#
# Banana logging
#

import logging
import sys

Logger = logging.getLogger


def config(level="info"):
    """Configure the root logger"""

    log_format = "%(asctime)s - %(levelname)s - %(name)s : %(message)s"
    log_level_map = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "error": logging.ERROR,
    }

    logging.basicConfig(stream=sys.stdout, format=log_format, level=log_level_map[level])
