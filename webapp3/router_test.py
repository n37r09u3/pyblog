"""
Serializers test
"""
import unittest

from core.decorators import action
from core.response import JsonResponse
from core.router import Router
from core.handlers import RestHandler, BaseHandler


class TestHandler(BaseHandler):
    pass


class TestRestHandler(RestHandler):
    pass


class TestDynamicRestHandler(RestHandler):
    @action(methods=['GET'], detail=False)
    def toto(self, *args, **kwargs):
        return JsonResponse(data={'ok': 42})


class BaseTestCase(unittest.TestCase):
    def test_dynamic_route(self):
        router = Router()
        handler_name = 'handler'
        router.register(handler_name, TestDynamicRestHandler)

        self.assertItemsEqual(
            [
                ('^/{}/$'.format(handler_name), TestDynamicRestHandler),
                ('^/{}$'.format(handler_name), TestDynamicRestHandler),
                ('^/{}/toto/$'.format(handler_name), TestDynamicRestHandler),
                ('^/{}/toto$'.format(handler_name), TestDynamicRestHandler),
                ('^/{}/(?P<key>[^/]+)/$'.format(handler_name), TestDynamicRestHandler),
                ('^/{}/(?P<key>[^/]+)$'.format(handler_name), TestDynamicRestHandler)
            ],
            router.urls
        )

    def test_basic_router(self):
        router = Router()
        handler_name = 'handler'
        router.register(handler_name, TestHandler)

        self.assertItemsEqual(
            [
                ('^/{}$'.format(handler_name), TestHandler),
                ('^/{}/$'.format(handler_name), TestHandler),
                ('^/{}/(?P<key>[^/]+)$'.format(handler_name), TestHandler),
                ('^/{}/(?P<key>[^/]+)/$'.format(handler_name), TestHandler)
            ],
            router.urls
        )

    def test_model_router(self):
        router = Router()
        handler_name = 'handler'
        router.register(handler_name, TestRestHandler)

        self.assertItemsEqual(
            [
                ('^/{}/$'.format(handler_name), TestRestHandler),
                ('^/{}$'.format(handler_name), TestRestHandler),
                ('^/{}/(?P<key>[^/]+)/$'.format(handler_name), TestRestHandler),
                ('^/{}/(?P<key>[^/]+)$'.format(handler_name), TestRestHandler)
            ],
            router.urls
        )


if __name__ == '__main__':
    unittest.main()
