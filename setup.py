# coding: utf-8

import os

from setuptools import setup


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


setup(
    name='Wordpress Skeleton',
    version='0.0.1',
    author='Willington Vega',
    author_email='wvega@wvega.com',
    description=('Fabric recipes to work with WordPress projects'),
    long_description=read('README.md'),
    license='GPL',
    keywords='fabric wordpress',
    url='http://packages.python.org/wilson',
    packages=['skeleton', 'skeleton.wordpress'],
    package_data={'skeleton': ['*.json', '*.php', '*.sample']},
    classifiers=["Development Status :: 3 - Alpha"]
)
