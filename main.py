from wsgiref.simple_server import make_server
from base import web
from controller import *


def main():
    application = web.WSGIApplication3(
        [('/skin', ChangeTheme),
         ('/themes/[\\w\\-]+/templates/.*', Error404),
         ('/feed', FeedHandler),
         ('/post_comment', Post_comment),
         ('/page/(?P<page>\d+)', MainPage),
         ('/admin/import', admin_import),
         ('/category/(.*)', EntrysByCategory),
         ('/tag/(.*)', EntrysByTag),
         ('/', MainPage),
         ('/favicon.ico', Error404),
         ('/([\\w\\-\\./]+)', SinglePost),
         ('.*', Error404),
         ], debug=True)
    # wsgiref.handlers.CGIHandler().run(application)
    httpd = make_server('', 8000, application)
    print('http://localhost:8000/')
    httpd.serve_forever()


if __name__ == "__main__":
    main()
