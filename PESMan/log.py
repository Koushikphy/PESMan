import logging, sys
# Custom formatter
class MyFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt="%I:%M:%S %p %d-%m-%Y"):
        logging.Formatter.__init__(self, fmt, datefmt)

    def format(self, record):
        if record.levelno == logging.DEBUG: self._fmt = "%(message)s"
        elif record.levelno == logging.INFO: self._fmt = "[%(asctime)s] %(module)s - %(message)s"
        result = logging.Formatter.format(self, record)
        # print result
        return result





fmt = MyFormatter()
hdlr = logging.StreamHandler(sys.stdout)

hdlr.setFormatter(fmt)
logging.root.addHandler(hdlr)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.info('\nfjwehfu')
logger.debug('geuyerer')

try:
    x=9/0
except:

    logger.exception('fjwefio')