# -*- coding: utf-8 -*-

import cPickle
try:
    import json
except ImportError:
    import simplejson as json

from py2xml import PythonToXML

__all__ = ('formatters', 'Formatter')

class FormattersSingleton(object):
    """This singleton takes care of all registered formatters. You can easily 
    register your own formatter for use in both the Namespace and python client.
    """
    _formatters = {}

    def __new__(cls):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        return it

    def register(self, name, formatter, override=False):
        """Register the given formatter. If there's already an formatter with
        the given `name`, you can override by setting `override` to ``True``.
        """
        if not isinstance(formatter(None, None), Formatter):
            raise TypeError(u"You can only register a Formatter not a {item}".format(item=formatter))

        if name in self._formatters and not override:
            raise AttributeError(u"{name} is already a valid format type, try a new name".format(name=name))

        self._formatters[name] = formatter

    def get_defaults(self):
        result = filter(lambda item: getattr(item[1], '__active_by_default__', True), 
            self._formatters.items())
        return dict(result).keys()

    def copy(self):
        return dict(**self._formatters)

    def __contains__(self, value):
        return value in self._formatters

    def __getitem__(self, name):
        return self._formatters.get(name)

    def __setitem__(self, *args):
        raise AttributeError

formatters = FormattersSingleton()

class Formatter(object):
    """Baseclass for Formatter-implementations"""

    def __init__(self, http_request, callback):
        """A Formatter takes the original http request (Django's one) and a
        callback name, e. g. for JSONP."""
        self.http_request = http_request
        self.callback = callback

    def build(self, value):
        """Takes care of the building process and returns the encoded data."""
        raise NotImplemented

    def kwargs(self, value, action='build'):
        """Is called within ``simpleapi``. This method invokes both the parse
        and build function when needed."""
        raise NotImplemented

    def parse(self, value):
        """Takes care of the parsing proccess and returns the decoded data."""
        raise NotImplemented

class JSONFormatter(Formatter):
    """Formatter for the JSON-format. Used by default by the python client and 
    by many Javascript-Frameworks."""
    
    __mime__ = "application/json"

    def build(self, value):
        return json.dumps(value)

    def kwargs(self, value, action='build'):
        if action == 'build':
            return self.build(value)
        elif action == 'parse':
            return self.parse(value)

    def parse(self, value):
        return json.loads(value)

class JSONPFormatter(Formatter):
    """Formatter for JSONP-format. Used for cross-domain requests. If `callback`
    isn't provided, `simpleapiCallback` is used."""
    
    __mime__ = "application/javascript"

    def build(self, value):
        func = self.callback or 'simpleapiCallback'
        return u'{func}({data})'.format(func=func, data=json.dumps(value))

    def kwargs(self, value):
        if action == 'build':
            return json.dumps(value)
        elif action == 'parse':
            return self.parse(value)

    def parse(self, value):
        return json.loads(value)

class ValueFormatter(Formatter):
    """Basic formatter for simple, fast and tiny transports (it has a lot of
    limitations, though)."""
    
    __mime__ = "text/html"

    def build(self, value):
        return value

    def kwargs(self, value, action='build'):
        if action == 'build':
            return self.build(value)
        elif action == 'parse':
            return self.parse(value)

    def parse(self, value):
        return unicode(value)

class PickleFormatter(Formatter):
    """Formatter for use the cPickle python module which supports python object
    serialization. It has the fewest limitations (ie. it can also serialize 
    datetime objects), but is a security risk and should only be used in a 
    trusted environment. It's strongly recommended that you use authentication
    mechanismen to protect your namespace. The formatter is not activated by
    default and can be enabled by putting 'pickle' into Namespace's ``__input__``
    and ``__output__`` configuration. """
    
    __mime__ = "application/octet-stream"
    __active_by_default__ = False

    def build(self, value):
        return cPickle.dumps(value)

    def kwargs(self, value, action='build'):
        if action == 'build':
            return self.build(value)
        elif action == 'parse':
            return self.parse(value)

    def parse(self, value):
        if isinstance(value, unicode):
            value = value.encode("utf-8")
        return cPickle.loads(value)

class XMLFormatter(Formatter):
    __mime__ = "text/xml"

    def build(self, value):
        return PythonToXML.dumps(value)

    def kwargs(self, value, action='build'):
        if action == 'build':
            return self.build(value)
        elif action == 'parse':
            return self.parse(value)

    def parse(self, value):
        return PythonToXML.loads(value)

formatters.register('json', JSONFormatter)
formatters.register('jsonp', JSONPFormatter)
formatters.register('value', ValueFormatter)
formatters.register('pickle', PickleFormatter)
formatters.register('xml', XMLFormatter)