import pymysql, logging

logger = logging.getLogger(__name__)

class Cheetah:
   def __init__(self):
#     log cheetah initialization
      logger.info('Cheetah initializing')

   """gets article information from table.
#  get is what's to be selected with mysql select 'get'
#  expr is mysql command following after SELECT 'get' FROM DB.
#  if 'tags' is in get, then the tags for the specified article is put into the returned dictionary"""
   def getData(self, get='*', expr='where 1', override=None, dic=True, **kwargs):
#     connects to mysql databa
      self.connect()
#     determines whether to use dictionary or regular cursor
      if dic: cur = self.cur_dict
      else: cur = self.cur
#     override useful for debugging the tag system.
#     override variable is the mysql string to be used
      if override:
         tags = True
         req = override
      else:
         if get != '*':
            tags = False
            if type(get) is str:
               get = get.replace(' ','')
               get = get.split(',')
#        takes tags out of select query and raises flag
#!       do I have to distinguish between 'tags,' and ',tags'? Would the remaining ',' cause problems
            if 'tags' in get:
               tags = True
               get.remove('tags')
#        makes sure 'id' is in select query, but only if tags flag is raised
            if tags and 'id' not in get:
               get.append('id')
            get = ','.join(get)
#     raises tags flag if selecting with '*' wildcard
         else: tags = True
#     build and execute mysql query string
         req = "SELECT %s FROM Articles %s" % (get, expr)
         #req = "Select " + get + " from Articles " + expr
         if 'order' in kwargs:
            req += " order by %s" % order
         if 'limit' in kwargs:
            req += " limit %s" % limit
      logger.debug('request: %s' % req)

#     execute mysql query
      try:
         cur.execute(req)
      except:
#        makes sure that request string gets logged. Actual error doesn't print it
         logger.warning('error with request: %s' % req)
         raise
#     collects data from the PyMYSQL cursor
      data = cur.fetchall()
#     makes sure to get the tags if flag was raised
      if tags:
         for item in data:
            item['tags'] = self.getArticleTags(item['id'], False)
#     closes mysql connection
      self.close()
      return data

#  get id numbers of tags referenced in table article2tags by article with given id
   def getArticleTagIDs(self, article_id, connect=True):
#     checks if a new connection should be opened
      if connect: self.connect()
      self.cur.execute("SELECT tag FROM article2tags WHERE article=%i" % article_id)
      data = self.cur.fetchall()
      tags = [i[0] for i in data]
      logger.debug('article_id: %i :: tags: %s' % (article_id, tags))
#     checks if a the connection should be closed
      if connect: self.close()
      return tuple(tags)

#  returns list of tags from given article_id
   def getArticleTags(self, article_id, connect=True):
      if connect: self.connect()
#     get tag id numbers
      tag_ids = self.getArticleTagIDs(article_id, False)
#     if tag_ids is an empty tuple, no tags associated with article
      if tag_ids == tuple(): return None
#     only one tag associated with article
      if len(tag_ids) == 1:
         q="SELECT tagName from tags where tagID = %s" % tag_ids[0]
#     multiple tags associated with article
      else:
         q="SELECT tagName from tags where tagID in %s" % (tag_ids,)
      logger.debug('query: %s' % q)
#     execute query and get data from cursor
      self.cur.execute(q)
      tags = self.cur.fetchall()
#     convert data from tuple of tuples: ((1,),(2,)) into list: [1,2]
      tags = [i[0] for i in tags]
      logger.debug('article_id: %i :: tags: %s' % (article_id, tags))
      if connect: self.close()
      return tags

#  creates tag in database and returns its id
#  assumes that the tag does not already exist
   def createTag(self, tag, connect=False):
      if connect: self.connect()
      cur = self.cur
#     inserts tag into table
      cur.execute("INSERT INTO tags (tagName,tagID) VALUES (%r, NULL)" % tag)
#     collects new id of tag for debugging purposes
      cur.execute("SELECT last_insert_id()")
      out = cur.fetchone()[0]
      logger.debug('tag: %s :: id: %s' % (tag, out))
      if connect:
