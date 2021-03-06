#!/usr/bin/python

import tornado.ioloop
import tornado.web
import tornado.websocket
import datetime
import json

import Pyro.core
import Pyro.naming

from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)

clients = dict() # we store clients in dictionary..

class IndexHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        self.render("www/index.html")

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self, *args):
        self.id = self.get_argument("Id")
        clients[self.id] = {"id": self.id, "object": self}
        tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(seconds=1),self.count)

    def on_message(self, message):        
        self.write_message(u"yo!")
        print "Client %s received a message : %s" % (self.id, message)
        
    def on_close(self):
        if self.id in clients:
            del clients[self.id]

    def count(self):
        global c
        global movement
        world = movement.all()
        self.write_message(json.dumps(world))
        #self.write_message("count : %s"%(str(c)))
        #c+=1
        #print "loop"
        tornado.ioloop.IOLoop.instance().add_timeout(datetime.timedelta(milliseconds=100),self.count)

c = 0

app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/www/(.*)', tornado.web.StaticFileHandler, {'path':'www'}),
    (r'/ws', WebSocketHandler),
])

if __name__ == '__main__':

    movement = Pyro.core.getProxyForURI("PYRONAME://robotmovement")

    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

