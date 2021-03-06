# coding: utf-8

import os

from setuptools import setup


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name='Wordpress Skeleton',
    version='0.0.3',
    author='Willington Vega',
    author_email='wvega@wvega.com',
    description=('Fabric recipes to work with WordPress projects'),
    long_description=read('README.md'),
    license='GPL',
    keywords='fabric wordpress',
    url='http://packages.python.org/wilson',
    packages=['skeleton'],
    package_data={'skeleton': ['assets/*']},
    install_requires=['Fabric'],
    classifiers=["Development Status :: 3 - Alpha"],
    test_suite='tests.suite'
)