#!       apparently actions aren't saved without committing?
         self.conn.commit()
         self.close()
      return out

#  finds tag from the given search term
#  term can either be the tags name or its id or a list of terms
   def findTag(self, term, connect=True):
      if connect: self.connect()
      cur = self.cur
      out = None
#     searches for tag by id
      if type(term) is int:
         if cur.execute("SELECT tagName from tags where tagID = %i" % term) > 1:
            logger.warning('tagid duplicate in mysql :: id : %i' % term)
         out = cur.fetchone()
#     searches for tag by name
      elif type(term) is str:
         if cur.execute("SELECT tagID from tags where tagName = '%s'" % term) > 1:
            logger.warning('tagname duplicate in mysql :: name: %s' % term)
         out = cur.fetchone()
#     searches for tags by items in list
      elif type(term) is list:
         tags = []
         for t in term:
            tags.append(self.findTag(t),False)
         out = tags
         logger.debug('term: %s :: found tag: %s' % (term, str(out)))
      if connect: self.close()
      logger.debug('term: %s :: found tag: %s' % (term, str(out)))
#     fixes out and returns it
      if out == tuple() or out is None: return None
      if out is tuple: out = out[0]
      return out

#  parses string of tags to normalize them
#  helps to prevent duplicates
   def parseTags(self, tags):
      x=tags
#     changes dividing character from ';' or ',' to '`'
#     assumes method of division was consistent, so either ';'' or ',' but not both
      if ';' in tags:
         tags = tags.replace(';','`')
      else:
         tags = tags.replace(',','`')
#     splits tags
      tags = tags.split('`')
#     actual parsing of tags
      loop = []
      for tag in tags:
#!       orig = tag
#        attempts to fix escape characters
         tag = tag.encode('iso8859-1','ignore').decode('unicode_escape','ignore')
         if ':' in tag:
            tag = tag.split(':')
            tag = tag[-1]
#        removes whitespace and makes all lowercase
         tag = tag.strip().lower()
#        skips if tag is unreasonably long
         if len(tag) > 25:
            logger.debug('skipping tag: %s' % tag)
            continue
         loop.append(tag)
      logger.debug('input: %s :: output: %s' % (x, tags))
      return loop

#  uploads a set of article->tag links to article2tags
   def uploadTags(self, article_id, tag_ids, commit=False, connect=False):
      if connect: self.connect()
      cur = self.cur
#     organizes data into tuple sets
      values = [(article_id,tag_id) for tag_id in tag_ids]
#     changes tuple into string
      values = str(tuple(values))
#     removes leading and trailing brackets '(' ')'
      values = values[1:-1]
      logger.debug('values: %s' % values)
#     create and execute request string
      req = "INSERT INTO article2tags (article,tag) VALUES %s" % values
      try:
         x=cur.execute(req)
      except:
#        makes sure that request string gets logged. Actual error doesn't print it
         logger.warning('error with request: %s' % req)
         raise
      logger.debug('article_id: %i :: tag_ids: %s :: exec return: %s :: mysql request: %s' % (article_id, tag_ids, x, req))
      if commit: self.conn.commit()
      if connect: self.close()

#  given an article and a list of tags, creates a list of tag ids that go with the article id
#  will create a new tag entry in table if one doesn't exist already. otherwise just reuses the old id number
   def putTags(self, article_id, tags, commit=False, connect=False):
      if type(tags) == str:
         tags = self.parseTags(tags)
#     list of tag id numbers
      tag_IDs = []
      for tag in tags:
#        checks if tag already exists
         tag_ID = self.findTag(tag, connect)
         if tag_ID:
            tag_IDs.append(tag_ID)
#        otherwise creates a new tag
         else:
            tag_IDs.append(self.createTag(tag, True))
      tag_IDs = list(set(tag_IDs))
      logger.debug('article_id, tags, tag_IDs :: %i, %s, %s' % (article_id, tags, tag_IDs))
#     uploads new tag associations
      self.uploadTags(article_id,tag_IDs, commit, connect)

#  uploads article data to Article table. Data should be a list of dictionaries
#  but can also use just one dictionary
   def putData(self, data, *values):
      self.connect()
      cur = self.cur_dict
