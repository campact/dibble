# -*- coding: utf-8 -*-
import warnings

import pymongo
from . import fields
from .update import Update


class ModelError(Exception):
    """base class for all model related errors"""
    pass


class UnboundModelError(ModelError):
    """attempted usage of model that was not bound to a mapper"""
    pass


class UnsavedModelError(ModelError):
    """raised when reload was called for an unsaved model"""
    pass


class UndefinedFieldError(KeyError):
    """raised when trying to access an undefined field"""
    pass


class ModelBase(object):
    """base class for all dibble models"""
    _id = fields.Field()

    def __init__(self, *arg, **kw):
        initial = dict(*arg, **kw)
        self._update = Update()
        self._fields = {}
        self._mapper = None
        self._requires_reload = False

        for k in dir(self):
            # lookup in class to avoid triggering property evaluation
            v = getattr(self.__class__, k, None)

            if isinstance(v, fields.UnboundField):
                field = getattr(self, k)

                if k in initial:
                    bound = field.bind(k, self, initial[k])

                else:
                    bound = field.bind(k, self)

                setattr(self, k, bound)
                self._fields[k] = bound

    def __iter__(self):
        for name, field in self._fields.iteritems():
            if field.defined:
                yield (name, field.value)

    def __delattr__(self, item):
        if item in self._fields:
            del self._fields[item]
            setattr(self, item, None)

        else:
            super(ModelBase, self).__delattr__(item)

    def __setattr__(self, key, value):
        if isinstance(value, fields.BaseField) and key not in self._fields:
            self._fields[key] = value

        elif isinstance(value, fields.UnboundField):
            value = value.bind(key, self)
            self._fields[key] = value

        super(ModelBase, self).__setattr__(key, value)

    def __getattribute__(self, item):
        v = super(ModelBase, self).__getattribute__(item)

        if v is None and isinstance(getattr(self.__class__, item, None), fields.UnboundField):
            raise AttributeError('{0!r} object has no attribute {1!r}'.format(type(self), item))

        return v

    def __getitem__(self, key):
        field = self._fields[key]

        if field.defined:
            return self._fields[key].value

        raise UndefinedFieldError('Field {0!r} is not defined.'.format(key))

    def __repr__(self):
        return '<{0}({1!r})>'.format(self.__class__.__name__, dict(self))

    @property
    def is_new(self):
        """returns whether the model was saved before or is completely new"""
        return not self._id.defined

    def bind(self, mapper):
        """bind this model to a :class:`~dibble.mapper.ModelMapper`. Usually this is handled by the mapper when it
        returns a model
        """
        self._mapper = mapper

    def reload(self, force=True):
        """reload model from the database if necessary

         :param force: reload model even if unnecessary
         """
        if self._requires_reload or force:
            if not self._mapper:
                raise UnboundModelError()

            if not self._id.defined:
                raise UnsavedModelError()

            new = self._mapper.with_options(read_preference=pymongo.ReadPreference.PRIMARY).find_one(
                {'_id': self._id.value})

            for name, field in new._fields.items():
                if name in self._fields:
                    self._fields[name].reset(field._value)

            self._requires_reload = False

    def save(self, _id=None, codec_options=None, write_concern=None):
        """Save model data to database. Requires the model to be bound to a mapper first. Additional arguments
        will be passed to :meth:`~dibble.mapper.ModelMapper.save` method of the mapper.

        :param _id: Write a custom id. This is only respected when the model was never saved before.
        :param codec_options: See :class:`bson.codec_options.CodecOptions`
        :param write_concern: See :class:`pymongo.write_concern.WriteConcern`
        """
        if not self._mapper:
            raise UnboundModelError()

        self._requires_reload = False

        oid = None
        if self.is_new:
            doc = dict(self)

            if _id:
                doc['_id'] = _id

            result = self._mapper.with_options(codec_options=codec_options, write_concern=write_concern).insert_one(doc)

            # Note: Despite the statement in the documentation of InsertOneResult it should be safe to access the
            # id attribute even after unacknowledged writes (w=0) because the id is created in the driver.
            # http://api.mongodb.org/python/3.0/api/pymongo/results.html#pymongo.results.InsertOneResult
            oid = result.inserted_id
            self._id.reset(oid)

        else:
            doc = dict(self)
            upd = dict(self._update)
            oid = doc.get('_id', None)

            # do not perform update with empty update document as
            # this would overwrite/clear existing data
            if upd:
                self._mapper.with_options(codec_options=codec_options, write_concern=write_concern).update_one(
                    {'_id': oid}, upd)

        self._update.clear()
        self._requires_reload = True

        return oid


class Model(ModelBase):
    """A Model describes the structure of a MongoDB document. It consists of :class:`~dibble.field.Field` instances
    which can then be used to manipulate the document data.

    Models should be defined by inheriting from :class:`~dibble.model.Model` and adding the wanted Fields to the class.
    """
    pass
