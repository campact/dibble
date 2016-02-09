# -*- coding: utf-8 -*-
from nose import with_setup
from nose.tools import eq_, assert_not_equal, assert_dict_equal, assert_dict_contains_subset, raises, assert_false
import dibble.model
import dibble.fields
import pymongo


DBNAME = 'dibbletest'


class TestModel(dibble.model.Model):
    foo = dibble.fields.Field()


def get_db():
    client = pymongo.MongoClient()

    return client[DBNAME]


def get_mapper():
    db = get_db()

    return dibble.mapper.ModelMapper(TestModel, db.test)


def setup_db():
    db = get_db()
    [db.drop_collection(x) for x in db.collection_names() if not x.startswith('system.')]
    db.client.drop_database(DBNAME)


def test_subfield_access():
    tm = TestModel()
    sf = tm.foo['bar']

    eq_(sf.name, 'foo.bar')


def test_subfield_operation():
    tm = TestModel()
    sf = tm.foo['bar']

    sf.set('fumm')

    assert_dict_equal(dict(tm._update), {'$set': {'foo.bar': 'fumm'}})


def test_subfield_initialize():
    tm = TestModel({'foo': {'bar': 'baz'}})
    sf = tm.foo['bar']

    eq_(sf.value, 'baz')
    assert_false(tm.foo['baz'].defined)


def test_subfield_update():
    tm = TestModel({'foo': {'bar': 'baz'}})
    sf = tm.foo['bar']

    tm.foo.set({'bar': 'fumm'})
    eq_(sf.value, 'fumm')

    tm.foo['bar'].set('fnorb')
    eq_(sf.value, 'fnorb')
    assert_dict_equal(tm.foo.value, {'bar': 'fnorb'})


def test_nested_subfield_access():
    tm = TestModel()
    nsf = tm.foo['bar']['baz']

    eq_(nsf.name, 'foo.bar.baz')


def test_nested_subfield_operation():
    tm = TestModel()
    nsf = tm.foo['bar']['baz']

    nsf.set('fumm')

    assert_dict_equal(dict(tm._update), {'$set': {'foo.bar.baz': 'fumm'}})


def test_nested_subfield_initialize():
    tm = TestModel({'foo': {'bar': {'baz': 'fumm'}}})
    nsf = tm.foo['bar']['baz']

    eq_(nsf.value, 'fumm')


def test_nested_subfield_update():
    tm = TestModel({'foo': {'bar': {'baz': 'fumm'}}})
    nsf = tm.foo['bar']['baz']

    tm.foo.set({'bar': {'baz': 'fnorb'}})
    eq_(nsf.value, 'fnorb')

    tm.foo['bar'].set({'baz': 'doh!'})
    eq_(nsf.value, 'doh!')

    tm.foo['bar']['baz'].set('ding')
    eq_(nsf.value, 'ding')
    assert_dict_equal(tm.foo['bar'].value, {'baz': 'ding'})
    assert_dict_equal(tm.foo.value, {'bar': {'baz': 'ding'}})


@with_setup(setup_db)
def test_subfield_mapper():
    mapper = get_mapper()
    tm = mapper()

    tm.foo['bar']['baz'].set('fumm')
    tm.save()

    res = mapper.collection.find_one()
    expected = {'foo': {'bar': {'baz': 'fumm'}}}
    assert_dict_contains_subset(expected, res)

    tm.foo['bar']['baz'].set('fnorb')
    tm.save()

    res = mapper.collection.find_one()
    expected = {'foo': {'bar': {'baz': 'fnorb'}}}
    assert_dict_contains_subset(expected, res)

    tm.foo['bar'].set({'baz': 'ding'})
    tm.save()

    res = mapper.collection.find_one()
    expected = {'foo': {'bar': {'baz': 'ding'}}}
    assert_dict_contains_subset(expected, res)

    tm.foo.set({'bar': {'baz': 'yadda'}})
    tm.save()

    res = mapper.collection.find_one()
    expected = {'foo': {'bar': {'baz': 'yadda'}}}
    assert_dict_contains_subset(expected, res)


@raises(dibble.fields.InvalidatedSubfieldError)
def test_subfield_invalidated_value():
    tm = TestModel()
    sf = tm.foo['bar']

    tm.foo.set('bar')
    sf.value


@raises(dibble.fields.InvalidatedSubfieldError)
def test_subfield_invalidated_reloading():
    tm = TestModel()
    sf = tm.foo['bar']

    tm.foo.set('bar')
    sf.set('fnorb')


@raises(dibble.fields.InvalidatedSubfieldError)
def test_subfield_invalidation_dict():
    tm = TestModel({'foo': {'bar': 'baz'}})
    sf = tm.foo['bar']

    sf.set('fumm')
    eq_(sf.value, 'fumm')
    eq_(tm.foo.value, {'bar': 'fumm'})

    tm.foo.set({'fnorb': None})
    sf.set('baz')


@raises(dibble.fields.InvalidatedSubfieldError)
def test_subfield_reset_invalidate():
    tm = TestModel({'foo': {'bar': 'baz'}})
    sf = tm.foo['bar']

    sf.set('fnorb')
    tm.foo.reset(dibble.fields.undefined)

    sf.value


@raises(ValueError)
def test_subfield_of_simple_value():
    tm = TestModel({'foo': 'bar'})
    sf = tm.foo['baz']
