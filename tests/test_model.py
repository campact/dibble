# -*- coding: utf-8 -*-
import dibble.fields
import dibble.model
from nose.tools import raises, eq_, assert_false, assert_true


class SimpleModel(dibble.model.Model):
    xbool = dibble.fields.Field()
    xint = dibble.fields.Field()
    xfloat = dibble.fields.Field()
    xbytes = dibble.fields.Field()
    xunicode = dibble.fields.Field()
    xlist = dibble.fields.Field()
    xdict = dibble.fields.Field()


class PropertyModel(dibble.model.Model):
    @property
    def prop(self):
        return self.zfield['subfield'].value

    zfield = dibble.fields.Field()


def test_initialization():
    cls = SimpleModel
    m = SimpleModel()

    assert isinstance(cls.xbool, dibble.fields.UnboundField)
    assert isinstance(cls.xint, dibble.fields.UnboundField)
    assert isinstance(cls.xfloat, dibble.fields.UnboundField)
    assert isinstance(cls.xbytes, dibble.fields.UnboundField)
    assert isinstance(cls.xunicode, dibble.fields.UnboundField)
    assert isinstance(cls.xlist, dibble.fields.UnboundField)
    assert isinstance(cls.xdict, dibble.fields.UnboundField)

    assert isinstance(m.xbool, dibble.fields.Field)
    assert isinstance(m.xint, dibble.fields.Field)
    assert isinstance(m.xfloat, dibble.fields.Field)
    assert isinstance(m.xbytes, dibble.fields.Field)
    assert isinstance(m.xunicode, dibble.fields.Field)
    assert isinstance(m.xlist, dibble.fields.Field)
    assert isinstance(m.xdict, dibble.fields.Field)


def test_inheritance():
    class InheritedModel(SimpleModel):
        ybool = dibble.fields.Field()
        yint = dibble.fields.Field()
        yfloat = dibble.fields.Field()
        ybytes = dibble.fields.Field()
        yunicode = dibble.fields.Field()
        ylist = dibble.fields.Field()
        ydict = dibble.fields.Field()

    m = InheritedModel()

    assert isinstance(m.xbool, dibble.fields.Field)
    assert isinstance(m.xint, dibble.fields.Field)
    assert isinstance(m.xfloat, dibble.fields.Field)
    assert isinstance(m.xbytes, dibble.fields.Field)
    assert isinstance(m.xunicode, dibble.fields.Field)
    assert isinstance(m.xlist, dibble.fields.Field)
    assert isinstance(m.xdict, dibble.fields.Field)

    assert isinstance(m.ybool, dibble.fields.Field)
    assert isinstance(m.yint, dibble.fields.Field)
    assert isinstance(m.yfloat, dibble.fields.Field)
    assert isinstance(m.ybytes, dibble.fields.Field)
    assert isinstance(m.yunicode, dibble.fields.Field)
    assert isinstance(m.ylist, dibble.fields.Field)
    assert isinstance(m.ydict, dibble.fields.Field)


def test_update():
    class TestModel(dibble.model.Model):
        counter = dibble.fields.Field()

    m = TestModel()
    m.counter.set(1)

    eq_(dict(m._update), {'$set': {'counter': 1}})

    m.counter.inc(1)

    eq_(dict(m._update), {'$set': {'counter': 1}, '$inc': {'counter': 1}})


def test_defined():
    class TestModel(dibble.model.Model):
        counter = dibble.fields.Field()

    m = TestModel()
    assert_false(m.counter.defined)


def test_initial():
    class TestModel(dibble.model.Model):
        counter = dibble.fields.Field()

    m = TestModel(counter=5)
    eq_(m.counter.value, 5)

    m = TestModel({'counter': 10})
    eq_(m.counter.value, 10)


def test_default():
    class TestModel(dibble.model.Model):
        counter = dibble.fields.Field(default=100)

    m = TestModel()
    eq_(m.counter.value, 100)


def test_default_callable():
    class TestModel(dibble.model.Model):
        counter = dibble.fields.Field(default=lambda: 42)

    m = TestModel()
    eq_(m.counter.value, 42)

    m.counter.inc(8)
    eq_(m.counter.value, 50)


def test_default_initial():
    class TestModel(dibble.model.Model):
        counter = dibble.fields.Field(default=100)

    m = TestModel({'counter': 5})
    eq_(m.counter.value, 5)


def test_iter():
    class TestModel(dibble.model.Model):
        a = dibble.fields.Field()
        b = dibble.fields.Field()
        c = dibble.fields.Field()

    m = TestModel(a=1, b=2)
    values = dict(m)

    eq_(sorted(values.keys()), ['a', 'b'])
    eq_(values, {'a': 1, 'b': 2})

    m.c.set(3)
    values = dict(m)

    eq_(values, {'a': 1, 'b': 2, 'c': 3})


def test_getitem():
    m = SimpleModel(xint=1)

    eq_(m['xint'], 1)


@raises(KeyError)
def test_getitem_keyerror():
    m = SimpleModel()
    m['not_existing_key']


@raises(dibble.model.UndefinedFieldError)
def test_getitem_undefined_field():
    m = SimpleModel()
    m['xint']


@raises(AttributeError)
def test_getattr_undefined():
    m = SimpleModel()
    m.foobarbaz


def test_getattr_defined():
    m = SimpleModel()
    assert_true(m.xint, dibble.fields.Field)


@raises(AttributeError)
def test_delattr_undefined():
    m = SimpleModel()
    del m.foobarbaz


def test_delattr_defined_field():
    m = SimpleModel()
    del m.xint
    assert_false(hasattr(m, 'xint'))


def test_delattr_defined():
    m = SimpleModel()
    del m._mapper
    assert_false(hasattr(m, '_mapper'))


def test_field_add():
    m = SimpleModel()
    f = dibble.fields.Field()
    m.newfield = f

    assert_true(hasattr(m, 'newfield'))
    print m.newfield
    assert_true(isinstance(m.newfield, dibble.fields.Field))


@raises(dibble.model.UnboundModelError)
def test_unbound_model():
    m = SimpleModel()
    m.save()


def test_model_with_properties():
    m = PropertyModel()

    # should not trigger errors
    eq_(m.prop, None)


def test_model_repr():
    m = SimpleModel({'xbool': True, 'xfloat': 0.1})
    r = repr(m)

    assert_true(r.startswith('<SimpleModel({'))
    assert_true(r.endswith('})>'))
    eq_(r[13:-2], repr(dict(m)))
