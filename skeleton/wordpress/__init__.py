# coding: utf-8

import datetime
import getpass
import os
import re

from fabric.api import local, abort
from fabric.contrib.console import confirm

from skeleton import Skeleton, options


SKELETON = os.path.join(os.getcwd(), '.skeleton.json')


def httpdconf(domain=None, directory=None, *args, **kw):
    domain = 'local.%s' % options['project.name'] if domain is None else domain
    directory = os.getcwd() if directory is None else directory
    directory = os.path.realpath(directory)

    conf = os.path.expanduser(options['global.httpd.conf'])
    root = os.path.expanduser(os.path.join(options['global.httpd.htdocs'], domain))

    if not os.path.exists(conf):
        abort('Configuration directory doesn\'t exists: %s\n' % conf)

    try:
        conf = open(os.path.join(conf, '%s.conf' % domain), 'w+')

        conf.write('<VirtualHost *:80>\n')
        conf.write('\tServerName %s\n' % domain)
        conf.write('\tDocumentRoot %s\n' % root)
        conf.write('\n')
        conf.write('\t<Directory %s>\n' % root)
        conf.write('\t\tOptions FollowSymLinks\n')
        conf.write('\t\tAllowOverride All\n')
        conf.write('\t</Directory>\n')
        conf.write('</VirtualHost>\n')
        conf.close()
    except OSError:
        abort('Couldn\'t write the configuration file.')

    try:
        if os.path.exists(root):
            print root, os.path.realpath(root), directory
            os.unlink(root)
        os.symlink(directory, root)
    except OSError:
            message = "Warning: couldn't create symbolic link %s to %s. Try:" % (directory, root)
            message = '%s\nln -s %s %s\n' % (message, directory, root)
            abort(message)

    print('A VirtualHost has been created:')
    print('\n\t%s => %s.\n' % (domain, directory))
    print('Add the following to your /etc/hosts and restart Apache:')
    print('\n\t127.0.0.1\t\t%s\n' % domain)


def git(force=False):
    """Creates a new git repo for this project"""

    if force or confirm('This will remove the current .git directory, do you want to continue?', default=False):
        # remove wordpress-skeleton.git metadata
        local('rm -rf .git')

        # setup a new repository
        local('git init')
        local('cp -f %s .gitignore' % Skeleton.asset('gitignore.sample'))
        local('git add .')
        local('git commit -m "Initial commit."')

        # TODO: create origin? this is probably not needed
        # if os.path.exists('/files/Git/projects/'):
        #     repo = '/files/Git/projects/%s.git' % options['name']
        #     if not os.path.exists(repo):
        #         local('git clone --bare . %s' % repo)
        #     local('git remote add origin %s' % repo)
        #     local('git config branch.master.remote origin')
        #     local('git config branch.master.merge refs/heads/master')
        # else:
        #     print("\nCan't create origin. Skipping")
    else:
        print('Ok. Nothing was touched!')


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


def init():
    """Creates a sample skeleton.json file"""

    message = 'A skeleton.json file already exists. Do you want to overwrite it?'
    if os.path.exists(SKELETON) and not confirm(message):
        print('Ok. Nothing was touched.')
        return

    local('cp -f %s .skeleton.json' % Skeleton.asset('skeleton.project.json'))


def setup(version='latest'):
    """Setup a new WordPress project"""

    if options.get('project.name', 'example.com') == 'example.com':
        if not os.path.exists(SKELETON):
            abort('Please create your skeleton.json file.')
        else:
            abort('Please update your skeleton.json file.')

    wordpress(version)
    git(force=True)

    httpdconf(options['project.name'], os.getcwd())

    print("\nThat's all. Have fun!")


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


def replace(pattern, replacement):
    """Replace strings in database records"""

    prepare()

    host = options['project.mysql.host']
    db = options['project.mysql.db']
    username = options['project.mysql.user']
    password = options['project.mysql.password']

    args = (Skeleton.asset('searchandreplace.php'), pattern, replacement, host, username, password, db)
    local('php %s %s %s %s %s %s %s true' % args)


def backup(databases=False):
    """Creates database backups using different website URLs for testing, production and local environment"""

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
    sqlfile = filename.replace('.sql', '-local.sql')

    i = 2
    while os.path.exists(sqlfile):
        filename = basename.replace('.sql', '-%d.sql' % i)
        sqlfile = filename.replace('.sql', '-local.sql')
        i = i + 1

    command = 'mysqldump --add-drop-table --add-drop-database -h%s -u%s -p%s'
    command = '%s --databases' % command if databases else command
    command = command + ' %s > %s'

    # create db backups for testing and development environments
    last = 'project.url.local'
    for e in ['production', 'testing', 'local']:
        if options['project.url.%s' % e] is None:
            continue

        sqlfile = filename.replace('.sql', '-%s.sql' % e)

        replace(options[last], options['project.url.%s' % e])

        local(command % (host, username, password, db, sqlfile))
        local('cp %s sql/%s-%s-latest.sql' % (sqlfile, options['project.name'], e))

        last = 'project.url.%s' % e


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
