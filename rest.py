#-*-coding:utf-8

from datetime import date
import time
import signal

import tornado.httpserver
import tornado.escape
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.gen
import tornado.httpclient

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)

MAX_WAIT_SECONDS_BEFORE_SHUTDOWN = 3

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class VersionHandler(tornado.web.RequestHandler):
    def get(self):
        response = { 'version': '3.5.1',
                     'last_build':  date.today().isoformat() }
        self.write(response)
        self.set_header("Content-Type", "text/plain")
 
class GetGameByIdHandler(tornado.web.RequestHandler):
    def get(self, id):
        response = { 'id': int(id),
                     'name': 'Crazy Game',
                     'release_date': date.today().isoformat() }
        self.write(response)

class GetGameByIdNewHandler(tornado.web.RequestHandler):
    def initialize(self, common_string):
        self.common_string = common_string

    def get(self, id):
        response = { 'id': int(id),
                     'name': 'Crazy Game',
                     'release_date': date.today().isoformat(),
                     'common_string': self.common_string }
        self.write(response)

class GetFullPageAsyncNewHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_client.fetch("https://www.websequencediagrams.com/examples.html", callback=self.on_fetch)
 
    def on_fetch(self, http_response):
        if http_response.error: raise tornado.web.HTTPError(500)
        response = http_response.body.decode().replace("Simple signals", "Complex signals")
        self.write(response)
        #self.set_header("Content-Type", "text/html")
        self.finish()

class GetFullPageAsyncHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_response = yield http_client.fetch("https://www.websequencediagrams.com/examples.html")
        response = http_response.body.decode().replace("Signal to Self", "Signal to Others")
        self.write(response)
        self.set_header("Content-Type", "text/html")

class ErrorHandler(tornado.web.RequestHandler):
    def write_error(self, status_code, **kwargs):
        self.write("What the fuck")
        self.set_header("Content-Type", "text/plain")
        self.set_status(status_code)

    def get(self, error_code):
        if error_code == 1:
            self.set_status(400)
        elif error_code == 2:
            self.send_error(503)
        else:
            raise tornado.web.HTTPError(500)

 
application = tornado.web.Application([
    (r"/error/([0-9]+)", ErrorHandler),
    (r"/getfullpage", GetFullPageAsyncHandler),
    (r"/getfullpagenew", GetFullPageAsyncNewHandler),
    (r"/", MainHandler),
    (r"/getgamebyid/([0-9]+)", GetGameByIdHandler),
    (r"/getgamebyidnew/([0-9]+)", GetGameByIdNewHandler, dict(common_string='Value defined in Application')),
    (r"/version", VersionHandler)
])

def sig_handler(sig, frame):
    #logging.warning('Caught signal: %s', sig)
    tornado.ioloop.IOLoop.instance().add_callback(shutdown)
 
def shutdown():
    #logging.info('Stopping http server')
    server.stop()
 
    #logging.info('Will shutdown in %s seconds ...', MAX_WAIT_SECONDS_BEFORE_SHUTDOWN)
    io_loop = tornado.ioloop.IOLoop.instance()
 
    deadline = time.time() + MAX_WAIT_SECONDS_BEFORE_SHUTDOWN
 
    def stop_loop():
        now = time.time()
        if now < deadline and (io_loop._callbacks or io_loop._timeouts):
            io_loop.add_timeout(now + 1, stop_loop)
        else:
            io_loop.stop()
            #logging.info('Shutdown')
    stop_loop()
 
if __name__ == "__main__":
    #application.listen(8888)

    global server
 
    server = tornado.httpserver.HTTPServer(application)
    server.listen(options.port)
 
    signal.signal(signal.SIGTERM, sig_handler)
    signal.signal(signal.SIGINT, sig_handler)

    tornado.ioloop.IOLoop.instance().start()
