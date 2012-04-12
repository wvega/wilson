# coding: utf-8

import datetime
import getpass
import os
import re

from fabric.api import local, abort
from fabric.contrib.console import confirm

from options import options


def setup(version='3.1.3'):
    """Setup a new WordPress project"""

    if options['name'] == 'example.com':
        abort('Please update your options.py first!')

    wordpress(version)
    git(force=True)

    import urlparse
    host = urlparse.urlparse(options['local.url']).netloc
    httpdconf(host, os.getcwd())

    print("\nThat's all. Have fun!")


def wordpress(version):
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
            if not os.path.exists(repo):
                local('git clone --bare . %s' % repo)
            local('git remote add origin %s' % repo)
            local('git config branch.master.remote origin')
            local('git config branch.master.merge refs/heads/master')
        else:
            print("\nCan't create origin. Skipping")
    else:
        print('Ok. Nothing was touched!')


def httpdconf(domain, src, *args, **kw):
    conf = options['httpd.conf.dir']
    root = os.path.join(options['httpd.document.root'], domain)
    src = os.path.realpath(src)

    if not os.path.exists(conf):
        print '\nERROR: Configuration directory doesn\'t exists: %s\n' % conf
        return

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

    try:
        os.symlink(src, root)
    except OSError:
        if os.path.exists(root):
            os.unlink(root)
            os.symlink(src, root)
        else:
            print("Warning: couldn't create symbolic link (%s) to %s. Try:" % (src, root))
            print('ln -s %s %s\n' % (src, root))

    print('A VirtualHost has been created:')
    print('\n%s => %s.\n' % (domain, src))
    print('Add the following to your /etc/hosts and restart Apache:')
    print('\n::1             %s\n' % domain)


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

    if not os.path.exists('sql'):
        local('mkdir -p sql')

    # find an unique name for the backup file
    now = datetime.datetime.now()
    basename = 'sql/%s-%d-%.2d-%.2d.sql' % (options['name'], now.year, now.month, now.day)
    filename = basename.replace('.sql', '-1.sql')
    sqlfile = filename.replace('.sql', '-local.sql')

    i = 2
    while os.path.exists(sqlfile):
        filename = basename.replace('.sql', '-%d.sql' % i)
        sqlfile = filename.replace('.sql', '-local.sql')
        i = i + 1

    command = 'mysqldump --add-drop-table --add-drop-database -h%s -u%s -p%s --databases %s > %s'

    # create db backups for testing and development environments
    last = 'local.url'
    for e in ['production', 'testing', 'local']:
        if options['%s.url' % e] is None:
            continue

        sqlfile = filename.replace('.sql', '-%s.sql' % e)

        replace(options[last], options['%s.url' % e])

        local(command % (host, username, password, db, sqlfile))
        local('cp %s sql/%s-%s-latest.sql' % (sqlfile, options['name'], e))

        last = '%s.url' % e


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
