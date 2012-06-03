# coding: utf-8

import os
import json

from fabric.api import warn, abort


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
        except ValueError:
            abort('One of your skeleton.json files contains an error.')

        return dict(system.items() + project.items())

    @classmethod
    def asset(cls, filename):
        return os.path.join(os.path.dirname(__file__), filename)


options = Skeleton.options()
