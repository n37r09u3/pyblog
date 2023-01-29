import logging
import os

from peewee import *

db = SqliteDatabase('pyblog.db')
db.connect()


class Theme:
    def __init__(self, name='default'):
        self.name = name
        self.mapping_cache = {}
        self.dir = '/themes/%s' % name
        self.viewdir = os.path.join(os.getcwd(), 'view')
        self.server_dir = os.path.join(os.getcwd(), 'themes', self.name)

    def __getattr__(self, name):
        if name in self.mapping_cache:
            return self.mapping_cache[name]
        else:
            path = os.path.join(self.server_dir, 'templates', name + '.html')
            if not os.path.exists(path):
                path = os.path.join(os.getcwd(), 'themes', 'default', 'templates', name + '.html')
                if os.path.exists(path):
                    self.mapping_cache[name] = path
                    return path
            else:
                self.mapping_cache[name] = path
                return path
            return None


class ThemeIterator:
    def __init__(self, theme_path='themes'):
        self.iterating = False
        self.theme_path = theme_path
        self.list = []

    def __iter__(self):
        return self

    def next(self):
        if not self.iterating:
            self.iterating = True
            self.list = os.listdir(self.theme_path)
            self.cursor = 0

        if self.cursor >= len(self.list):
            self.iterating = False
            raise StopIteration
        else:
            value = self.list[self.cursor]
            self.cursor += 1
            return (str(value), unicode(value))


#
# class BaseModel(db.Model):
#     def __init__(self, parent=None, key_name=None, _app=None, **kwds):
#         self.__isdirty = False
#         DBModel.__init__(self, parent=None, key_name=None, _app=None, **kwds)
#
#     def __setattr__(self, attrname, value):
#         """
#         DataStore api stores all prop values say "email" is stored in "_email" so
#         we intercept the set attribute, see if it has changed, then check for an
#         onchanged method for that property to call
#         """
#         if (attrname.find('_') != 0):
#             if hasattr(self, '_' + attrname):
#                 curval = getattr(self, '_' + attrname)
#                 if curval != value:
#                     self.__isdirty = True
#                     if hasattr(self, attrname + '_onchange'):
#                         getattr(self, attrname + '_onchange')(curval, value)
#
#         DBModel.__setattr__(self, attrname, value)


class Person(Model):
    name = CharField(null=True)
    birthday = DateField()

    class Meta:
        database = db  # This model uses the "people.db" database.


class Cache(db.Model):
    cachekey = CharField(null=True)
    content = CharField(null=True)


class Blog(db.Model):
    key_name = CharField(null=True)
    owner = CharField(null=True)
    author = CharField(null=True)
    rpcuser = CharField(null=True)
    rpcpassowrd = CharField(null=True)
    description = CharField(null=True)
    baseurl = CharField(null=True)
    urlpath = CharField(null=True)
    title = CharField(null=True)
    subtitle = CharField(null=True)
    entrycount = CharField(null=True)
    posts_per_page = CharField(null=True)
    feedurl = CharField(null=True)
    blogversion = CharField(null=True)
    theme_name = CharField(default='default')
    enable_memcache = CharField(null=True)
    link_format = CharField(null=True)
    theme = None

    def initialsetup(self):
        self.title = 'Your Blog Title'
        self.subtitle = 'Your Blog Subtitle'

    def get_theme(self):
        self.theme = Theme(self.theme_name)
        return self.theme


class Category(db.Model):
    name = CharField(null=True)
    slug = CharField(null=True)

    @property
    def posts(self):
        return Entry.all().filter('entrytype =', 'post').filter('categorie_keys =', self)

    @property
    def count(self):
        return self.posts.count()


class Archive(db.Model):
    monthyear = CharField(null=True)
    entrycount = CharField(null=True)
    date = CharField(null=True)


class Tag(db.Model):
    tag = CharField(null=True)
    tagcount = CharField(null=True)

    @property
    def posts(self):
        return Entry.all('entrytype =', 'post').filter('tags =', self)


class Link(db.Model):
    href = CharField(null=True)
    linktype = CharField(null=True)
    linktext = CharField(null=True)


class Entry(db.Model):
    author = CharField(null=True)
    published = BlobField(default=False)
    content = CharField(null=True)
    title = CharField(null=True)
    date = CharField(null=True)
    tags = CharField(null=True)
    categorie_keys = CharField(null=True)
    slug = CharField(null=True)
    link = CharField(null=True)
    monthyear = CharField(null=True)
    entrytype = CharField(null=True)
    entry_parent = CharField(null=True)
    menu_order = CharField(null=True)
    commentcount = CharField(null=True)

    # compatible with wordpress
    is_wp = CharField(null=True)
    post_id = CharField(null=True)

    def fullurl(self):
        return g_blog.baseurl + '/' + self.link;

    @property
    def categories(self):
        try:
            return db.get(self.categorie_keys)
        except:
            return []

    ##    def get_categories(self):
    ##        return ','.join([cate for cate in self.categories])
    ##
    ##    def set_categories(self, cates):
    ##        if cates:
    ##            catestemp = [db.Category(cate.strip()) for cate in cates.split(',')]
    ##            self.catesnew = [cate for cate in catestemp if not cate in self.categories]
    ##            self.categorie = tagstemp
    ##    scates = property(get_categories,set_categories)

    def comments(self):
        return Comment.all().filter('entry =', self)

    def update_archive(self):
        """Checks to see if there is a month-year entry for the
        month of current blog, if not creates it and increments count"""
        my = self.date.strftime('%b-%Y')  # May-2008
        archive = Archive.all().filter('monthyear', my).fetch(10)
        if self.entrytype == 'post':
            if archive == []:
                archive = Archive(monthyear=my)
                self.monthyear = my
                archive.put()
            else:
                # ratchet up the count
                archive[0].entrycount += 1
                archive[0].put()

    def save(self):
        """
        Use this instead of self.put(), as we do some other work here
        """

        my = self.date.strftime('%b-%Y')  # May-2008
        self.monthyear = my

        return self.put()

    def publish(self, newval=True):
        if newval:

            if not self.is_saved():
                self.save()
            if not self.is_wp:
                self.post_id = self.key().id()

            vals = {'year': self.date.year, 'month': self.date.month, 'day': self.date.day,
                    'postname': self.slug, 'post_id': self.post_id}

            if not self.link:
                if g_blog.link_format and self.slug:
                    self.link = g_blog.link_format.strip() % vals
                else:
                    self.link = '?p=%(post_id)s' % vals

            if not self.published:
                g_blog.entrycount += 1
            self.published = True

            g_blog.save()
            self.save()
        else:
            self.published = false
            if self.published:
                g_blog.entrycount -= 1
            g_blog.save()
            self.save()


class User(db.Model):
    user = CharField(null=True)
    dispname = CharField(null=True)
    website = CharField(null=True)
    isadmin = CharField(null=True)

    def __unicode__(self):
        if self.dispname:
            return self.dispname
        else:
            return self.user.nickname()

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class Comment(db.Model):
    entry = CharField(null=True)
    date = CharField(null=True)
    content = CharField(null=True)
    author = CharField(null=True)
    email = CharField(null=True)
    weburl = CharField(null=True)
    status = CharField(null=True)

    @property
    def shortcontent(self, len=20):
        return self.content[:len]


db.create_tables([Blog, Entry, Category])
# setting
logging.info('module setting reloaded')
try:
    g_blog = Blog.get(Blog.key_name == 'default')
except:
    g_blog = Blog(key_name='default')
    g_blog.save()
g_blog.get_theme()

g_blog.rootdir = os.path.dirname(__file__)
