import yaml
import os,logging,re

logger = logging.getLogger(__name__)

class Pidgeon:
   def __init__(self):
      self.loadJson()

#  checks if host is in json
   def checkHost(self, host):
      if host in self.json:
         return True
      else: return False

#return any exceptions when searching for paragraphs
   def exceptions(self, host):
      if host not in self.json:
            raise jsonHostError(host)
      if 'except' in self.json[host]:
         return self.json[host]['except']
      return None

#return the tags and classes to look for when searching for the article text
   def query(self, host):
      if host not in self.json.keys():
         raise jsonHostError(host)
      return self.json[host]['content']

   def mysql(self):
      pass

#return the necessary connection parameters like special headers and cookies needed
   def connType(self, host):
      if host not in self.json.keys():
         raise jsonHostError(host)
      if 'conn' in self.json[host].keys():
         return self.json[host]['conn']
      else: return None

#returns instructions for spider on how to crawl for articles
   def crawlSpace(self, host):
      pass

#returns the entire spider block for the link search mechanism
   def spider(self, host):
      if host not in self.json.keys():
         raise jsonHostError(host)
      return self.json[host]['spider']

#returns instructions on how to find authors
   def author(self, host):
      if host not in self.json.keys():
         raise jsonHostError(host)
      if 'author' in self.json[host]:
         return self.json[host]['author']
      return []

#loads json file and processes data
   def loadJson(self):
      f=open(os.path.dirname(__file__) + '/sources.yaml','r')
      raw = f.read()
      f.close()
      self.json = yaml.load(raw)
      #try:
         #self.json = json.loads(raw)
      """except ValueError as e:
         print(e.args)
         def testInt(char):
            try:
               int(char)
               return True
            except ValueError:
               return False
         s = str(e)[-6:-1]
         print(s)
         for i in range(len(s)-1):
           if testInt(s[i]):
              break
         index = int(s[i:])
         char=raw[index]
         message = 'Error Parsing JSON:\nraw:\t' + raw[index-50:index] + '>' + char + '<' + raw[index:index+5]
         message += '\nchar:\t' + raw[index]
         message += '\nindex:\t' + s[i:]
         e.args = (message,)
         raise"""
      return self.json

#  parses a query from the json to be used with Soup
   def parseQuery(self, query):
#     leading symbols in the json allow for more complex objects to be
#     stored. Currently only regexp is supported
      def typeCheck(string):
         if string[0:2] == "r'":
            return re.compile(string[2:])
         else: return string
#     processes an array of attrs with typecheck. Returns a list
      def processAttrs(attrs):
         items = []
         for item in attrs:
            items.append(typeCheck(item))
         return items

#     processes tag portion of query using typecheck. if an array is
#     present each item is typechecked as well
      if 'tag' in query:
         tag = query['tag']
         if type(tag) is str:
            tag = typeCheck(tag)
         elif type(tag) is list:
            tags = tag[:]
            for item in tag:
               tags.append(typeCheck(item))
            tag = tags
         else: tag = ''
      else: tag = ''

#     processes the attrs portion of query. If the content of an attribute
#     is a list then either
#     A: ~listt is the first item:
#       each name:content pair is searched individually
#     B:
#       each name:content list is searched together so that tags must match
#       all the attribute names
      if 'attrs' in query:
         attrs = query['attrs']
#        final output variable
         attrsOut = {}
         for key in attrs:
            if type(attrs[key]) is list:
               if attrs[key][0] == '~list':
                  attrsOut = [key]
                  attrsOut.extend(processAttrs(attrs[key][1:]))
                  break
               else:
                  attrsOut[key] = processAttrs(attrs[key])
            elif type(attrs[key]) is str:
               attrsOut[key] = typeCheck(attrs[key])
      else: attrsOut=None
      return [tag,attrsOut]

#  searches through given soup using query data
#  found in searchBlock
   def search(self, soup, searchBlock):
#     checks the type of the query and performs the search
      def querySoup(soup, query):
         query = self.parseQuery(query)
         logger.debug('search query: %s' % query)
         if type(query[1]) is list:
            queryResults = []
            for item in query[1][1:]:
               queryResults.extend(soup.find_all(query[0],{query[1][0]:item}))
            return queryResults
         else:
            return soup.find_all(*query)
      results = []
#     more complex searching algorithm
#     multiple different search queries
      if type(searchBlock) is list:
         for block in searchBlock:
#           a list of queries to refine the scope of soup searched through
            if type(block) is list:
#              refines soup to all queries except last one
               soups = [soup]
               for query in block[:-1]:
                  soupResults = []
                  for soup in soups:
                     soupResults.extend(querySoup(soup, query))
                  soups = soupResults
#              calls itself to do the final search through the very
#              refined soup
               for refinedSoup in soups:
                  results.extend(self.search(refinedSoup,block[-1]))
#           does a search without refining the soup,
#           iterates through all searchblocks
            else:
               results.extend(querySoup(soup,block))
#     does a search without refining anything, most simple search possible
      else:
         results = querySoup(soup, searchBlock)
      return results

class jsonHostError(LookupError):
   def __init__(self, host):
      self.host = host
   def __str__(self):
      return "Host '" + str(self.host) + "' not found in json"
