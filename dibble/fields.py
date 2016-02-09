# -*- coding: utf-8 -*-
"""
"""
import collections
from dibble.operations import SetMixin, IncrementMixin, RenameMixin, UnsetMixin, PushMixin, PushAllMixin
from dibble.operations import AddToSetMixin, PopMixin, PullMixin, PullAllMixin


class InvalidatedSubfieldError(Exception):
    """
    Error raised when using a Subfield that has been invalidated by updates to parent Fields
    """
    pass


#: used for undefined defaults and initial values
undefined = type('Undefined', (object, ), {'__nonzero__': lambda s: False})()
#: used for unknown values in reset-calls
unknown = type('Unknown', (object, ), {'__nonzero__': lambda s: False})()


class FieldMeta(type):
    """
    MetaClass of BaseField class. Ensures that all BaseField instances are turned into UnboundField instances which
    are later used by the instance of :class:`dibble.model.Model` and bound to it.
    """
    def __call__(cls, *arg, **kw):
        if '_model' in kw:
            if kw['_model'] is None:
                raise ValueError('model cannot be None')

            return type.__call__(cls, *arg, **kw)

        return UnboundField(cls, *arg, **kw)


class UnboundField(object):
    """
    All Fields are replaced by :class:`UnboundField` instances by the :class:`FieldMeta` MetaClass.
    A :class:`UnboundField` is not usable for anything until bind() was called with a Model instance.
    This is used so that :class:`Field` instances get a reference to their associated :class:`dibble.model.Model`
    instance.
    """
    def __init__(self, field_class, *arg, **kw):
        self.field_class = field_class
        self.arg = arg
        self.kw = kw

    def bind(self, name, model, initial=undefined):
        return self.field_class(_name=name, _model=model, _initial=initial, *self.arg, **self.kw)


class BaseField(object):
    """Provides a low-level API for access and manipulation of the field values.
    Handles default and initial values, field name and the :class:`dibble.model.Model` reference.
    """
    __metaclass__ = FieldMeta

    def __init__(self, default=undefined, _name=None, _initial=undefined, _model=undefined):
        self._default = default
        self._value = (_initial if _initial is not undefined else self.default)
        self._name = _name
        self._model = _model
        self.initial = _initial

    def __call__(self):
        return self.value

    @property
    def name(self):
        """name (document key) of this Field"""
        return self._name

    @property
    def defined(self):
        """True if this Field was assigned a value"""
        return self._value is not undefined

    @property
    def default(self):
        """default value of this Field"""
        return self._default() if isinstance(self._default, collections.Callable) else self._default

    @property
    def value(self):
        """current value of this Field"""
        if self._name != '_id':
            self._reload(force=False)

        return self._value if self.defined else None

    def reset(self, value=unknown):
        """reset field to it's initial value or default value if no initial value was given. Can also be used to
        reset the field to a specified value that will be used as the new initial value for this field.

        :param value: new initial value of field
        """
        if value is unknown:
            self._value = (self.initial if self.initial is not undefined else self.default)
            self._model._update.drop_field(self.name)

        else:
            self.initial = value
            self.reset()

    def _setvalue(self, value):
        self._value = value

    def _undefine(self):
        self._setvalue(undefined)

    def _reload(self, *arg, **kw):
        self._model.reload(*arg, **kw)


class Field(BaseField, SetMixin, IncrementMixin, RenameMixin, UnsetMixin, PushMixin, PushAllMixin, AddToSetMixin,
            PopMixin, PullMixin, PullAllMixin):
    """:class:`Field` combines the low-level API provided by :class:`BaseField` with the higher-level operations from
    :mod:`dibble.operations`.
    """
    def __init__(self, default=undefined, _name=None, _initial=undefined, _model=None):
        super(Field, self).__init__(default, _name, _initial, _model)
        self._subfields = {}

    def _setvalue(self, value):
        super(Field, self)._setvalue(value)
        self._reset_subfields()

    def _reset_subfields(self):
        if self._subfields:
            invalidated_subfields = []
            if self._value is undefined:
                for key, field in self._subfields.items():
                    field._invalidate()
                    invalidated_subfields.append(key)

            elif isinstance(self._value, collections.Mapping):
                for key, field in self._subfields.items():
                    if key in self._value:
                        v = self._value[key]
                        field.reset(v)

                    else:
                        field._invalidate()
                        invalidated_subfields.append(key)

            else:
                for key, field in self._subfields.items():
                    field._invalidate()
                    invalidated_subfields.append(key)

            for key in invalidated_subfields:
                self._subfields.pop(key)

    def reset(self, value=unknown):
        super(Field, self).reset(value)

        if value is not unknown:
            self._reset_subfields()

    reset.__doc__ = BaseField.reset.__doc__

    def subfield(self, key):
        """get a :class:`Subfield` for the given key"""
        if key not in self._subfields:
            sf = Subfield(parent=self)

            if self.defined:
                if isinstance(self._value, collections.Mapping):
                    if key in self._value:
                        sf_initial = self._value[key]
                        bsf = sf.bind(key, self._model, initial=sf_initial)

                    else:
                        bsf = sf.bind(key, self._model)

                else:
                    raise ValueError('Cannot create subfield for {0!r}'.format(self._value))

            else:
                bsf = sf.bind(key, self._model)

            self._subfields[key] = bsf

        return self._subfields[key]

    def __getitem__(self, item):
        return self.subfield(item)

    __getitem__.__doc__ = subfield.__doc__


class Subfield(Field):
    """Subfields can be used to access and manipulate nested documents. It supports the full set of the Field API.

    Example usage::

        subfield = field['subfield']
        subfield.set('foobar')
    """
    def __init__(self, default=undefined, _name=None, _initial=undefined, _model=None, parent=None):
        super(Subfield, self).__init__(default=default, _name=_name, _initial=_initial, _model=_model)
        self.parent = parent

    @property
    def name(self):
        return '{0}.{1}'.format('.'.join(x._name for x in reversed(self.parents)), self._name)

    @property
    def parents(self):
        """get list of parent fields of this subfield"""
        parentlist = []
        field = self.parent

        while field is not None:
            parentlist.append(field)
            field = getattr(field, 'parent', None)

        return parentlist

    def _setvalue(self, value):
        if self.parent is None:
            raise InvalidatedSubfieldError('Subfield {0!r} was invalidated by an update to it\'s '
                                           'parent Field.'.format(self._name))

        super(Subfield, self)._setvalue(value)

        parents = self.parents
        parent, key, v = parents[0], self._name, value

        while parent is not None:
            if parent.defined:
                parent._value[key] = v
                break

            parent._value = v = {key: v}
            key = parent._name
            parent = getattr(parent, 'parent', None)

    def _invalidate(self):
        self.parent = None
        self._model = None

    @property
    def value(self):
        """current value of this subfield"""
        if self.parent is None:
            raise InvalidatedSubfieldError('Subfield {0!r} was invalidated by an update to it\'s '
                                           'parent Field.'.format(self._name))

        return super(Subfield, self).value

    def _reload(self, *arg, **kw):
        if self.parent is None:
            raise InvalidatedSubfieldError('Subfield {0!r} was invalidated by an update to it\'s '
                                           'parent Field.'.format(self._name))

        return super(Subfield, self)._reload(*arg, **kw)
