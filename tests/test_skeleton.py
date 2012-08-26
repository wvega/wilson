# coding: utf-8

import os

import fabric

import skeleton

from tests import SkeletonTestCase


class BaseSkeletonTestCase(SkeletonTestCase):

    def setUp(self):
        self.running = fabric.state.output.running
        self.warnings = fabric.state.output.warnings
        fabric.state.output.running = False
        fabric.state.output.warnings = False

    def tearUp(self):
        fabric.state.output.running = self.running
        fabric.state.output.warnings = self.warnings

    def test_init(self):
        path = os.path.join(os.getcwd(), '.skeleton.json')

        self.assertFalse(os.path.exists(path))

        skeleton.init()

        self.assertTrue(os.path.exists(path))

        os.unlink(path)

    def test_options(self):
        _options = skeleton.Skeleton.options()
        self.assertIsInstance(_options, dict)

        self.assertEqual(skeleton.options, _options)

    def test_asset(self):
        path = skeleton.Skeleton.asset('skeleton.global.json')
        self.assertTrue(os.path.exists(path))

        path = skeleton.Skeleton.asset('missing.file')
        self.assertFalse(os.path.exists(path))
