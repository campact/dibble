# -*- coding: utf-8 -*-
import collections


class InvalidOperatorError(ValueError):
    pass


class DuplicateFieldError(ValueError):
    pass


class FieldDict(dict):
    def __setitem__(self, k, v):
        if k in self:
            raise DuplicateFieldError('Field "{0}" already set.'.format(k))

        super(FieldDict, self).__setitem__(k, v)

    def update(self, E=None, **F):
        raise NotImplementedError()


class OperatorDict(collections.defaultdict):
    OPERATORS = ('$inc', '$rename', '$set', '$unset', '$push', '$pushAll', '$addToSet',
                 '$pop', '$pull', '$pullAll')

    def __init__(self):
        super(OperatorDict, self).__init__(FieldDict)

    def __setitem__(self, k, v):
        if k not in self.OPERATORS:
            raise InvalidOperatorError('"{0}" is not a valid operator'.format(k))

        super(OperatorDict, self).__setitem__(k, v)

    def update(self, E=None, **F):
        raise NotImplementedError()


class Update(object):
    def __init__(self):
        self._ops = OperatorDict()

    def __iter__(self):
        return self._ops.iteritems()

    def __contains__(self, item):
        return any(item in fields for fields in self._ops.values())

    def clear(self):
        self._ops.clear()

    def drop_field(self, field):
        empty_keys = []

        for k, updates in self._ops.iteritems():
            updates.pop(field, None)

            if not updates:
                empty_keys.append(k)

        for k in empty_keys:
            del self._ops[k]

    def set(self, field, value):
        self._ops['$set'][field] = value

    def inc(self, field, increment):
        """
        >>> update = Update()
        >>> update.inc('foo', 'bar')
        >>> dict(update)
        {'$inc': {'foo': 'bar'}}
        """
        self._ops['$inc'][field] = increment

    def rename(self, old, new):
        """
        >>> update = Update()
        >>> update.rename('old', 'new')
        >>> dict(update)
        {'$rename': {'old': 'new'}}
        """
        self._ops['$rename'][old] = new

    def unset(self, name):
        self._ops['$unset'][name] = 1

    def push(self, name, value):
        self._ops['$push'][name] = value

    def pushAll(self, name, values):
        self._ops['$pushAll'][name] = values

    def addToSet(self, name, value):
        self._ops['$addToSet'][name] = value

    def pop(self, name, first=False):
        v = (-1 if first else 1)
        self._ops['$pop'][name] = v

    def pull(self, name, value):
        self._ops['$pull'][name] = value

    def pullAll(self, name, values):
        self._ops['$pullAll'][name] = values
