# coding: utf-8

from fabric.api import local
from fabric.contrib.console import confirm
from fabric.utils import puts

from skeleton import Skeleton


def git(force=False):
    """Creates a new git repo for this project"""

    m = 'This will remove the current .git directory, do you want to continue?'
    if force or confirm(m, default=False):
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
        puts('Ok. Nothing was touched!')
