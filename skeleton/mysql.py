# coding: utf-8

from fabric.api import local

from skeleton import Skeleton, options
from skeleton.wordpress import prepare


def replace(pattern, replacement):
    """Replace strings in database records"""

    prepare()

    host = options['project.mysql.host']
    db = options['project.mysql.db']
    username = options['project.mysql.user']
    password = options['project.mysql.password']

    path = Skeleton.asset('searchandreplace.php')
    args = (path, pattern, replacement, host, username, password, db)
    local('php %s %s %s %s %s %s %s true' % args)
