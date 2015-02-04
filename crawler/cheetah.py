import pymysql, logging

logger = logging.getLogger(__name__)

class Cheetah:
#  log the init of cheetah
   def __init__(self):
      logger.info('Cheetah initializing')

   """gets article information from table. get is mysql select string
#  expr is mysql command following FROM DB. if 'tags' is in get,
#  then the tags for the specified article is put into the
#  returned dictionary"""
   def getData(self, get='*', expr='where 1', override=None, dic=True, **kwargs):
      self.connect()
      if dic: cur = self.cur_dict
      else: cur = self.cur
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
            if 'tags' in get:
               tags = True
               get.remove('tags')
#        makes sure 'id' is in select query
            if tags and 'id' not in get:
               get.append('id')
            get = ','.join(get)
#     raises tag if select query is '*' wildcard
         else: tags = True
#     create and execute mysql query string
         req = "Select " + get + " from Articles " + expr
         if 'order' in kwargs:
            req += " order by " + order
         if 'limit' in kwargs:
            req += " limit " + limit
      print('request: %s' % req)
      logger.debug('request: %s' % req)
      try:
         cur.execute(req)
      except:
         logger.warning('error with request: %s' % req)
         raise
      data = cur.fetchall()
      if tags:
         for item in data:
            item['tags'] = self.getArticleTags(item['id'], False)
      self.close()
      return data

#  get tag ids with given article_ids from db article2tags
   def getArticleTagIDs(self, article_id, connect=True):
      if connect: self.connect()
      self.cur.execute("SELECT tag FROM article2tags WHERE article=%i" % article_id)
      data = self.cur.fetchall()
      tags = [i[0] for i in data]
      logger.debug('article_id: %i :: tags: %s' % (article_id, tags))
      if connect: self.close()
      return tuple(tags)

#  returns array of tags from given article_id
   def getArticleTags(self, article_id, connect=True):
      if connect: self.connect()
#     get tag_ids
      tag_ids = self.getArticleTagIDs(article_id, False)
      if tag_ids == tuple(): return None
      if len(tag_ids) == 1:
         q="SELECT tagName from tags where tagID = %s" % tag_ids[0]
      else:
         q="SELECT tagName from tags where tagID in %s" % (tag_ids,)
      logger.debug('query: %s' % q)
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
      cur.execute("INSERT INTO tags (tagName,tagID) VALUES (%r, NULL)" % tag)
      cur.execute("SELECT last_insert_id()")
      out = cur.fetchone()[0]
      logger.debug('tag: %s :: id: %s' % (tag, out))
      if connect:
         self.conn.commit()
         self.close()
      return out

#  finds tag from the given search term
#  term can either be the tags name or its id
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
            tags.append(self.findTag(t))
         logger.debug('term: %s :: found tag: %s' % (term, str(out)))
         return out
      if connect: self.close()
      logger.debug('term: %s :: found tag: %s' % (term, str(out)))
      if out == tuple() or out is None: return None
      return out[0]

#  parses string of tags to normalize them
#  helps to prevent duplicates
   def parseTags(self, tags):
      x=tags
#     changes dividing character from ; or , to `
      if ';' in tags:
         tags = tags.replace(';','`')
      else:
         tags = tags.replace(',','`')
      tags = tags.split('`')
#     splits tags
      loop = []
      for i,tag in enumerate(loop):
         orig = tag
         tag = tag.encode('iso8859-1','ignore').decode('unicode_escape','ignore')
         if ':' in tag:
            tag = tag.split(':')
            tag = tag[-1]
         tag = tag.strip().lower()
         if len(tag) > 25:
            logger.debug('skipping tag: %s' % tag)
            continue
         loop.append(tag)
      logger.debug('input: %s :: output: %s' % (x, tags))
      return tags

#  uploads a set of article->tag pairs to article2tags
   def uploadTags(self, article_id, tag_ids, commit=False, connect=False):
      if connect: self.connect()
      cur = self.cur
