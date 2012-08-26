# coding: utf-8

from fabric.contrib.project import rsync_project as rsync
from fabric.utils import puts


def sync(path, exclude=[], key=None):
    exclude = ['.git/*', 'build/*', '*.pyc']

    # extras = '-L -e "ssh -i %s"' % key
    extras = ''
    result = rsync(path, delete=True, exclude=exclude, extra_opts=extras)

    puts(result) if result else None
