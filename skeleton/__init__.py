# coding: utf-8

import os
import json

from fabric.api import abort, local, warn
from fabric.contrib.console import confirm
from fabric.utils import puts


SKELETON = os.path.join(os.getcwd(), '.skeleton.json')


def init():
    """Creates a sample skeleton.json file"""

    message = 'A skeleton.json file already exists. Do you want to overwrite it?'
    if os.path.exists(SKELETON) and not confirm(message):
        puts('Ok. Nothing was touched.')
        return

    local('cp -f %s .skeleton.json' % Skeleton.asset('skeleton.project.json'))


class Skeleton(object):

    @classmethod
    def options(cls):
        # global options
        try:
            filename = os.path.expanduser(os.path.join('~', '.skeleton.json'))
            try:
                system = json.loads(open(filename).read())
            except IOError:
                warn('No global skeleton.json file was found.')
                system = {}

            # project options
            filename = os.path.join(os.getcwd(), '.skeleton.json')
            try:
                project = json.loads(open(filename).read())
            except IOError:
                warn('No skeleton.json was found for this project.')
                project = {}
        except ValueError, e:
            abort('One of your skeleton.json files contains an error:\n\n%s' % e)

        return dict(system.items() + project.items())

    @classmethod
    def asset(cls, filename):
        return os.path.join(os.path.dirname(__file__), 'assets', filename)


options = Skeleton.options()
