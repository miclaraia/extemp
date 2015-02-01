from bs4 import BeautifulSoup
import urllib.request
import json
from crawler.pidgeon import Pidgeon
import re,logging

logger = logging.getLogger(__name__)

class Owl:
   def __init__(self, url, everything=True, flavor="all"):
      #self.user_agent = 'Mozilla/5.0'
      self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.114 Safari/537.36'
      self.url = url
      self.pidgeon = Pidgeon()
      self.host = self.findHost(url)
      self.flavor = flavor

      logger.info('owl initializing:: url: %s:: host: %s' % (url, self.host))
      if everything:
         self.process()

#processes everything
   def process(self):
      self.getSoup()
      self.parseSoup(self.flavor)

#  finds which part of the url is the host
   def findHost(self, url):
      logger.debug('finding host: %s' % url)
      bits = url[7:].split('.')
      logger.debug('bits of url: %s' % bits)
      for i in range(2):
         if self.pidgeon.checkHost(bits[i]):
            return bits[i]
         for check in bits:
            if self.pidgeon.checkHost(check):
               return check
      raise HostError(url)

#  connects to the website and creates a soup object out of it.
# can take parameters defining if cookies are needed and
# any extra headers
   def getSoup(self, url=False, headers=True, cookies=False):
      if url is False:
         url = self.url
         host = self.host
      else:
         host = self.findHost(url)

      conn = self.pidgeon.connType(host)

      html=''
      try:
         if conn is not None:
            if cookies or 'cookies' in conn:
               cookies = True
               headers = False
               import http.cookiejar
               cj = http.cookiejar.CookieJar()
               opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
               html = opener.open(url).read().decode('utf-8')
            if 'headers' in conn:
               if type(conn) is dict:
                  headers = conn['headers']
               else:
                  headers = False
         if headers:
            req = urllib.request.Request(url)
            if headers == True:
               req.add_header('User-agent', self.user_agent)
            else:
               req.add_header('User-agent', headers)
            html = urllib.request.urlopen(req).read()
         elif not cookies:
            html = urllib.request.urlopen(url).read()
      except urllib.error.URLError as e:
         logger.error(url)
         raise e
      html = str(html)
      self.soup = BeautifulSoup(html)
      headers = True

#parses the soup getting title, text, tags, etc.
   def parseSoup(self, flavor):
      if flavor == "all":
         self.text = self.getText()
         self.title = self.getTitle()
         self.tags = self.getTags()
         self.date = self.getDate()
         self.desc = self.getDesc()
         self.author = self.getAuthor()
         self.data = self.getData()

         logger.debug('length of text: %i' % len(str(self.text.split('\n'))))
      elif flavor == "chicken":
         pass

#  returns the body text of the article so
#  long as the host is in the source ref file
   def getText(self):
#     uses a search term dictionary to generate a soup search
      def getItems(query):
         if 'attrs' in query.keys():
            items = self.soup.find_all(query['tag'], attrs=query['attrs'])
         else:
            try:
               items = self.soup.find_all(query['tag'])
            except RuntimeError as e:
               raise RuntimeError('error using soup.find_all::url:%s::query:%s' % (self.url, query))
         return items

#     processes a paragraph by removing certain characters
      def processPara(s):
         s=''.join(s.split('\r'))
         s=''.join(s.split('\n'))
         s=' '.join(s.split('\t'))
         s=s.replace('"',"'").strip()
         s=s.encode('iso8859-1','ignore').decode('unicode_escape','ignore')
         return s

#     suddounds the text in all <a> tags with 'link' so it
#     appears in the processed text
      def processLinks(tag):
         for link in tag.find_all("a"):
            if not link.string: continue
            link.string = "'link'" + link.string + "'link'"

#     soup objects which are to be removed before text is extracted
      excepts = self.pidgeon.exceptions(self.host)
      logger.debug('excepts: %s' % excepts)
#     iterable list of tags/items searched for in the soup
#     if no text was previously found, listed sources are overriden and all
#     p tags are used instead
      queries = iter(list(self.pidgeon.query(self.host)))

#     chooses the right query by comparing the number of items returned
      query = next(queries)
      items = getItems(query)
      while len(items) < 3:
         try:
            query = next(queries)
            items2 = getItems(query)
         except StopIteration:
            break
         if len(items2) > len(items): items = items2
      if len(items) == 0:
         logger.warning('couldnt find article text:: url: %s' % self.url)
         raise TextError(self.url)

#     removes all excepted tags
      if excepts:
#        creates an appendable list if there are multiple
#        except clauses
         if type(excepts) is list:
            excludes = []
            for clause in excepts:
               rules = getItems(clause)
               for i in rules:
                  excludes.append(i)
         else:
            excludes = getItems(excepts)
