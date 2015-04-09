# -*- coding: utf-8 -*-
"""
`dibble.operations` contains implementations of MongoDBs atomic update operations as described in
http://docs.mongodb.org/manual/reference/operator/
"""
import collections
import functools


class UnknownFieldError(KeyError):
    """raised by `rename` and `unset` when trying to rename a class member that is not a field"""
    pass


class DuplicateFieldError(KeyError):
    """raised by `rename` when the new field name is already in use"""
    pass


def reloading(fn):
    """decorator that automatically reloads the model if necessary before calling the wrapped method"""
    @functools.wraps(fn)
    def wrapper(self, *arg, **kw):
        self._reload(force=False)
        return fn(self, *arg, **kw)

    return wrapper


class SetMixin(object):
    @reloading
    def set(self, value):
        """set field to new value

        :param value: new value
        """
        self._setvalue(value)
        self._model._update.set(self.name, value)


class IncrementMixin(object):
    @reloading
    def inc(self, increment):
        """add `increment` to field value"""
        if self.defined:
            self._setvalue(self._value + increment)

        else:
            self._setvalue(increment)

        self._model._update.inc(self.name, increment)


class RenameMixin(object):
    def rename(self, new):
        """rename field to name given by `new`"""
        f = getattr(self._model, self.name, None)

        if f is not None:
            if hasattr(self._model, new):
                raise DuplicateFieldError('Field {0!r} is already present on Model'.format(new))

            else:
                oldname = self.name
                delattr(self._model, self.name)
                setattr(self._model, new, f)
                f._name = new
                self._model._update.rename(oldname, new)

        else:
            raise UnknownFieldError('Unknown Field: {0!r}'.format(self.name))


class UnsetMixin(object):
    @reloading
    def unset(self):
        """unset this field"""
        f = getattr(self._model, self.name, None)

        if f is not None:
            self._undefine()
            self._model._update.unset(self.name)

        else:
            raise UnknownFieldError('Unknown Field: {0!r}'.format(self.name))


class PushMixin(object):
    @reloading
    def push(self, value):
        """append `value` to the current value of the field. Will fail if current field value is not a list."""
        if self.defined:
            self._setvalue(self._value + [value])

        else:
            self._setvalue([value])

        self._model._update.push(self.name, value)


class PushAllMixin(object):
    @reloading
    def push_all(self, values):
        """append all values to the current value of the field. Will fail is current field value is not a list"""
        if self.defined:
            self._setvalue(self._value + values)

        else:
            self._setvalue(values[:])

        self._model._update.pushAll(self.name, values)


class AddToSetMixin(object):
    @reloading
    def add_to_set(self, value):
        """append value to the current value of the field if it is not already in the list. Will fail is current field
        value is not a list
        """
        newvalue = (self._value[:] if self.defined else [])

        if isinstance(value, collections.Mapping) and ('$each' in value):
            for v in value['$each']:
                if v not in newvalue:
                    newvalue.append(v)

        else:
            if value not in newvalue:
                newvalue.append(value)

        self._setvalue(newvalue)
        self._model._update.addToSet(self.name, value)


class PopMixin(object):
    @reloading
    def pop(self, first=False):
        """remove last (or first) item from current field value list. Will fail is current field value is not a list.

        :param first: remove first item instead of last
        """
        if first:
            self._setvalue(self._value[1:])

        else:
            self._setvalue(self._value[:-1])

        self._model._update.pop(self.name, first)


class PullMixin(object):
    @reloading
    def pull(self, value):
        """remove an item by `value` from current field value list. Will fail is current field value is not a list."""
        if isinstance(value, dict):
            raise NotImplementedError('using pull() with a match criteria is not supported')

        elif self._value:
            self._setvalue([x for x in self._value if x != value])

        self._model._update.pull(self.name, value)


class PullAllMixin(object):
    @reloading
    def pull_all(self, values):
        """remove each item in `values` from current field value list. Will fail is current field value is not a
        list."""
        self._setvalue([x for x in self._value if (x not in values)])
        self._model._update.pullAll(self.name, values)
