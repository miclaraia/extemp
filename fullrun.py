#!/usr/bin/python3
from crawler import *
import crawler.owl
import time,json,logging

#logger used for the entire package and everything else
logger = logging.getLogger('crawler')
log_fail = logging.getLogger('url_fail')
path = os.path.abspath(__file__)
path = '/'.join(path.split('/')[:-1])
log_fail.addHandler(logging.handlers.RotatingFileHandler('/home/michael/extemp/crawler/debug/urls/log',backupCount=9))
log_fail.handlers[0].setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:: %(message)s','%Y-%m-%d %H:%M:%S'))
log_fail.handlers[0].doRollover()
log_fail.propagate = False
log_fail.warning('fail logging initialized')

#logger used specifically for debugging this module
debugger = logging.Logger('fullrun.debug')
#sets filepath of debugger output file
path = os.path.abspath(__file__)
path = '/'.join(path.split('/')[:-1])
path += '/debug/fullrun.log'
#creates file handler for debugger
logFile = logging.FileHandler(path)
logFile.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s::%(message)s','%Y-%m-%d %H:%M:%S')
logFile.setFormatter(formatter)

#clears debuggers handlers and adds the new one
handlers = list(debugger.handlers)
for h in handlers:
   debugger.removeHandler(h)
debugger.addHandler(logFile)

#creates initial variables and objects
cheet = Cheetah()
hosts=('bbc','cnn','time','economist','washingtonpost','nytimes','theguardian','newsweek','usnews')

logger.warning('fullrun initializing')
cheetUp = []
debug = []
for host in hosts[:]:
#for host in ['usnews']:
   try:
      debugger.debug('host:%s' % host)
      logger.info('host: %s' % host)
      linkTime = time.time()
      links = Spider(host).getLinks()
      linkTime = time.time() - linkTime
      debugger.debug('linkTime:%s' % linkTime)
      dbg = 'links:\n'
      for link in links:
         dbg += '\t\t%s\n' % link
      debugger.debug(dbg)
      for link in links[:]:
         try:
            try:
               owl = Owl(link)
               data = owl.getData()
               if 'text' not in data:
                  continue
               cheetUp.append(data)
            except crawler.owl.HostError:
               logger.error('cant find host:: link: %s' % e.url)
               links.remove(link)
               raise e
            except crawler.owl.TextError as e:
               logger.error('cant find text:: link: %s' % e.url)
               links.remove(link)
               raise e
            except KeyboardInterrupt:
               raise
            except:
               logger.exception('fullrun line 52')
               continue
         except crawler.owl.OwlError as e:
            log_fail.error('%s: %s' % (e.url, type(e)))
            continue
   except KeyboardInterrupt:
      raise
   except:
      logger.exception('fullrun line 55')
      continue
logger.info('total links processed: %i' % len(cheetUp))
if len(cheetUp) > 0:
   try:
      cheet.putData(cheetUp)
      debugger.info('cheetah data length:%i' % len(cheetUp))
      logger.warning('process completed successfully')
   except Exception:
      logger.exception()
      logger.critical('error uploading data')
      f = open('fail_data.json','w')
      f.write(json.dumps(cheetUp))
      f.close()
      raise
else:
   logger.critical('no data in mysql data upload queue')
