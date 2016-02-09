# -*- coding: utf-8 -*-
import pymongo.cursor


class ModelCursor(pymongo.cursor.Cursor):
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
        #: The :class:`dibble.model.Model` subclass associated with this mapper.
        self.model = model

        #: The :class:`pymongo.collection.Collection` instance associated with this mapper.
        self.collection = collection

    def __call__(self, *arg, **kw):
        """create a new model instance bound to this ModelMapper. The model's :meth:`dibble.model.Model.save` method
        will insert the model into the underlying :attr:`collection`.
        """
        doc = self.model(*arg, **kw)
        doc.bind(self)
        return doc

    def with_options(self, codec_options=None, read_preference=None,
                     write_concern=None, read_concern=None):
        """
        Get a clone of this ModelMapper that uses a clone of the current collection but with the specified settings.
        Parameters are passed to :meth:`pymongo.collection.Collection.with_options` untouched.

        :return: A clone of this :class:`~dibble.mapper.ModelMapper`.
        """
        return ModelMapper(self.model, self.collection.with_options(codec_options, read_preference,
                                                                    write_concern, read_concern))

    def find(self, *args, **kw):
        """find documents by spec, which is a MongoDB query document. Additional arguments will be passed to the
        :class:`ModelCursor` constructor.

        :return: A new :class:`ModelCursor` instance with query results
        """
        return ModelCursor(self, self.collection, *args, **kw)

    def find_one(self, filter_or_id=None, *arg, **kw):
        """find first matching document by spec, which is a MongoDB query document. Additional arguments will be
        passed to the :meth:`pymongo.collection.Collection.find_one` method of the :attr:`collection`.

        :param `filter_or_id` (optional): a dictionary specifying
            the query to be performed OR any other type to be used as
            the value for a query for ``"_id"``.
        :return: A :class:`dibble.model.Model` instance or None if no matching document was found
        """

        doc = self.collection.find_one(filter_or_id, *arg, **kw)
        return self(doc) if doc is not None else None

    def __getattr__(self, item):
        """For all other attributes it's just a proxy for associated :attr:`collection`."""

        return getattr(self.collection, item)
