import os
import logging
import logging.handlers

debug = os.environ.get("_DEBUG")
def setup_logger():
    log_path = os.path.join(os.environ.get("LOG_PATH") or "", "server.log")
    handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=1*1024*1024, backupCount=5)
    fmt = logging.Formatter('%(levelname)s(%(asctime)s): %(message)s')
    handler.setFormatter(fmt)
    logger = logging.getLogger("server")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    if debug:
        log_path = os.path.join(os.environ.get("LOG_PATH") or "", "buffer.log")
        handler = logging.handlers.RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=5)
        handler.setFormatter(fmt)
        logger = logging.getLogger("buffer")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

setup_logger()