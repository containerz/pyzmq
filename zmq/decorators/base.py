from functools import wraps

from zmq.utils.strtypes import basestring


class ZDecoratorBase(object):

    def __init__(self, target):
        self.target = target

    def __call__(self, *dec_args, **dec_kwargs):
        self.kwname = None
        self.dec_args = dec_args
        self.dec_kwargs = dec_kwargs

        self.pop_kwname()

        def decorator(func):
            @wraps(func)
            def wrapper(*wrap_args, **wrap_kwargs):
                self.wrap_args = wrap_args
                self.wrap_kwargs = wrap_kwargs

                self.hook('preinit')

                with self.target(*self.dec_args, **self.dec_kwargs) as obj:
                    self.hook('postinit')

                    if self.kwname and self.kwname not in self.wrap_kwargs:
                        self.wrap_kwargs[self.kwname] = obj
                    elif self.kwname and self.kwname in self.wrap_kwargs:
                        raise TypeError(
                            "{0}() got multiple values for"
                            " argument '{1}'".format(
                                func.__name__, self.kwname))
                    else:
                        self.wrap_args = (obj,) + self.wrap_args

                    self.hook('preexec')
                    func(*self.wrap_args, **self.wrap_kwargs)
                    self.hook('postexec')

                self.hook('cleanup')

            return wrapper

        return decorator

    def hook(self, func):
        getattr(self, 'hook_{0}'.format(func), self.nop)()

    @staticmethod
    def nop(*args, **kwargs):
        pass  # and save the world silently

    def pop_kwname(self):
        if isinstance(self.dec_kwargs.get('name'), basestring):
            self.kwname = self.dec_kwargs.pop('name')
        elif (len(self.dec_args) >= 1 and
              isinstance(self.dec_args[0], basestring)):
            self.kwname = self.dec_args[0]
            self.dec_args = self.dec_args[1:]
