# coding: utf-8

import getpass
import os
import re

from fabric.api import local
from fabric.contrib.console import confirm

from options import options


def setup():
    """Setup a new WordPress project"""

    wordpress()
    git(force=True)

    print("\nThat's all. Don't forget to update your options.py!")


def wordpress(version='3.1.3'):
    """Download latest stable version of WordPress"""

    if version is None:
        basename = 'latest.tar.gz'
    else:
        basename = 'wordpress-%s.tar.gz' % version

    local('wget http://wordpress.org/%s' % basename)
    local('tar -xzf %s' % basename)
    local('mv wordpress/* .')
    local('rm wordpress -rf')
    local('rm %s' % basename)

    local('mkdir -m 0777 wp-content/uploads')
    local('mv htaccess.sample .htaccess')

    local('rm wp-config-sample.php')


def git(force=False):
    """Creates a new git repo for this project"""

    if force or confirm('This will removesad the current .git directory, do you want to continue?', default=False):
        # remove wordpress-skeleton.git metadata
        local('rm .git -rf')

        # setup a new repository
        local('git init')
        local('mv gitignore.sample .gitignore')
    else:
        print('Ok. Nothing was touched!');


def prepare():
    """Load DB configuration from wp-config.php file"""

    if os.path.exists('wp-config.php'):
        patterns = {
            'db': re.compile(r"define[( ]*'DB_NAME'[ ,]*'([^']+)'[ );]*"),
            'password': re.compile(r"define[( ]*'DB_PASSWORD'[ ,]*'([^']+)'[ );]*"),
            'user': re.compile(r"define[( ]*'DB_USER'[ ,]*'([^']+)'[ );]*"),
            'host': re.compile(r"define[( ]*'DB_HOST'[ ,]*'([^']+)'[ );]*")
        }

    for line in open('wp-config.php'):
        for key in patterns:
            result = patterns[key].search(line)
            if result is not None:
                settings['local.%s' % key] = result.group(1)


def replace(pattern, replacement):
    """Replace strings in database records"""

    prepare()

    host = settings['local.host']
    username = settings['local.user']
    password = settings['local.password']
    db = settings['local.db']

    args = (pattern, replacement, host, username, password, db)
    local('php searchandreplace.php %s %s %s %s %s %s true' % args)


def backup():
    """Creates database backups using different website URLs for testing, production and local environment"""

    prepare()

    host = settings['local.host']
    username = settings['local.user']
    password = settings['local.password']
    db = settings['local.db']

    # find an unique name for the backup file
    import datetime
    now = datetime.datetime.now()
    basename = 'sql/%s-%d-%.2d-%.2d-1.sql' % (settings['name'], now.year, now.month, now.day)
    filename = basename
    i = 2

    while os.path.exists(filename):
        filename = basename.replace('.sql', '-%d.sql' % i)
        i = i + 1

    # create db backups for testing and development environments
    for e in ['production', 'testing']:
        if settings['%s.url' % e] is None:
            continue
        replace(settings['local.url'], settings['%s.url' % e])
        local('mysqldump -uroot -ppassword %s > %s' % (db, filename.replace('.sql', '-%s.sql' % e)))

    # create a local db backup
    replace(settings['testing.url'], settings['local.url'])
    local('mysqldump -uroot -ppassword %s > %s' % (db, filename))


def config(target='local', create=None):
    """Swtich between different wp-config.php files"""

    if target in ['p', 'production'] and os.path.exists('wp-config.production.php'):
        local('cp wp-config.production.php wp-config.php')
    elif target in ['t', 'testing'] and os.path.exists('wp-config.testing.php'):
        local('cp wp-config.testing.php wp-config.php')
    elif target == 'local':
        local('cp wp-config.%s.php wp-config.php' % getpass.getuser())
    elif not os.path.exists('wp-config.%s.php' % target):
        if create or confirm('Do you want to create the config file wp-config.%s.php' % target):
            local('cp wp-config.php wp-config.%s.php' % target)
    else:        
        local('cp wp-config.%s.php wp-config.php' % target)

