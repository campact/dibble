# -*- coding: utf-8 -*-
import pymongo
import dibble.fields
import dibble.model
import dibble.mapper
from nose import with_setup
from nose.tools import eq_, assert_dict_contains_subset, raises, assert_dict_equal


DBNAME = 'dibbletest'


class UserModel(dibble.model.Model):
    name = dibble.fields.Field()


class AdvancedUserModel(dibble.model.Model):
    logincount = dibble.fields.Field()
    username = dibble.fields.Field()
    usernames = dibble.fields.Field()


class ReloadTestModel(dibble.model.Model):
    counter = dibble.fields.Field()
    foo = dibble.fields.Field()
    bar = dibble.fields.Field()


def get_db():
    con = pymongo.Connection()

    return con[DBNAME]


def get_mapper():
    db = get_db()

    return dibble.mapper.ModelMapper(UserModel, db.user)


def setup_db():
    db = get_db()
    [db.drop_collection(x) for x in db.collection_names() if not x.startswith('system.')]
    db.connection.drop_database(DBNAME)


@with_setup(setup_db)
def test_modelmapper_new():
    users = get_mapper()

    username = 'testuser'
    user = users(name=username)

    eq_(user['name'], username)
    eq_(user.name.value, username)


@with_setup(setup_db)
def test_modelmapper_count():
    mapper = get_mapper()
    eq_(mapper.count(), 0)


@with_setup(setup_db)
def test_modelmapper_save_and_find_one():
    users = get_mapper()

    dummy_user = {'name': 'test'}
    users.save(dummy_user)

    eq_(users.count(), 1)


@with_setup(setup_db)
def test_find_generator():
    users = get_mapper()

    dummy_user = {'name': 'test'}
    uid = users.save(dummy_user, safe=True)

    for x in range(10):
        users.save({'name': 'test_' + str(x)})

    cursor = users.find({'name': dummy_user['name']})

    eq_(cursor.count(), 1)

    db_user = list(cursor)[0]

    eq_(db_user['_id'], uid)
    eq_(db_user.name.value, dummy_user['name'])
    eq_(db_user['name'], dummy_user['name'])


@with_setup(setup_db)
def test_find_getitem():
    users = get_mapper()

    dummy_user = {'name': 'test'}
    uid = users.save(dummy_user, safe=True)

    for x in range(10):
        users.save({'name': 'test_' + str(x)})

    cursor = users.find({'name': dummy_user['name']})

    eq_(cursor.count(), 1)

    db_user = cursor[0]

    eq_(db_user['_id'], uid)
    eq_(db_user.name.value, dummy_user['name'])
    eq_(db_user['name'], dummy_user['name'])


@with_setup(setup_db)
def test_modelmapper_model_save():
    db = get_db()
    users = dibble.mapper.ModelMapper(AdvancedUserModel, db.user)

    user = users()
    user.logincount.inc(1)
    user.username.set('Foo Bar')
    user.usernames.push('Foo Bar')
    user.save()

    u = dict(users.collection.find_one())
    expected = {'logincount': 1, 'username': 'Foo Bar', 'usernames': ['Foo Bar']}

    assert_dict_contains_subset(expected, u)

    users.collection.update({}, {'$set': {'username': 'Fumm Fumm'}})

    user.logincount.inc(41)
    user.save()

    u = dict(users.collection.find_one())
    expected = {'logincount': 42, 'username': 'Fumm Fumm', 'usernames': ['Foo Bar']}

    assert_dict_contains_subset(expected, u)


@with_setup(setup_db)
def test_modelmapper_model_reload():
    db = get_db()
    users = dibble.mapper.ModelMapper(AdvancedUserModel, db.user)

    user = users()
    user.username.set('Foo Bar')
    user.save()

    users.collection.update({}, {'$set': {'username': 'Fumm Fumm'}})

    user.reload()

    expected = {'username': 'Fumm Fumm'}

    assert_dict_contains_subset(expected, dict(user))


@with_setup(setup_db)
@raises(dibble.model.UnboundModelError)
def test_modelmapper_model_reload_unbound():
    user = AdvancedUserModel()
    user.reload()


@with_setup(setup_db)
@raises(dibble.model.UnsavedModelError)
def test_modelmapper_model_reload_unsaved():
    db = get_db()
    users = dibble.mapper.ModelMapper(AdvancedUserModel, db.user)
    user = users()
    user.reload()


@with_setup(setup_db)
def test_modelmapper_custom_id():
    db = get_db()
    users = dibble.mapper.ModelMapper(UserModel, db.user)
    user = users()
    user.name.set('Foo Bar')

    user.save(_id='foobar')

    res = users.collection.find_one()
    expected = {'_id': 'foobar', 'name': 'Foo Bar'}

    assert_dict_equal(res, expected)


@with_setup(setup_db)
def test_modelpapper_reload_inc():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.save()

    # this is intentional and triggers a model reload
    m.counter.value

    m.counter.inc(1)
    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_set():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.save()

    m.bar.set('foo')

    eq_(m.foo.value, 'bar')
    eq_(m.bar.value, 'foo')

    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_inc():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.save()

    m.counter.inc(1)

    eq_(m.foo.value, 'bar')
    eq_(m.counter.value, 1)

    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_unset():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.bar.set('foo')
    m.save()

    m.bar.unset()

    eq_(m.foo.value, 'bar')
    eq_(m.bar.defined, False)

    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_push():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.save()

    m.bar.push('foo')

    eq_(m.foo.value, 'bar')
    eq_(m.bar.value, ['foo'])

    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_push_all():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.save()

    m.bar.push_all(['foo', 'bar', 'baz'])

    eq_(m.foo.value, 'bar')
    eq_(m.bar.value, ['foo', 'bar', 'baz'])

    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_add_to_set():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.save()

    m.bar.add_to_set('foo')

    eq_(m.foo.value, 'bar')
    eq_(m.bar.value, ['foo'])

    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_pop():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.bar.set(['foo', 'bar', 'baz'])
    m.save()

    m.bar.pop()

    eq_(m.foo.value, 'bar')
    eq_(m.bar.value, ['foo', 'bar'])

    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_pull():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.bar.set(['foo', 'bar', 'baz'])
    m.save()

    m.bar.pull('bar')

    eq_(m.foo.value, 'bar')
    eq_(m.bar.value, ['foo', 'baz'])

    m.save()


@with_setup(setup_db)
def test_modelpapper_reload_multifield_pull_all():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.bar.set(['foo', 'bar', 'baz'])
    m.save()

    m.bar.pull_all(['bar', 'baz'])

    eq_(m.foo.value, 'bar')
    eq_(m.bar.value, ['foo'])

    m.save()


@with_setup(setup_db)
def test_modelmapper_unsafe_update():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(ReloadTestModel, db.reloadtest)

    m = mapper()
    m.foo.set('bar')
    m.counter.set(1)
    m.save()

    m._update.inc('counter', 41)
    m.save()

    expected = {'foo': 'bar', 'counter': 42}
    assert_dict_contains_subset(expected, dict(m))


@with_setup(setup_db)
def test_subfield_invalidate():
    db = get_db()
    mapper = dibble.mapper.ModelMapper(UserModel, db.subfieldtest)

    m = mapper({'bar': 'baz'})
    m.save()
    m.name.set({'firstname': 'foo'})
    sf = m.name['firstname']

    m.reload()
    m.name.set({'firstname': 'bar'})
    m.save()
