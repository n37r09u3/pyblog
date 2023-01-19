
"""
Middleware tests
"""
import unittest
import webapp3
import webtest

from webob import Response
from google.appengine.ext import testbed, ndb

import settings
from core.handlers import BaseHandler
from core.middleware import Middleware


class TestRequestMiddleware(Middleware):
    def process_request(self, request):
        request.value = 'request'


class TestResponseMiddleware(Middleware):
    def process_response(self, request, response):
        response.body = 'response'


class APIUserHandler(BaseHandler):
    def get(self, *args, **kwargs):
        return Response(body=self.request.value)

    def post(self, *args, **kwargs):
        return Response()


class APIHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_app_identity_stub()

        ndb.get_context().clear_cache()

        app = webapp3.WSGIApplication([
            ('/user/', APIUserHandler)
        ])
        self.testapp = webtest.TestApp(app)

    def test_request_middleware(self):
        setattr(settings, 'MIDDLEWARE_CLASSES', ['core.middleware_test.TestRequestMiddleware'])

        response = self.testapp.get('/user/')
        self.assertEquals(response.body, 'request')

    def test_response_middleware(self):
        setattr(settings, 'MIDDLEWARE_CLASSES', ['core.middleware_test.TestResponseMiddleware'])

        response = self.testapp.post('/user/')
        self.assertEquals(response.body, 'response')


if __name__ == '__main__':
    unittest.main()