#        removes excepted tags
         for fluff in excludes:
            fluff.decompose()

#     the output text in list form
      text = []
      for item in items:
         #processLinks(item)
#        for all queries that do not directly search for <p> tags
         if query['tag'] != 'p':
            paras = []
#           searches paragraphs and processes them
            for para in item.find_all('p'):
               s=para.get_text()
               s=processPara(s)
               paras.append(s)
#           appends found paragraphs to text
            text.append('\n'.join(paras))
         else:
            s=item.get_text()
            s=processPara(s)
            text.append(s)
      return '\n'.join(text)

#  gets the articles tags from metadata
   def getTags(self):
      tags = self.soup.find('meta', attrs={'name':re.compile(r'(?i)keywords$')})
      if tags is not None and tags.attrs['content'] != '':
         tags = tags.attrs['content']
         if tags[-1] == ',': tags = tags[:-1]
         return tags
      return ''

#  gets the articles published date from the metadata
#  YYYY-MM-DD
   def getDate(self):
      r=re.compile(r'(?i)date')
      for i in self.soup.find_all('meta',attrs={'name':r}):
         date = i.attrs['content']
         if len(date) == 8:
            return '-'.join([date[:4],date[4:6],date[6:]])
         if '-' in date:
            return '-'.join(date.split('-')[:3])[:10]
         if '/' in date:
            return '-'.join(date.split('/')[:3])[:10]
      return ''

#  gets the articles title from the metadata
   def getTitle(self):
      titles = [self.soup.find('meta', attrs={'property':re.compile(r'title$')})]
      titles.append(self.soup.find('meta', attrs={'name':re.compile(r'title$')}))

      out = ''
      for title in titles:
          if title is not None:
             title = title.attrs['content']
             title = title.replace('"',"'")
             if len(title) > len(out): out = title
      out = out.strip()
      out = out.encode('iso8859-1','ignore').decode('unicode_escape','ignore')
      return out

   def getDesc(self):
      desc = self.soup.find('meta', attrs={'property':re.compile(r'(?i)description')})
      if desc is not None:
         desc = desc.attrs['content']
         desc = desc.replace('"',"'")
         desc = desc.strip()
         desc = desc.encode('iso8859-1','ignore').decode('unicode_escape','ignore')
         return desc
      return ''

   def getAuthor(self):
      json = self.pidgeon.author(self.host)
      if json is None:
         return None
      author = None
      for method in json:
         logger.debug('method: %s' % method)
         if method['method'] == 'search':
            author=self.getAuthor_search(method['string'])
         elif method['method'] == 'meta':
            author = self.getAuthor_meta()
         elif method['method'] == 'soup_query':
            author = self.getAuthor_soup(method)
         if author:
            break
      logger.debug('author: %s' % author)
      if author is None:
         author = ''
      else:
         author = author.title().replace('\\','')
      return author

   def getAuthor_meta(self):
      x = self.soup.find_all('meta',attrs={'name':'author'})
      if x:
         return x[0].get('content')
      return None

   def getAuthor_search(self, string):
      string = string.replace('\\','')
      for script in self.soup.find_all('script'):
         text = str(script.string)
         text = text.replace('\\n','\n')
         text = text.replace('\\t','\t')
         text = text.replace('\\\'','\'')
         text = text.replace('\\"','\"')

         x=re.search(string, text)
         if x:
            return x.group(1)
      return None

#  uses the style in spider to find the text version of the
#  author's name, found usually by the article's title
   def getAuthor_soup(self, query):
      search = self.pidgeon.search(self.soup,query)
      if len(search) > 0:
         author = search[0].text
         logger.debug('found author: %s' % author)
         return author
      return None

#  gets all the metadata from the soup
   def getMeta(self):
      return {'title':str(self.title),'tags':str(self.tags),'date':str(self.date),'summary':str(self.desc)}

#  gets all the data that is not none and puts
#  it in a dictionary; takes a list argument to only return those items
#  if dic is a list, getData does not remove data values that are None
   def getData(self, dic=None):
      data = {'host':self.host,'url':self.url}
      if self.text != '': data['text'] = self.text
      if self.title != '': data['title'] = self.title
      if self.tags != '': data['ATags'] = self.tags
      if self.desc != '': data['summary'] = self.desc
      if self.date != '': data['date'] = self.date
      if self.author != '': data['author'] = self.author
      if type(dic) is list:
         output = {}
         for prop in list:
            output['list'] = data[prop]
         return output
      return data

class OwlError(ValueError):
    def __init__(self, url):
        self.url = url

class HostError(OwlError):
   def __str__(self):
      return 'no known host found in url: ' + str(self.url)

class TextError(OwlError):
   def __str__(self):
      return 'unable to find text: ' + str(self.url)