#     organizes data into tuple sets
      values = [(article_id,tag_id) for tag_id in tag_ids]
      values = str(tuple(values))
      values = values[1:-1]
      logger.debug('values: %s' % values)
#     create request string
      x=cur.execute("INSERT INTO article2tags (article,tag) VALUES %s" % values)
      logger.debug('article_id: %i :: tag_ids: %s :: exec return: %s' % (article_id, tag_ids, x))
      if commit: self.conn.commit()
      if connect: self.close()

#  gets list of tags paired
   def putTags(self, article_id, tags, commit=False, connect=False):
      if type(tags) == str:
         tags = self.parseTags(tags)
      tag_IDs = []
      for tag in tags:
         tag_ID = self.findTag(tag, connect)
         if tag_ID:
            tag_IDs.append(tag_ID)
         else:
            tag_IDs.append(self.createTag(tag, True))
      tag_IDs = list(set(tag_IDs))
      logger.debug('article_id, tags, tag_IDs :: %i, %s, %s' % (article_id, tags, tag_IDs))
      self.uploadTags(article_id,tag_IDs, commit, connect)

   def putData(self, data, *values):
      self.connect()
      cur = self.cur_dict
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

#        insert a default value to make data more comprehensive
         if 'date' not in item:
            data[i]['date'] = 'CURDATE()'

         requests.append((tuple(item),tuple([item[key] for key in item])))
      logger.info('uploading data')
      for i in requests:
         keys = str(i[0])
         keys = ''.join(keys.split("'"))
         q = "INSERT INTO Articles %s VALUES %s;" % (keys, i[1])
         logger.debug(q)
         cur.execute(q)
      self.conn.commit()
      for tag in tags:
         self.putTags(*tag, connect=False, commit=False)
      self.conn.commit()
      logger.info('upload complete')
      self.close()

   def getPins(self,user,connect=True):
      user = user.lower().strip()
      if connect: self.connect()
      cur = self.cur
      q = "SELECT article FROM sessions WHERE name='%s'" % user
      logger.debug('query: %s' % q)
      cur.execute(q)
      data = cur.fetchall()
      if connect: self.close()
      return [x[0] for x in data]

   def addPins(self,user,ids,connect=True):
      user = user.lower().strip()
      if connect: self.connect()
      cur = self.cur
      if type(ids) is str or type(ids) is int:
         ids = [ids]
      current = set(self.getPins(user,False))
      ids = list(set(ids) - current)
      if ids != list():
         values = []
         for i in ids:
            values.append((user,i))
         q = "INSERT INTO sessions (name,article) VALUES %s" % str(values)[1:-1]
         print(q)
         logger.warn('query: %s' % q)
         cur.execute(q)
         self.conn.commit()
      if connect: self.close()
      return self.getPins(user,connect)
   def delPins(self,user,ids,connect=True):
      user = user.lower().strip()
      if connect: self.connect()
      cur = self.cur
      if type(ids) is str or type(ids) is int:
         ids = (ids,)
      elif type(ids) is list:
         ids = tuple(ids)
      if len(ids) > 1:
         q = "DELETE FROM sessions WHERE name='%s' and article in %s" % (user,ids)
      elif len(ids) == 1:
         q = "DELETE FROM sessions WHERE name='%s' and article=%s" % (user,ids[0])
      else:
         q = None

      print(q)
      if q:
         cur.execute(q)
         self.conn.commit()
      if connect: self.close()
      return self.getPins(user,connect)

   def close(self):
      logger.info('connection closing')
      self.cur.close()
      self.cur_dict.close()
      self.conn.close()

   def connect(self):
      logger.info('connection opening')
      self.conn = pymysql.connect(host='localhost',user='extemp',passwd='zhH/5]qAYTNNXgE',db='forensics',charset='utf8',init_command="SET NAMES UTF8")
      self.cur_dict = self.conn.cursor(pymysql.cursors.DictCursor)
      self.cur = self.conn.cursor()
