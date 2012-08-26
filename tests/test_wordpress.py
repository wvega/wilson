# coding: utf-8

import os
import shutil

import fabric

from skeleton.wordpress import wordpress

from tests import SkeletonTestCase


class WordPressSkeletonTestCase(SkeletonTestCase):

    def test_wordpress(self):
        dirname = '/tmp/skeleton-wordpress-test'
        os.mkdir(dirname)

        with fabric.api.lcd(dirname):
            wordpress()

            self.assertTrue(os.path.exists(os.path.join(dirname, 'wp-settings.php')))

        if os.path.exists(dirname):
            shutil.rmtree(dirname)
