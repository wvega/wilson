# coding: utf-8

import os

from fabric.api import abort
from fabric.utils import puts

from skeleton import options


def vhost(domain=None, directory=None, *args, **kw):
    """Creates a VirtualHost configuration file for Apache"""
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
            os.unlink(root)
        os.symlink(directory, root)
    except OSError:
            message = "Warning: couldn't create symbolic link %s to %s. Try:" % (directory, root)
            message = '%s\nln -s %s %s\n' % (message, directory, root)
            abort(message)

    puts('A VirtualHost has been created:')
    puts('\n\t%s => %s.\n' % (domain, directory))
    puts('Add the following to your /etc/hosts and restart Apache:')
    puts('\n\t127.0.0.1\t\t%s\n' % domain)
