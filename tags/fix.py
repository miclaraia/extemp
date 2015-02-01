import pymysql
import math

conn = pymysql.connect(host='192.168.1.55',user='mike',passwd='opahans3',db='forensics',charset='utf8')
cur = conn.cursor()
cur2 = conn.cursor()
length = cur.execute('select id,tags from Articles where tags is not null')
length = math.ceil(length/20)

for i in range(length):
   a=cur.fetchmany(20)
   for x in a:
      idn = x[0]
      y=x[1]
      flag=False
      if ':' in y:
         flag=True
      if ';' in y:
         y = y.replace(';','`')
      else:
         y = y.replace(',','`')
      y = y.split('`')
      z=[]
      for a in y:
         #print(a)
         if flag:
            a = a.split(':')
            a = a[-1]
            a = a.strip()
         z.append(a)
      y = z
      del(z)

      def assignTag(tag,ida,flag):
         if cur2.execute('select tagID from tags where tagName = "%s" limit 1' % tag):
            flag = False
            tagID = cur2.fetchall()[0][0]
            cur2.execute("insert into article2tags values (%i,%i)" % (ida, tagID))
            conn.commit()
         else:
            if flag:
               print(tag,ida)
               raise Exception
            flag = True
            cur2.execute('insert into tags values ("%s",NULL);' % tag)
            conn.commit()
            assignTag(tag,ida,flag)
         return flag

      for tag in y:
         tag = tag.encode('iso8859-1','ignore').decode('unicode_escape','ignore')
         tag = tag.strip()
         tag = tag.strip(' \n\t\r')
         tag = tag.lower()
         if tag == '' or len(tag) < 3:
            continue
         tag = tag.replace('"',"'")
         if len(tag) > 30:
            tag = tag[:30]
         print(tag)
         try:
            assignTag(tag,idn,False)
         except:
            print(tag,idn)
            raise


