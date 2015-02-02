#!/usr/bin/python3
import cherrypy
import pymysql
import sys,re,os,time,logging
from mako.template import Template
from mako.lookup import TemplateLookup
print(sys.path)

#makes sure crawler is in the pathspec
home = os.path.expanduser('~')
sys.path.append('%s/extemp/repo' % home)
import crawler
from crawler.cheetah import Cheetah

crawler.cheetah.logger = cherrypy.log.access_log
cherrypy.log.access_log.setLevel(logging.DEBUG)
cherrypy.log.access_log.handlers[1].setLevel(logging.INFO)

for h in crawler.logger.handlers:
   cherrypy.log.access_log.addHandler(h)
"""cherrypy.log.access_log.setLevel(logging.INFO)
cherrypy.log.access_log.handlers[1].setFormatter(logging.Formatter('%(levelname)s::%(name)s: %(message)s'))
cherrypy.log.access_log.handlers[0].setFormatter(logging.Formatter('%(levelname)s::%(name)s: %(message)s'))"""

"""path = os.path.dirname(__file__)
if path != '': path += '/'
date = str(time.strftime("%Y-%m-%d"))
cherrypy.log.error_file = '%sdebug/error/log-%s' % (path,date)
cherrypy.log.access_file = '%sdebug/access/log-%s' % (path,date)"""
path = os.path.dirname(__file__)
if path != '': path += '/'
date = str(time.strftime("%Y-%m-%d"))
cherrypy.log.error_file = '/var/log/extemp/error/log-%s' % date
cherrypy.log.access_file = '/var/log/extemp/access/log-%s' % date
lookup = TemplateLookup(directories=[path + 'html'])

class cherryParent:
   cols = {'text','data','title'}
   hosts = {'bbc':'BBC','cnn':'CNN','economist':'The Economist','newsweek':'Newsweek','nytimes':'New York Times','theguardian':'The Guardian','time':'Time','usnews':'US News','washingtonpost':'Washington Post'}
#  deletes an article from main article table and creates a backup in secondary table
   def deleteArticle(self, a_id):
      backup = 'INSERT IGNORE INTO article_backups SELECT * FROM Articles WHERE id=%s;' % a_id
      delete = 'DELETE FROM Articles WHERE id=%s;' % a_id
      print(backup,delete)

      cheet = Cheetah()
      cheet.connect()
      cheet.cur.execute(backup)
      cheet.cur.execute(delete)
      cheet.conn.commit()
      cheet.close()

#  creates updates elements of an article in the main table
#  data in backup table should be in original form, so
#  copies row over if there is not already an entry for it
   def updateArticle(self, a_id, **kwargs):
#     ensures that only colums in cols set are updated
      for i in (set(kwargs) - self.cols):
         del kwargs[i]
      if 'text' in kwargs:
         text = kwargs['text'].encode('iso8859-1','ignore').decode('unicode_escape','ignore')
         text = text.replace('</p>','').replace('<br>','').replace('"',"'")
         text = text.split('<p>')[1:]
         text2 = []
         for t in text:
            t = t.strip()
            if t != '':
               text2.append(t)
         text = '\n'.join(text2)
         kwargs['text'] = text

      backup = 'INSERT IGNORE INTO article_backups SELECT * FROM Articles WHERE id=%s;' % a_id
      if len(kwargs) == 1:
         update = '%s="%s"' % (list(kwargs.items())[0])
      else:
         update = tuple([('%s="%s"' % i) for i in list(kwargs.items())])
      update = str(update).replace('\\n','\n')
      req = 'UPDATE Articles SET %s where id=%s' % (update,a_id)

      cheet = Cheetah()
      cheet.connect()
      cheet.cur.execute(backup)
      cheet.cur.execute(req)
      cheet.conn.commit()
      cheet.close()

   def insertArticle(self):
      pass

   def checkPin(self,id):
      if type(id) is not int:
         try:
            id = int(id)
         except:
            return False
      user = cherrypy.session.get('user')
      if user:
         return (id in Cheetah().getPins(user))
      return False

   def pinArticle(self,id):
      if 'user' in cherrypy.session:
         Cheetah().addPins(cherrypy.session['user'],id)

   def unpinArticle(self,id):
      if 'user' in cherrypy.session:
         Cheetah().delPins(cherrypy.session['user'],id)

