from crawler.owl import Owl
from crawler.cheetah import Cheetah
from crawler.pidgeon import Pidgeon
import re
import logging

logger = logging.getLogger(__name__)

#crawls homepages of news sites to find articles
class Spider():
   def __init__(self, host):
      logger.info('spider initializing:: host:%s' % host)
      self.host = host
      self.pidgeon = Pidgeon()
      if type(host) is dict:
         pass
      else:
         self.json = self.pidgeon.spider(host)
      self.links = []

#gets all links using data in sources.json and puts them into self.links
#checks for duplicates and creates array to hold url and tags (where the
#link was found on the site) for each link
   def getLinks(self):
      logger.debug('getting links:: %s' % (self.host))
#     base url of the site from pidgeon
      baseURL = self.json['url']
      logger.debug('baseURL: %s' % baseURL)
#     checks to make sure the url is formed right
      if '~' not in baseURL: raise malformedBaseURL(self.host)
      if len(baseURL.split('~')) > 2: raise malformedBaseURL(self.host)
#     iterates through subs in spider block
      for sub in self.json['sub']:
         if 'paginate' in sub:
            parsed = self.parseURLs(sub['url'],sub['paginate'])
         else:
            parsed = self.parseURLs(sub['url'])
         logger.debug('parsed: %s' % parsed)
#        iterates through all the urls in the sub-url block
         for urlChunk in parsed:
#           creates url for owl to work with and creates owl
            url = baseURL.replace('~',urlChunk)
            logger.debug('searching for links in url: %s' % url)
            owl = Owl(url,everything=False)
            owl.getSoup()
#           removes anything if an except block is present
#           in the spider block
            if 'except' in self.json:
               self.rmExcept(owl.soup, self.json['except'])
#           removes anything in except blocks in the sub block
            if 'except' in sub:
               self.rmExcept(owl.soup, sub['except'])
#           temp array to store links found in this sub-url block
            links = []
#           search block allows for more complex searching
#           algorithm
            if 'search' in sub:
               links.extend(self.xfind_links(owl.soup, sub['search']))
            else:
               links.extend(self.xfind_links(owl.soup, sub))
            if len(links) == 0: continue
            checkedLinks = self.checkLinks(links, url)
            checkedLinks = self.cheetahCheck(checkedLinks)
            self.links.extend(checkedLinks)
            #self.links.extend(links)
            logger.info('links found:: sub:%s:: %i' % (url,len(links)))
      self.links = list(set(self.links))
      logger.info('all links found: %i' % len(self.links))
      return self.links

#  parses urls into a list and checks for errors
   def parseURLs(self, urls, pagination=False):
      logger.debug('parsing urls for %s' % self.host)
      exitURLs = []
#     a list of urls
      if type(urls) is list:
         for url in urls:
#           a list of urls with the same leading directory
#           the leading directory is found in the first
#           item in the array
            if type(url) is list:
               base = url[0]
               for item in url[1:]:
                  exitURLs.append(base + '/' + item)
            elif type(url) is str:
               exitURLs.append(url)
            else: raise subURLTypeError(self.host, url)
#     just one url
      elif type(urls) is str:
         exitURLs.append(urls)
      else: raise subURLTypeError(self.host, urls)
      if pagination:
         exitURLs += self.paginate(exitURLs,pagination)
      logger.debug('url return: %s' % exitURLs)
      return exitURLs

#  supports pagination in the news sites
   def paginate(self, urls, pagination):
      logger.info('paginating urls: %s :: host: %s' % (urls,self.host))
      if 'append' not in pagination or '~' not in pagination['append']:
         raise malformedBaseURL(self.host)
      if 'max' not in pagination:
         pagination['max'] = 2
      exitURLs = []
      for this_url in urls:
         paginated = []
         for i in range(pagination['max']):
            url = this_url
            i += 2
            url += '/' + pagination['append']
            url = url.replace('~',str(i))
            paginated.append(url)
         exitURLs += paginated
      logger.debug('returning paginated urls: %s' % exitURLs)
      return exitURLs

