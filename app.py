from base import web
from controller import *

application = web.MyWSGIApplication(
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
