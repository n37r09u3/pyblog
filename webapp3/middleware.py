"""
Base middleware class
"""
import importlib
import webapp3

import settings


def load_class(full_class_string):
    """
    Dynamically load a class from a string
    """
    class_data = full_class_string.split('.')
    module_path = '.'.join(class_data[:-1])
    class_str = class_data[-1]

    module = importlib.import_module(module_path)
    # Finally, we retrieve the Class
    return getattr(module, class_str, None)


def get_middlewares():
    """
    Return all middleware classes
    """
    middlewares = []

    for middleware in getattr(settings, 'MIDDLEWARE_CLASSES', []):
        middlewares.append(load_class(middleware)())

    return middlewares


class Middleware(object):
    """
    Base middleware class
    """
    ACTIVATE_ON_METHODS = webapp3.WSGIApplication.allowed_methods.union(('PATCH',))

    def activate_on_method(self, method):
        return method.upper() in self.ACTIVATE_ON_METHODS

    def process_request(self, request):
        """
        Will be called before handler
        """
        pass

    def process_response(self, request, response):
        """
        Will be called after handler
        """
        pass
