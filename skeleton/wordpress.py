# coding: utf-8

import datetime
import getpass
import os
import re

from fabric.api import local, abort
from fabric.contrib.console import confirm
from fabric.utils import puts

from skeleton import Skeleton, options
from skeleton.git import git
from skeleton.httpd import vhost
from skeleton.mysql import replace


def wordpress(version=None):
    """Download latest stable version of WordPress"""

    if version is None:
        basename = 'latest.tar.gz'
    else:
        basename = 'wordpress-%s.tar.gz' % version

    if os.path.exists(os.path.join(os.getcwd(), basename)):
        os.unlink(os.path.join(os.getcwd(), basename))

    local('wget http://wordpress.org/%s' % basename)
    local('tar -xf %s' % basename)
    local('cp -fR wordpress/* .')
    local('rm -rf wordpress')

    local('mkdir -pm 0777 wp-content/uploads')
    local('cp -f %s .htaccess' % Skeleton.asset('htaccess.sample'))

    local('rm %s' % basename)


def setup(version='latest'):
    """Setup a new WordPress project"""

    if options.get('project.name', 'example.com') == 'example.com':
        abort('Please create or update your skeleton.json file.')

    wordpress(version)
    git(force=True)

    vhost(options['project.name'], os.getcwd())

    puts("\nThat's all. Have fun!")


def prepare():
    """Load DB configuration from wp-config.php file"""

    if os.path.exists('wp-config.php'):
        patterns = {
            'host': re.compile(r"define[( ]*'DB_HOST'[ ,]*'([^']+)'[ );]*"),
            'db': re.compile(r"define[( ]*'DB_NAME'[ ,]*'([^']+)'[ );]*"),
            'user': re.compile(r"define[( ]*'DB_USER'[ ,]*'([^']+)'[ );]*"),
            'password': re.compile(r"define[( ]*'DB_PASSWORD'[ ,]*'([^']+)'[ );]*")
        }

    for line in open('wp-config.php'):
        for key in patterns:
            result = patterns[key].search(line)
            if result is not None:
                options['project.mysql.%s' % key] = result.group(1)


def config(target='local', create=None):
    """Swtich between different wp-config.php files"""

    target = getpass.getuser() if target == 'local' else target

    if target in ['p', 'production'] and os.path.exists('wp-config.production.php'):
        local('cp wp-config.production.php wp-config.php')
    elif target in ['t', 'testing'] and os.path.exists('wp-config.testing.php'):
        local('cp wp-config.testing.php wp-config.php')
    elif os.path.exists('wp-config.%s.php' % target):
        local('cp wp-config.%s.php wp-config.php' % target)
    elif create or confirm('Do you want to create the config file wp-config.%s.php' % target):
            local('cp wp-config.php wp-config.%s.php' % target)


def backup(databases=False):
    """
    Creates database backups using different website URLs for testing,
    production and local environment.
    """

    prepare()

    host = options['project.mysql.host']
    username = options['project.mysql.user']
    password = options['project.mysql.password']
    db = options['project.mysql.db']

    if not os.path.exists('sql'):
        local('mkdir -p sql')

    # find an unique name for the backup file
    now = datetime.datetime.now()
    basename = 'sql/%s-%d-%.2d-%.2d.sql' % (options['project.name'], now.year, now.month, now.day)
    filename = basename.replace('.sql', '-1.sql')
    sql = filename.replace('.sql', '-local.sql')

    i = 2
    while os.path.exists(sql):
        filename = basename.replace('.sql', '-%d.sql' % i)
        sql = filename.replace('.sql', '-local.sql')
        i = i + 1

    command = 'mysqldump --add-drop-table --add-drop-database -h%s -u%s -p%s'
    command = '%s --databases' % command if databases else command
    command = command + ' %s > %s'

    # create db backups for testing and development environments
    last = 'project.url.local'
    for e in ['production', 'testing', 'local']:
        if options['project.url.%s' % e] is None:
            continue

        sql = filename.replace('.sql', '-%s.sql' % e)

        replace(options[last], options['project.url.%s' % e])

        local(command % (host, username, password, db, sql))
        local('cp %s sql/%s-%s-latest.sql' % (sql, options['project.name'], e))

        last = 'project.url.%s' % e
