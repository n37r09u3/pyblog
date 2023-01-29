import web
from model import *

# logging.info('module base reloaded')
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader

env = Environment(
    loader=FileSystemLoader("themes"),
    autoescape=select_autoescape()
)


class BaseRequestHandler(web.RequestHandler):
    def __init__(self):
        pass

    def initialize(self, request, response):
        web.RequestHandler.initialize(self, request, response)
        self.blog = g_blog
        # self.login_user = users.get_current_user()
        # self.is_login = (self.login_user != None)
        # if self.is_login:
        #     self.loginurl = users.create_logout_url(self.request.uri)
        #     # self.user = User.all().filter('user = ', self.login_user).get() or User(user = self.login_user)
        # else:
        #     self.loginurl = users.create_login_url(self.request.uri)
        #     # self.user = None
        #
        # self.is_admin = users.is_current_user_admin()
        # if self.is_admin:
        #     self.auth = 'admin'
        # elif self.is_login:
        #     self.auth = 'login'
        # else:
        #     self.auth = 'guest'
        self.auth = 'guest'
        try:
            self.referer = self.request.headers['referer']
        except:
            self.referer = None

        self.template_vals = {'self': self, 'blog': self.blog}

    def __before__(self, *args):
        pass

    def __after__(self, *args):
        pass

    def error(self, errorcode, message='an error occured'):
        if errorcode == 404:
            message = 'Sorry, we were not able to find the requested page.  We have logged this error and will look into it.'
        elif errorcode == 403:
            message = 'Sorry, that page is reserved for administrators.  '
        elif errorcode == 500:
            message = "Sorry, the server encountered an error.  We have logged this error and will look into it."

        #        self.template_vals.update({'errorcode': errorcode, 'message': message})
        if errorcode > 0:
            self.response.set_status(errorcode)

        errorfile = getattr(self.blog.theme, 'error' + str(errorcode))
        if not errorfile:
            errorfile = self.blog.theme.error
        self.response.out.write("404")
        # self.response.out.write(template.render(errorfile, self.template_vals))

    def render_use_cache(self, template_file, values):
        """
        Helper method to render the appropriate template
        """

        html = memcache.get('%s:page:%s' % (self.login_user, self.request.path_qs))

        if html == None:
            # try:
            sfile = getattr(self.blog.theme, template_file)
            self.template_vals.update(values)
            html = template.render(sfile, self.template_vals)
            # except Exception, e: # if theme files are not found, fall back to default theme
            # return self.response.out.write('template file "%s" dose not exist.'%(template_file))
            # return self.error(-1,'template file "%s" dose not exist.'%(sfile))

        #            memcache.set('%s:page:%s' % (self.login_user, self.request.path_qs), html)

        self.response.out.write(html)

    def render(self, template_file, template_vals={}):
        """
        Helper method to render the appropriate template
        """
        from jinja2 import Template
        # template = Template('Hello {{ name }}!')
        template = env.get_template("default/2.html")
        # template.render(name='John Doe')
        self.template_vals.update(template_vals)
        path = os.path.join(self.blog.rootdir, template_file)
        s = template.render(self.template_vals)
        self.response.out.write(s)

    def param(self, name, **kw):
        return self.request.get(name, **kw)

    def write(self, s):
        self.response.out.write(s)

    def chk_login(self, redirect_url='/'):
        if self.is_login:
            return True
        else:
            self.redirect(redirect_url)
            return False

    def chk_admin(self, redirect_url='/'):
        if self.is_admin:
            return True
        else:
            self.redirect(redirect_url)
            return False


class BasePublicPage(BaseRequestHandler):
    def initialize(self, request, response):
        BaseRequestHandler.initialize(self, request, response)
        menu_pages = Entry.select().where(Entry.entrytype == 'page', Entry.published == True, Entry.entry_parent == 0)
        self.template_vals.update({
            'menu_pages': menu_pages,
            'categories': Category.select(),
            'recent_comments': Comment.select().order_by(Comment.date)
        })
