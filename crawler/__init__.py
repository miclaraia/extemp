from crawler.cheetah import Cheetah
from crawler.owl import Owl
from crawler.spider import Spider
import logging, logging.handlers, os, time

#define logfile path
path = os.path.dirname(__file__)
path += '/debug/'

#init formatters
#file logger format
format_file = logging.Formatter('%(asctime)s %(levelname)s::%(name)s:%(funcName)s::%(message)s', '%Y-%m-%d %H:%M:%S')
#screen logger format
format_screen = logging.Formatter('%(levelname)s::%(name)s: %(message)s')

#create and configure handlers
#logs warnings to screen
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
console.setFormatter(format_screen)

backup = 7
when='D'
#logs warnings to file
date = str(time.strftime("%Y-%m-%d"))
warnings = logging.FileHandler(path + 'error/log-%s' % date)
warnings.setLevel(logging.WARNING)
warnings.setFormatter(format_file)
#logs debugging to file
debug = logging.FileHandler(path + 'debug/log-%s' % date)
debug.setLevel(logging.DEBUG)
debug.setFormatter(format_file)
#logs info to file
general = logging.FileHandler(path + 'info/log-%s' % date)
general.setLevel(logging.INFO)
general.setFormatter(format_file)
#create and configure the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
#logger.addHandler(console)
logger.addHandler(warnings)
logger.addHandler(debug)
logger.addHandler(general)

logger.warning('crawler init complete')
"""for i in logger.handlers[1:4]:
   i.doRollover()"""

"""#logger used specifically for debugging errors
logExcept = logging.Logger(__name__ + '.error')
#sets filepath of debugger output file
path = os.path.abspath(__file__)
path = '/'.join(path.split('/')[:-1])
path += '/debug/exceptions.log'"""
