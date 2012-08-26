# coding: utf-8

import unittest

import fabric


class SkeletonTestCase(unittest.TestCase):

    def setUp(self):
        self.running = fabric.state.output.running
        self.warnings = fabric.state.output.warnings
        self.stdout = fabric.state.output.stdout
        self.stderr = fabric.state.output.stderr

        fabric.state.output.running = False
        fabric.state.output.warnings = False
        fabric.state.output.stdout = False
        fabric.state.output.stderr = False

    def tearUp(self):
        fabric.state.output.running = self.running
        fabric.state.output.warnings = self.warnings
        fabric.state.output.stdout = self.stdout
        fabric.state.output.stderr = self.stderr


def suite():
    suite = unittest.TestSuite()

    from tests.test_skeleton import BaseSkeletonTestCase
    suite.addTest(BaseSkeletonTestCase('test_init'))
    suite.addTest(BaseSkeletonTestCase('test_options'))
    suite.addTest(BaseSkeletonTestCase('test_asset'))

    from tests.test_git import GitSkeletonTestCase
    suite.addTest(GitSkeletonTestCase('test_git'))

    from tests.test_wordpress import WordPressSkeletonTestCase
    suite.addTest(WordPressSkeletonTestCase('test_wordpress'))

    return suite