class Root(cherryParent):
   filters = {'host','date'}

   exposed=True
   #@cherrypy.expose()
   def index(self, **kwargs):
      match = set(kwargs.keys()) & self.filters
      matchq = [(" and %s='%s'" % (x,kwargs[x])) for x in match]
      user = cherrypy.session.get('user')
      print('user: ' + str(user))
      if user:
         ids = Cheetah().getPins(user)
         if ids:
            if len(ids) > 1:
               q = "where id in %s %s" % (str(tuple(ids)), ''.join(matchq))
            elif len(ids) == 1:
               q = "where id=%s %s" % (ids[0], ''.join(matchq))
         else:
            q = None
      else:
         if matchq:
            q = "where 1 %s order by timestamp desc limit 90" % ''.join(matchq)
         else:
            q = "select * from Articles p1 inner join (select max(timestamp) maxDate, host from Articles group by host) p2 on p1.timestamp = p2.maxDate and p1.host=p2.host order by timestamp desc;"
      if q:
         data = self.getResults(q)
         kwargs['results'] = data
      else:
         kwargs['results'] = []
      kwargs['Title'] = 'New Articles'
      return self.showIndex(**kwargs)

   def showIndex(self, **kwargs):
      tmpl = lookup.get_template("data.html")
      if 'title' in kwargs:
         kwargs['Title'] = kwargs['title']
         del kwargs['title']
      if not {'Title','results'} <= set(kwargs):
         raise ValueError('essential values missing from kwargs')
      kwargs['hosts'] = self.hosts
      return tmpl.render(**kwargs)

   def getResults(self, append):
      if append[:6].lower() == 'select':
         data = Cheetah().getData(override=append)
      else:
         data = Cheetah().getData("id,title,author,text,date,tags,host", append)
      for i,dic in enumerate(data):
#        change key of title for mako template
         data[i]['name'] = dic['title']
         del data[i]['title']

#        change host for humans
         if dic['host'] in self.hosts:
            data[i]['host'] = self.hosts[dic['host']]

#        fix unicode escaped characters in title
         try:
            data[i]['name'] = dic['name'].encode('iso8859-1','ignore').decode('unicode_escape','ignore')
         except:
            print(str(data[i]).encode('iso8859-1','ignore').decode('unicode_escape','ignore'))

#        split text into paragraphs
         text = dic['text']
         text = text.split('\n')

#        clean up text
         for x in text:
            x.replace('\\n','')
            if x != '' and '\\n' not in x:
               text = x
               break;
         if type(text) is list:
            text = '!!'.join(text)
         text = text.encode('iso8859-1','ignore').decode('unicode_escape','ignore')
         data[i]['text']=text[:400]
      return data

   def GET(self, **kwargs):
      if kwargs.get('host') == 'none':
         del kwargs['host']
      return self.index(**kwargs)

class Search(Root):
   exposed = True
   results = []
   filter_match = {'host'}
   filter_equal = {'date'}

   def index(self, results=[], **kwargs):
      print('args: ' + str(kwargs))
      kwargs['results'] = results
      kwargs['Title'] = 'Results'
      return self.showIndex(**kwargs)

   def search(self, query, filters={}):
      match = set(filters.keys()) & self.filter_match
      equal = set(filters.keys()) & self.filter_equal
      matchq = [(' @%s %s' % (x,filters[x])) for x in match]
      equalq = [(' @%s %s' % (x,filters[x])) for x in equal]
      q = "select id from articleI where match('%s" % query
      for x in matchq:
         q += x
      q += "')"
      for x in equalq:
         q += x
      q += ';'
      print(q)
      conn = pymysql.connect(host='localhost', port=9306)
      cur = conn.cursor()
      cherrypy.log(q)
      cur.execute(q)
      results = cur.fetchall()
      out = [i[0] for i in results]
      cur.close()
      conn.close()
      out = tuple(out)
      return out

   def restQuery(self, ids):
      if len(ids) > 1:
         return self.getResults("where id in %s" % (ids,))
      elif len(ids) == 1:
         return self.getResults("where id = %s" % ids[0])
      else:
         return []

   def GET(self, query=None, **kwargs):
      if query:
         kwargs['query'] = query
         kwargs['results'] = self.restQuery(self.search(query,kwargs))
      return self.index(**kwargs)

   """def POST(self, query, **kwargs):

#raise cherrypy.HTTPRedirect('/search?query=%s' % query, 303)
      ids = self.search(query)
      self.restQuery(ids)
      kwargs['host'] = 'test'
      kwargs['query'] = query
      return self.index(**kwargs)"""