#     get base index number for debugging and associating tags
      cur.execute("SELECT MAX(id) as id from Articles")
      index = cur.fetchone()['id']
#     cursor returns None if table is empty.
      index = 0 if index is None else index + 1
      logger.info('base index: %i' % index)
      if type(data) is not list:
         data = [data]
      requests = []
      tags = []
      for i,item in enumerate(data):
         if 'tags' in item:
            tags.append((index + i, item['tags']))
            #self.putTags(index + i, item['tags'], False)
            del(item['tags'])

#        has mysql assign a date if none exists
         if 'date' not in item:
            data[i]['date'] = 'CURDATE()'

         requests.append((tuple(item),tuple([item[key] for key in item])))
      logger.info('uploading data')
      for i in requests:
         keys = str(i[0])
#        removes "'" from keys string
         keys = ''.join(keys.split("'"))
#        builds
         req = "INSERT INTO Articles %s VALUES %s;" % (keys, i[1])
         logger.debug('put data request: %s' % req)
         try:
            cur.execute(req)
         except:
#           makes sure that request string gets logged. Actual error doesn't print it
            logger.warning('error with request: %s' % req)
            raise
      self.conn.commit()
      for tag in tags:
         self.putTags(*tag, connect=False, commit=False)
      self.conn.commit()
      logger.info('upload complete')
      self.close()

#  gets articles pinned by a certain user session
   def getPins(self,user,connect=True):
#     makes username lowercase and stripped of white spaces
      user = user.lower().strip()
      if connect: self.connect()
      cur = self.cur
      q = "SELECT article FROM sessions WHERE name='%s'" % user
      logger.debug('query: %s' % q)
      cur.execute(q)
      data = cur.fetchall()
      if connect: self.close()
      return [x[0] for x in data]

#  pins an article or set of article ids to a user session
   def addPins(self,user,ids,connect=True):
#     makes username lowercase and stripped of white spaces
      user = user.lower().strip()
      if connect: self.connect()
      cur = self.cur
#     makes list out of single int or string.
      if type(ids) is str or type(ids) is int:
         ids = [ids]
#     checks for and removes duplicate pins
      current = set(self.getPins(user,False))
      ids = list(set(ids) - current)
#     continues if list is not empty
      if ids != list():
         values = []
         for i in ids:
            values.append((user,i))
         q = "INSERT INTO sessions (name,article) VALUES %s" % str(values)[1:-1]
         logger.debug('query: %s' % q)
         cur.execute(q)
         self.conn.commit()
      if connect: self.close()
      return self.getPins(user,connect)

#  deletes a pinned id or set of id numbers from user session
   def delPins(self,user,ids,connect=True):
      user = user.lower().strip()
      if connect: self.connect()
      cur = self.cur
#     makes tuple out of single int or string.
      if type(ids) is str or type(ids) is int:
         ids = (ids,)
#     makes tuple out of list
      elif type(ids) is list:
         ids = tuple(ids)

#     passes ids as tuple to mysql
      if len(ids) > 1:
         q = "DELETE FROM sessions WHERE name='%s' and article in %s" % (user,ids)
#     passes single id to mysql
      elif len(ids) == 1:
         q = "DELETE FROM sessions WHERE name='%s' and article=%s" % (user,ids[0])
      else:
         q = None

      logger.debug('query: %s' % str(q))
      if q:
         cur.execute(q)
         self.conn.commit()
      if connect: self.close()
      return self.getPins(user,connect)

#  closes a mysql connection
   def close(self):
      logger.info('connection closing')
      self.cur.close()
      self.cur_dict.close()
      self.conn.close()

#  opens a mysql connection and creates cursors
   def connect(self):
      logger.info('connection opening')
      self.conn = pymysql.connect(host='localhost',user='extemp',passwd='zhH/5]qAYTNNXgE',db='forensics',charset='utf8',init_command="SET NAMES UTF8")
      self.cur_dict = self.conn.cursor(pymysql.cursors.DictCursor)
      self.cur = self.conn.cursor()
