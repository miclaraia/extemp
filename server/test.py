import cherrypy


class HelloWorld(object):
    def index(self):
        return "Hello world!"
    index.exposed = True

cherrypy.quickstart(HelloWorld())
