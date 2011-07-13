# coding: utf-8

import getpass
import os
import re

from fabric.api import local, abort
from fabric.contrib.console import confirm

from options import options


def setup():
    """Setup a new WordPress project"""

    if options['name'] == 'example.com':
        abort('Please update your options.py first!')

    wordpress()
    git(force=True)

    print("\nThat's all. Have fun!")


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


def git(force=False):
    """Creates a new git repo for this project"""

    if force or confirm('This will remove the current .git directory, do you want to continue?', default=False):
        # remove wordpress-skeleton.git metadata
        local('rm .git -rf')

        # setup a new repository
        local('git init')
        local('mv gitignore.sample .gitignore')
        local('git add .')
        local('git commit -m "Initial commit."')
        
        if os.path.exists('/files/Git/projects/'):
            repo = '/files/Git/projects/%s.git' % options['name']
            local('git clone --bare . %s' % repo)
            local('git remote add origin %s' % repo )
            local('git config branch.master.remote origin')
            local('git config branch.master.merge refs/heads/master')
        else:
            print("\nCan't create origin. Skipping")
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
                options['local.%s' % key] = result.group(1)


def replace(pattern, replacement):
    """Replace strings in database records"""

    prepare()

    host = options['local.host']
    username = options['local.user']
    password = options['local.password']
    db = options['local.db']

    args = (pattern, replacement, host, username, password, db)
    local('php searchandreplace.php %s %s %s %s %s %s true' % args)


def backup():
    """Creates database backups using different website URLs for testing, production and local environment"""

    prepare()

    host = options['local.host']
    username = options['local.user']
    password = options['local.password']
    db = options['local.db']

    # find an unique name for the backup file
    import datetime
    now = datetime.datetime.now()
    basename = 'sql/%s-%d-%.2d-%.2d.sql' % (options['name'], now.year, now.month, now.day)
    filename = basename.replace('.sql', '-1.sql')
    i = 2

    while os.path.exists(filename):
        filename = basename.replace('.sql', '-%d.sql' % i)
        i = i + 1

    # create db backups for testing and development environments
    last = 'local.url'
    for e in ['production', 'testing']:
        if options['%s.url' % e] is None:
            continue
        replace(options[last], options['%s.url' % e])
        local('mysqldump -uroot -ppassword %s > %s' % (db, filename.replace('.sql', '-%s.sql' % e)))
        last = '%s.url' % e

    # create a local db backup
    replace(options[last], options['local.url'])
    local('mysqldump -uroot -ppassword %s > %s' % (db, filename))


def config(target='local', create=None):
    """Swtich between different wp-config.php files"""

    target = getpass.getuser() if target == 'local' else target

    if target in ['p', 'production'] and os.path.exists('wp-config.production.php'):
        local('cp wp-config.production.php wp-config.php')
    elif target in ['t', 'testing'] and os.path.exists('wp-config.testing.php'):
        local('cp wp-config.testing.php wp-config.php')
    elif not os.path.exists('wp-config.%s.php' % target):
        if create or confirm('Do you want to create the config file wp-config.%s.php' % target):
            local('cp wp-config.php wp-config.%s.php' % target)
    else:        
        local('cp wp-config.%s.php wp-config.php' % target)


