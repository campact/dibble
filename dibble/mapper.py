# -*- coding: utf-8 -*-
from pymongo.cursor import Cursor as PymongoCursor


class ModelCursor(PymongoCursor):
    """custom :class:`pymongo.cursor.Cursor` subclass that returns model instances"""
    def __init__(self, mapper, *arg, **kw):
        super(ModelCursor, self).__init__(*arg, **kw)
        self.mapper = mapper

    def __getitem__(self, key):
        doc = super(ModelCursor, self).__getitem__(key)
        return self.mapper(doc)

    def next(self):
        doc = super(ModelCursor, self).next()
        return self.mapper(doc)


class ModelMapper(object):
    """The ModelMapper is the primary link between a :class:`pymongo.collection.Collection` and
    :class:`dibble.model.Model`. It is used to proxy most methods of the collection and wrap their returned values in
    :class:`dibble.model.Model` instances.

    :param dibble.model.Model model: model class for documents in the collection
    :param pymongo.collection.Collection collection: underlying collection instance for data storage
    """
    def __init__(self, model, collection):
        self.model = model
        self.collection = collection

    def __call__(self, *arg, **kw):
        """create a new model instance bound to this ModelMapper. The model's :meth:`dibble.model.Model.save` method
        will insert the model into the underlying :attr:`collection`.
        """
        doc = self.model(*arg, **kw)
        doc.bind(self)
        return doc

    def count(self):
        """number of documents in the underlying :attr:`collection`"""
        return self.collection.count()

    def find(self, spec=None, *args, **kw):
        """find documents by spec, which is a MongoDB query document. Additional arguments will be passed to the
        :class:`ModelCursor` constructor.

        :param dict spec: MongoDB query document
        :return: new `ModelCursor` instance with query results
        """
        spec = spec or {}
        kw.setdefault('slave_ok', self.collection.slave_okay)
        kw.setdefault('read_preference', self.collection.read_preference)

        if 'tag_sets' not in kw:
            kw['tag_sets'] = self.collection.tag_sets

        if 'secondary_acceptable_latency_ms' not in kw:
            kw['secondary_acceptable_latency_ms'] = self.collection.secondary_acceptable_latency_ms

        return ModelCursor(self, self.collection, spec, *args, **kw)

    def find_one(self, spec=None, *arg, **kw):
        """find first matching document by spec, which is a MongoDB query document. Additional arguments will be
        passt to the :meth:`~pymongo.Collection.find_one` method of the :attr:`collection`.

        :param dict spec: MongoDB query document
        :return: :attr:`model` instance or None if no matching document was found
        """
        spec = spec or {}
        doc = self.collection.find_one(spec, *arg, **kw)

        return (self(doc) if doc is not None else None)

    def update(self, spec, doc, *arg, **kw):
        """update documents in :attr:`collection` matching query document `spec` with the updates in `doc`.
        This method proxies :meth:`pymongo.Collection.update`
        """
        return self.collection.update(spec, doc, *arg, **kw)

    def save(self, doc, *arg, **kw):
        """save document `doc` into the collection
        This method proxies :meth:`pymongo.Collection.save`
        """
        return self.collection.save(doc, *arg, **kw)
