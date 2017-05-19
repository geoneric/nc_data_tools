import unittest
import numpy


class TestCase(unittest.TestCase):

    def assertArraysEqual(self,
            lhs,
            rhs):
        self.assertEqual(lhs.dtype, rhs.dtype)
        try:
            numpy.testing.assert_equal(lhs, rhs)
        except AssertionError as exception:
            self.fail(str(exception))
