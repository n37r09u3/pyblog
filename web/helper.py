from functools import wraps


def requires_admin(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.is_login:
            # self.redirect(users.create_login_url(self.request.uri))
            return
        elif not self.is_admin:
            return self.error(403)
        else:
            return method(self, *args, **kwargs)

    return wrapper


class Pager(object):
    def __init__(self, model=None, query=None, items_per_page=10):
        if model:
            self.query = model.all()
        elif query:
            self.query = query

        self.items_per_page = items_per_page

    def fetch(self, p):
        max_offset = self.query.count()
        n = max_offset / self.items_per_page
        if max_offset % self.items_per_page != 0:
            n += 1

        if p < 0 or p > n:
            p = 1
        offset = (p - 1) * self.items_per_page
        results = self.query.fetch(self.items_per_page, offset)

        links = {'prev': p - 1, 'next': p + 1, 'last': n}
        if links['next'] > n:
            links['next'] = 0

        return (results, links)
