# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(name='dibble',
      version='0.0.2',
      description='Mongodb Object Mapper',
      url='https://github.com/voxelbrain/dibble',
      packages=find_packages(exclude=['tests']),
      install_requires=['pymongo'],
      tests_require=['nose'],
      setup_requires=['setuptools-git'],
      test_suite='nose.collector')
