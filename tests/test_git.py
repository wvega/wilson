# coding: utf-8

import os
import shutil

import fabric

from skeleton.git import git

from tests import SkeletonTestCase


class GitSkeletonTestCase(SkeletonTestCase):

    def test_git(self):
        dirname = '/tmp/skeleton-git-test'
        os.mkdir(dirname)

        with fabric.api.lcd(dirname):
            git(True)

            self.assertTrue(os.path.exists(os.path.join(dirname, '.git')))

        if os.path.exists(dirname):
            shutil.rmtree(dirname)
