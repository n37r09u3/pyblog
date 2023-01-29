from functools import wraps
def printinfo(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        print(self)  # .__name__
        print(dir(self))
        for x in self.__dict__:
            print(x)
        return method(self, *args, **kwargs)

    return wrapper