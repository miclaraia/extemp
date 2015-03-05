README file

extemp is split into two main groups. The first is a set of tools that collects articles from a number of news sources and stores them in a searchable database for offline usage. The second is a portable webserver that plugs into this database and presents the articles to a user, and allows them to search, categorize, pin, and read the articles, all completely offline from the internet.

HISTORY
The idea for this project came form my participating in my schools forensics team in extemporaneous speaking. In extemporaneous speaking, each participant is given a prompt relating to current global issues. They then have thirty minutes to prepare a short coherent speach outlining their position on the issue and supporting it with facts from other sources. Traditionally these other sources were physical newspapers and magazines indexed by hand with notecards. With this new program, we had a searchable database of information at our fingertips at the competitions, allowing us to spend more time actually formulating what we wanted to say and less time looking for information to back up our claims. With over 50,000 articles in the collection, there is something available no matter what topic is chosen.

DATABASE
The mysql database used is named forensics, and the tables are Articles, article2tags, article_backups, host, sessions, and tags

Articles
	This is the main table that contains all the articles. Its columns are id int(11)|reviewed tinyint(1)|host varchar(20)|title varchar(150)|author tinytext|url varchar(400)|ATags tinytext()|categories tinytext|summary varchar(500)|text text|date date|timestamp timestamp

article2tags
	Table associating article id numbers with tag id numbers. Columns are article int(11) | tag int(11)

article_backups
	Table for making backups of articles when deleted or modified with the webserver. Basically a failsafe for lost information. Columns are identical to Articles

host
	Table containing all the supported news sources. Two columns: id int(11) | host tinytext

sessions
	Table containing articles pinned to a username. Columns: id int(11) | name tinytext | article int(11)

tags
	Table containing all the tags associated with articles. Columns: tagName varchar(50) | tagID int(11)


The two main executable python files are fullrun.py which searches and stores articles, and server.py which does the webserver part.