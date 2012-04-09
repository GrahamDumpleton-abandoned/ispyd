import sys

# From Python 3.X. In older Python versions it fails if attributes do
# not exist and don't maintain a __wrapped__ attribute.

WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__doc__', '__annotations__')
WRAPPER_UPDATES = ('__dict__',)

def update_wrapper(wrapper,
                   wrapped,
                   assigned = WRAPPER_ASSIGNMENTS,
                   updated = WRAPPER_UPDATES):
    """Update a wrapper function to look like the wrapped function

       wrapper is the function to be updated
       wrapped is the original function
       assigned is a tuple naming the attributes assigned directly
       from the wrapped function to the wrapper function (defaults to
       functools.WRAPPER_ASSIGNMENTS)
       updated is a tuple naming the attributes of the wrapper that
       are updated with the corresponding attribute from the wrapped
       function (defaults to functools.WRAPPER_UPDATES)
    """
    wrapper.__wrapped__ = wrapped
    for attr in assigned:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass
        else:
            setattr(wrapper, attr, value)
    for attr in updated:
        getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
    # Return the wrapper so this can be used as a decorator via partial()
    return wrapper

# Generic object wrapper which tries to proxy everything through to
# the wrapped object and also preserve introspection abilties.

class ObjectWrapper(object):

    def __init__(self, wrapped):
        if type(wrapped) == type(()):
            (instance, wrapped) = wrapped
        else:
            instance = None

        self._ispyd_instance = instance
        self._ispyd_next_object = wrapped

        try:
            self._ispyd_last_object = wrapped._ispyd_last_object
        except:
            self._ispyd_last_object = wrapped

        for attr in WRAPPER_ASSIGNMENTS:
            try:
                value = getattr(wrapped, attr)
            except AttributeError:
                pass
            else:
                object.__setattr__(self, attr, value)

    def __setattr__(self, name, value):
        if not name.startswith('_ispyd_'):
            setattr(self._ispyd_next_object, name, value)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        return getattr(self._ispyd_next_object, name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        descriptor = self._ispyd_next_object.__get__(instance, owner)
        return self._ispyd_new_object((instance, descriptor))

    def _ispyd_new_object(self, wrapped):
        return self.__class__(wrapped)

    def __dir__(self):
        return dir(self._ispyd_next_object)

    def __call__(self, *args, **kwargs):
        return self._ispyd_next_object(*args, **kwargs)