#  finds links given the soup and search query in block form
   def xfind_links(self, soup, searchBlock):
      logger.info('xfinding links host: %s' % self.host)
      links = []
#     creates an iterable list out of searchblock
      if type(searchBlock) is not list:
         searchBlock = [searchBlock]
#     iterates through the results of search, calls find_links
#     to get the actual urls of each link
      for block in self.pidgeon.search(soup, searchBlock):
         link = self.find_links(block, self.pidgeon.parseQuery(searchBlock[-1]))
         if link: links.append(link)
      logger.debug('xfind_links return: %s' % links)
      return links

#  uses the query used to figure out if an actual <a> tag was found,
#  or if the first <a> tag in element is to be used to take the link
   def find_links(self, element, query):
      if element.name == 'a':
         return element.attrs['href']
      else:
         try:
            return element.a.attrs['href']
         except AttributeError:
            logging.exception('error finding a tag::element:%s' % element)
            return None

#  checks links for duplicsates and malformed urls
#  sub: subset from the homepage of the site
#  url: url used to get to ^ sub
   def checkLinks(self, links, url):
      links = links[:]
      if len(links) == 0: return links
#     checks if url has a trailing '/'
      if url[-1] == '/': url = url[:-1]
#     checks all the links that they are full urls, and don't have any
#     trailing php GET pieces
      for i, link in enumerate(links):
         link = link.strip()
         if link[:7] != 'http://':
            link = 'http://' + url.split('/')[2] + link
         link = link.replace('\r','')
         link = link.replace('\n','')
         link = link.replace('"','')
         link = link.split('?')[0]
         links[i] = link
#     checks for duplicates within linksOut
      links = list(set(links))
#     checks each link to see if it already exists in self.links
      linksOut = links[:]
      for link in links:
         if link in self.links:
            linksOut.remove(link)
      return linksOut

#  checks if links are already stored in the database
   def cheetahCheck(self, links):
      links = links[:]
      if len(links) == 0: return links
      origLinks = links[:]
      cheetLinks = ['"' + link + '"' for link in links]

      req = 'where url in (' + ','.join(cheetLinks) + ');'
      logger.debug('mysql request: %s' % req)
      dbLinks = list(set(Cheetah().getData('url', req, dic=False)))
      for dupLink in dbLinks:
         links.remove(dupLink[0])
      return links

#  searches for and removes any blocks that match query in exceptBlock
   def rmExcept(self, soup, exceptBlock):
      if type(exceptBlock) is not list:
         exceptBlock = [exceptBlock]
      for ex in self.pidgeon.search(soup, exceptBlock):
         ex.decompose()

class malformedURL(ValueError):
   def __init__(self, url):
      if type(url) is str:
         self.url = url
      elif type(url) is list:
         self.url = '\n\t'.join(url)
      else:
         self.url = str(url)
   def __str__(self):
      return 'error parsing url:%s' % self.url

class malformedBaseURL(malformedURL):
   def __init__(self, host):
      super(Pidgeon().spider(host)['url'])
   def __str__(self):
      s = str(malformedURL)
      return 'SPIDER::%s' % s

class subURLTypeError(ValueError):
   def __init__(self, url):
      self.url = url
      f = open('debug/subURLTypeError.err', 'a')
      f.write(str(url))
      f.close()
   def __str__(self):
      return 'error with url type:%s' % type(self.url)

class bcolors:
   HEADER = '\033[95m'
   OKBLUE = '\033[94m'
   OKGREEN = '\033[92m'
   WARNING = '\033[93m'
   FAIL = '\033[91m'
   ENDC = '\033[0m'

   def disable(self):
      self.HEADER = ''
      self.OKBLUE = ''
      self.OKGREEN = ''
      self.WARNING = ''
      self.FAIL = ''
      self.ENDC = ''