class Article(cherryParent):
   exposed = True

   def getArticle(self, a_id, **kwargs):
      tmpl = lookup.get_template("article.html")
      data = Cheetah().getData("url,title,author,text,date,host,tags","where id='%s'limit 1" % a_id)[0]
      data['Title'] = data['title'].encode('iso8859-1','ignore').decode('unicode_escape','ignore')
      del data['title']

      text = data['text'].encode('iso8859-1','ignore').decode('unicode_escape','ignore')
      text = text.replace('\n\n','\n')
      text = text.replace('\n\n','\n')
      text = text.replace('\n\n','\n')
      text = '<p>' + '</p>\n<p>'.join(text.split('\n'))
      data['text'] = text
      data['id'] = a_id
      if data['host'] in self.hosts:
         data['host'] = self.hosts[data['host']]
      data.update(kwargs)

      return tmpl.render(**data)

   def GET(self, id=None, **kwargs):
      if id == None:
         return 'No id given'
      else:
         user = cherrypy.session.get('user')
         if user:
            if self.checkPin(id):
               kwargs['pin'] = True
            else:
               kwargs['pin'] = False
         return self.getArticle(id, **kwargs)

   def POST(self, id, **kwargs):
      if 'action' in kwargs:
         if kwargs['action'] == 'submit' and 'text' in kwargs:
            text = kwargs['text']
            if text == '':
               return 'Error receiving data'
            self.updateArticle(id,**kwargs)
         if kwargs['action'] == 'delete':
            self.deleteArticle(id)
            raise cherrypy.HTTPRedirect('/', 301)
         if kwargs['action'] == 'pin':
            self.pinArticle(id)
            raise cherrypy.HTTPRedirect('/', 301)
         if kwargs['action'] == 'unpin':
            self.unpinArticle(id)
            raise cherrypy.HTTPRedirect('/', 301)
      raise cherrypy.HTTPRedirect('/article/%s' % id, 301)
      #return str(id) + '\n' + str(kwargs)

class Login:
   exposed = True
   #@cherrypy.expose
   def index(self):
      tmpl = lookup.get_template("login.html")
      return tmpl.render(Title='Login',x=cherrypy.session.get('user'))

   def POST(self, **kwargs):
      if 'user' in kwargs:
         cherrypy.session['user'] = kwargs['user']
         return self.index()

   def GET(self):
      return self.index()

cherrypy.config.update({'tools.staticdir.root' : '%s/extemp/repo/server' % home})
cherrypy.config.update(path+'global.conf')
cherrypy.tree.mount(Root(),'',config=path+'root.conf')
cherrypy.tree.mount(Article(),'/article',config=path+'article.conf')
cherrypy.tree.mount(Search(),'/search',config=path+'search.conf')
cherrypy.tree.mount(Login(),'/login',config=path+'login.conf')
for app in [v[1] for v in cherrypy.tree.apps.items()]:
   app.merge(path + 'apps.conf')
if hasattr(cherrypy.engine, 'block'):
# 3.1 syntax
   cherrypy.engine.start()
   cherrypy.engine.block()
else:
# 3.0 syntax
   cherrypy.server.quickstart()
   cherrypy.engine.start()
