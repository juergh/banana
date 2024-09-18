#
# Banana logging
#

import logging
import sys

Logger = logging.getLogger


class _StreamToLogger:
    """Helper class to redirect stdout and stderr to the logger"""

    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        message = message.rstrip("\n")
        if message:
            self.logger.log(self.level, message)


def Logger_init(redirect_stdio=False, log_to_stdout=True, log_level="info"):
    """Initialize/configure the logger"""

    log_format = "%(asctime)s - %(levelname)s - %(name)s : %(message)s"
    log_level_map = {
        "info": logging.INFO,
        "debug": logging.DEBUG,
        "error": logging.ERROR,
    }

    if log_to_stdout:
        logging.basicConfig(stream=sys.stdout, format=log_format, level=log_level_map[log_level])
    #    else:
    #        logging.basicConfig(filename=CONF.dwarf_log, format=log_format,
    #                            level=log_level)

    if redirect_stdio:
        # Redirect stdout and stderr to the logger
        logger = logging.getLogger(__name__)
        sys.stdout = _StreamToLogger(logger, logging.INFO)
        sys.stderr = _StreamToLogger(logger, logging.ERROR)
