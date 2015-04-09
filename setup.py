# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


setup(name='dibble',
      version='0.0.4',
      description='Mongodb Object Mapper',
      url='https://github.com/voxelbrain/dibble',
      packages=find_packages(exclude=['tests']),
      install_requires=['pymongo>=2.4'],
      tests_require=['nose'],
      setup_requires=['setuptools-git'],
      test_suite='nose.collector')
