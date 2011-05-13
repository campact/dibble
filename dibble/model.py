# -*- coding: utf-8 -*-
from . import fields
from .update import Update


class ModelError(Exception): pass
class UnboundModelError(ModelError): pass


class ModelBase(object):
    def __init__(self, *arg, **kw):
        initial = dict(*arg, **kw)
        self._update = Update()
        self._fields = {}
        self._mapper = None

        for k in dir(self):
            v = getattr(self, k)

            if isinstance(v, fields.UnboundField):
                if k in initial:
                    bound = v.bind(k, self, initial[k])

                else:
                    bound = v.bind(k, self)

                setattr(self, k, bound)
                self._fields[k] = bound

    def __iter__(self):
        for name, field in self._fields.iteritems():
            if field.defined:
                yield name, field.value


    def __getitem__(self, key):
        field = self._fields[key]

        if field.defined:
            return self._fields[key].value

        raise KeyError('Field {0!r} is not defined.'.format(key))


    def bind(self, mapper):
        self._mapper = mapper


    def save(self, *arg, **kw):
        if not self._mapper:
            raise UnboundModelError()

        return self._mapper.save(self, *arg, **kw)



class Model(ModelBase):
    pass
