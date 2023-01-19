"""
Core handlers for webapp3 simple use
"""
import json
import logging
import traceback

import re
import webapp3
from webob import Response

from core.exceptions import (
    NotFound,
    NotAuthorized,
    MissingParameter,
    Forbidden,
    BadRequest,
    MissingBody,
    DispatchError
)
from core.middleware import get_middlewares
from core.response import JsonResponse, CorsResponse
from helpers.decorators import cached_property
import settings


class BaseCronHandler(webapp3.RequestHandler):
    """
    Base cron handler
    """
    def dispatch(self):
        """
        Change dispatch default behaviour and checks if cron header is present
        """
        if self.is_cron():
            return super(BaseCronHandler, self).dispatch()
        else:
            return Response(status=400, json_body={
                'error': 'This route is only callable with google cloud cron jobs'
            })

    def is_cron(self):
        """
        Verify cron headers, in local development always return TRUE
        """
        return self.request.headers.get('X-Appengine-Cron', 'false') == 'true' or settings.IS_LOCAL


class BaseHandler(webapp3.RequestHandler):
    """
    BaseHandler with some intelligence & automation
    """
    def __init__(self, *args, **kwargs):
        super(BaseHandler, self).__init__(*args, **kwargs)
        self.route_args = {}
        self.env = {}
        self.query_params = {}
        self.user = None
        self.action = None

    @cached_property
    def middlewares(self):
        """
        Cached property that load all middlewares
        :return: :py:class:`list` of :py:class:`Middleware` instances
        """
        return get_middlewares()

    def dispatch(self):
        """
        Function called to make the dispatch job.
        Calls internally :py:meth:`core.handlers.BaseHandler.apply_dispatch`
        :return: :py:class:`webob.Response`
        """
        self.action = self.request.method.lower()

        return self.apply_dispatch()

    def apply_dispatch(self):
        """
        Does the hole mechanism of dispatch.
        Loops over all middlewares before and after the dispatch method call
        .. code-block:: python
            for middleware in self.middlewares:
                middleware.process_request(self.request)
            self.route_args = self.get_route_args()
            response = self.do_dispatch()
            for middleware in self.middlewares:
                middleware.process_response(self.request, response)
        :return: :py:class:`core.response.Response`
        """
        try:
            self.query_params = dict(self.request.GET)
            self.env = self.request.GET.env

            for middleware in self.middlewares:
                if middleware.activate_on_method(self.request.method.upper()):
                    middleware.process_request(self.request)

            self.route_args = self.get_route_args()
            response = self.do_dispatch()

            for middleware in self.middlewares:
                if middleware.activate_on_method(self.request.method.upper()):
                    middleware.process_response(self.request, response)

            return response
        except NotFound as nf:
            return JsonResponse(status=404, data=str(nf) or 'Not found')
        except NotAuthorized as na:
            return JsonResponse(status=403, data=str(na) or 'Not authorized')
        except Forbidden as fo:
            return JsonResponse(status=401, data=str(fo) or 'Forbidden')
        except MissingParameter as mp:
            return JsonResponse(status=400, data=str(mp) or 'Missing parameter')
        except BadRequest as br:
            return JsonResponse(status=400, data=str(br) or 'Bad request')
        except MissingBody as mb:
            return JsonResponse(status=400, data=str(mb) or 'Request is missing a body')
        except ValueError as ve:
            return JsonResponse(status=400, data=str(ve) or 'Value error')
        except DispatchError:
            return Response(status=404)
        except Exception as err:
            logging.error('%s: %s',
                          err.__class__.__name__,
                          str(err))
            logging.error(traceback.format_exc())
            return self.handle_exception(err, self.app.debug)

    def check_action_permissions(self):
        """
        Overridable method on each handler. Allow top level check of permissions.
        For access control, override this method with your logic and return False if
        access should not be given. It will internally raise an :py:class:`core.exceptionsNotAuthorized` and
        return a 401 response
        :return: :py:class:`bool`
        """
        return True

    def do_dispatch(self):
        """
        Function that does the dispatch job
        :return: :py:class:`webob.Response`
        """
        if self.check_action_permissions() is False:
            raise NotAuthorized()

        return super(BaseHandler, self).dispatch()

    def get_body(self):
        """
        Tries to parse the request body as JSON
        :return: JSON serialized data as :py:class:`dict` instance.
        """
        _cached_body = getattr(self, '__cached_body', None)

        if _cached_body is not None:
            return _cached_body

        if self.request.body:
            try:
                json_body = json.loads(self.request.body)
                setattr(self, '__cached_body', json_body)
                return json_body
            except Exception as err:
                logging.warning('Request is missing a body: %s -> %s',
                                err.__class__.__name__, str(err))
        raise MissingBody('Request is missing a body')

    def get_route_args(self):
        """
        Parses the route arguments based on the handler url
        :return: route arguments in a :py:class:`dict` instance.
        For instance if the view url is ``r'/resource/(?P<slug>[^/]+)/'`` and the calling url is ``GET /resource/my-slug/``
        The returned dict will be formatted like this
        .. code-block:: python
           {'slug': 'my-slug'}
        .. note::
            Those route arguments are then available in each of the Handler methods in the self.route_args attribute
        """
        return self.request.route.regex.search(self.request.upath_info).groupdict()

    @classmethod
    def get_extra_actions(cls):
        actions = []

        for _method in cls.__dict__.values():
            if getattr(_method, 'is_dynamic_action', False):
                actions.append(_method)
        return actions


class RestHandler(BaseHandler):
    def list(self, request):
        """
        List operation
        :return: :py:class:`core.response.JsonResponse`
        """
        raise NotImplementedError

    def create(self, request):
        """
        :return: :py:class:`core.response.JsonResponse`
        """
        raise NotImplementedError

    def retrieve(self, request, key=None):
        """
        :return: :py:class:`core.response.JsonResponse`
        """
        raise NotImplementedError

    def update(self, request, key=None):
        """
        :return: :py:class:`core.response.JsonResponse`
        """
        raise NotImplementedError

    def partial_update(self, request, key=None):
        """
        :return: :py:class:`core.response.JsonResponse`
        """
        raise NotImplementedError

    def destroy(self, request, key=None):
        """
        :return: :py:class:`core.response.JsonResponse`
        """
        raise NotImplementedError

    def do_dispatch(self):
        """
        Dispatches the request.
        This will first check if there's a handler_method defined in the
        matched route, and if not it'll use the method correspondent to the
        request method (``get()``, ``post()`` etc).
        """
        if self.request.method.upper() == 'OPTIONS':
            return CorsResponse()

        route_args = self.get_route_args()
        route_kwargs = {}
        matched_url = None
        for url in getattr(self, 'urls', []):
            if re.match(url.regex, self.request.path_info):
                matched_url = url
                break

        if matched_url is None:
            raise NotFound('URL not found on this server')

        if matched_url.route.detail is True:
            try:
                route_kwargs['key'] = route_args['key']
            except Exception:
                return JsonResponse(status=400, data='Given urlsafe is invalid')

        if self.request.method.lower() not in matched_url.route.mapping.keys():
            raise DispatchError('Invalid method {}'.format(self.request.method))

        self.action = matched_url.route.mapping[self.request.method.lower()]
        method = getattr(self, self.action, None)
        # The handler only receives *args if no named variables are set.
        args, kwargs = route_args, route_kwargs
        if kwargs:
            args = ()

        if self.check_action_permissions() is False:
            raise NotAuthorized()
        return method(self, *args, **kwargs)
