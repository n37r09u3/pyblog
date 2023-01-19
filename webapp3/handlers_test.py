"""
Handlers test
"""
import unittest
import webapp3
import webtest

from webob import Response
from google.appengine.ext import testbed, ndb

from core.exceptions import BadRequest, NotFound
from core.decorators import action
from core.response import JsonResponse
from core.handlers import RestHandler, BaseHandler
from core.router import Router


class User(ndb.Model):
    email = ndb.StringProperty()
    last_name = ndb.StringProperty()
    first_name = ndb.StringProperty()
    age = ndb.IntegerProperty()


class UserApi(RestHandler):
    """
    User example API
    """
    def list(self, request):
        users = User.query().fetch()

        return JsonResponse(data={
            'results': [
                user.to_dict()
                for user in users
            ],
            'count': len(users)
        })

    def create(self, request):
        data = self.get_body()

        try:
            new_user = User(email=data['email'])
            new_user.put()

            return JsonResponse(
                status=201,
                data=new_user.to_dict()
            )
        except Exception as err:
            raise BadRequest

    def retrieve(self, request, key=None):
        user = User.query(User.email == key).fetch()

        if user:
            return JsonResponse(data=user[0].to_dict())

        raise NotFound

    def destroy(self, request, key=None):
        user_key = User.query(User.email == key).fetch(keys_only=True)

        if user_key:
            user_key[0].delete()
            return JsonResponse(status=204)

        raise NotFound

    @action(methods=['GET'], detail=False)
    def toto(self, *args, **kwargs):
        return Response(body='toto')

    @action(methods=['GET'], detail=True)
    def tata(self, request, key):
        return Response(body=key)


class DynamicAPIModelHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        ndb.get_context().clear_cache()

        router = Router()
        router.register('user', UserApi)
        app = webapp3.WSGIApplication(router.urls)
        self.testapp = webtest.TestApp(app)
        self.entity = User(
            email='admin@test.com',
            first_name='admin',
            last_name='test',
            age=28
        )
        self.entity.put()

    def test_dispatch_toto(self):
        response = self.testapp.get('/user/toto')
        self.assertEquals(response.body, 'toto')

    def test_dispatch_toto_bad_method(self):
        response = self.testapp.put('/user/toto', expect_errors=True)
        self.assertEquals(response.status_code, 404)

    def test_dispatch_toto_slash(self):
        response = self.testapp.get('/user/toto/')
        self.assertEquals(response.body, 'toto')

    def test_dispatch_tata(self):
        response = self.testapp.get('/user/admin@test.com/tata')
        self.assertEquals(response.body, 'admin@test.com')

    def test_dispatch_tata_with_slash(self):
        response = self.testapp.get('/user/admin@test.com/tata/')
        self.assertEquals(response.body, 'admin@test.com')

    def test_dispatch_tata_bad_method(self):
        response = self.testapp.post('/user/admin@test.com/tata', expect_errors=True)
        self.assertEquals(response.status_code, 404)


class APIUserHandler(BaseHandler):
    def get(self, *args, **kwargs):
        return Response(body='get')

    def post(self, *args, **kwargs):
        return Response(body='post')

    def put(self, *args, **kwargs):
        return Response(body='put')

    def delete(self, *args, **kwargs):
        return Response(body='delete')

    def patch(self, *args, **kwargs):
        return Response(body='patch')


class APIHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        ndb.get_context().clear_cache()

        router = Router()
        router.register('user', APIUserHandler)
        app = webapp3.WSGIApplication(router.urls)
        self.testapp = webtest.TestApp(app)

    def test_dispatch_get(self):
        response = self.testapp.get('/user/')
        self.assertEquals(response.body, 'get')

    def test_dispatch_post(self):
        response = self.testapp.post('/user/')
        self.assertEquals(response.body, 'post')

    def test_dispatch_put(self):
        response = self.testapp.put('/user/')
        self.assertEquals(response.body, 'put')

    def test_dispatch_patch(self):
        response = self.testapp.patch('/user/')
        self.assertEquals(response.body, 'patch')

    def test_dispatch_delete(self):
        response = self.testapp.delete('/user/')
        self.assertEquals(response.body, 'delete')


if __name__ == '__main__':
    unittest.main()
