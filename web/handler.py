from webapp3 import RequestHandler


class MyRequestHandler(RequestHandler):
    def __init__(self):
        self.template_vals = {}

    def __before__(self, *args):
        """
        Allows common code to be used for all get/post/delete methods
        """
        pass

    def __after__(self, *args):
        """
        This runs AFTER response is returned to browser.
        If you have follow-up work that you don't want to do while
        browser is waiting put it here such as sending emails etc
        """
        pass
