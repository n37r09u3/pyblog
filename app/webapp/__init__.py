import cgi,os
#import StringIO
import logging
import re
import sys
import traceback
#import urlparse
import webob
import wsgiref.headers
import wsgiref.util
from webapp3 import *

RE_FIND_GROUPS = re.compile('\(.*?\)')
class RequestHandler(RequestHandler):
    def __init__(self):
        self.template_vals = {}

    def __before__(self,*args):
        """
        Allows common code to be used for all get/post/delete methods
        """
        pass

    def __after__(self,*args):
        """
        This runs AFTER response is returned to browser.
        If you have follow-up work that you don't want to do while
        browser is waiting put it here such as sending emails etc
        """
        pass


class WSGIApplication3(WSGIApplication):
    """
    Modifyed to add new methods __before__ and __after__
    before the get/post/delete/etc methods and then
    AFTER RESPONSE.  This is important because it means you
    can do work after the response has been returned to the browser
    """
    def __init__(self, url_mapping, debug=False):
        """Initializes this application with the given URL mapping.

        Args:
            url_mapping: list of (URI, RequestHandler) pairs (e.g., [('/', ReqHan)])
            debug: if true, we send Python stack traces to the browser on errors
        """
        self._init_url_mappings(url_mapping)
        self.__debug = debug
        WSGIApplication.active_instance = self
        self.current_request_args = ()

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        request = Request(environ)
        response = Response()

        WSGIApplication.active_instance = self

        handler = None
        groups = ()
        for regexp, handler_class in self._url_mapping:
            match = regexp.match(request.path)
            if match:
                handler = handler_class()
                handler.initialize(request, response)
                groups = match.groups()
                break
        self.current_request_args = groups

        if handler:
            try:
                handler.__before__(*groups)
                method = environ.get('REQUEST_METHOD',"GET")
                if method == 'GET':
                    handler.get(*groups)
                elif method == 'POST':
                    handler.post(*groups)
                elif method == 'HEAD':
                    handler.head(*groups)
                elif method == 'OPTIONS':
                    handler.options(*groups)
                elif method == 'PUT':
                    handler.put(*groups)
                elif method == 'DELETE':
                    handler.delete(*groups)
                elif method == 'TRACE':
                    handler.trace(*groups)
                else:
                    handler.error(501)
                response.wsgi_write(start_response)
                handler.__after__(*groups)
            except Exception as e:
                handler.handle_exception(e, self.__debug)
        else:
            response.set_status(404)
            response.wsgi_write(start_response)
        return ['']
    def _init_url_mappings(self, handler_tuples):
        """Initializes the maps needed for mapping urls to handlers and handlers
        to urls.

        Args:
          handler_tuples: list of (URI, RequestHandler) pairs.
        """

        handler_map = {}

        pattern_map = {}

        url_mapping = []

        for regexp, handler in handler_tuples:

            try:
                handler_name = handler.__name__
            except AttributeError:
                pass
            else:
                handler_map[handler_name] = handler

            if not regexp.startswith('^'):
                regexp = '^' + regexp
            if not regexp.endswith('$'):
                regexp += '$'

            if regexp == '^/form$':
                logging.warning('The URL "/form" is reserved and will not be matched.')

            compiled = re.compile(regexp)
            url_mapping.append((compiled, handler))

            num_groups = len(RE_FIND_GROUPS.findall(regexp))
            handler_patterns = pattern_map.setdefault(handler, [])
            handler_patterns.append((compiled, num_groups))

        self._handler_map = handler_map
        self._pattern_map = pattern_map
        self._url_mapping = url_mapping