from django.test import TestCase


# Create your tests here.
class YourTestClass(TestCase):
    """Don't normally have these print statements in real tests"""

    @classmethod
    def setUpTestData(cls):
        """setUpTestData: Run once to set up non-modified data for all class methods."""
        pass

    def setUp(self):
        """setUp: Run once for every test method to setup clean data."""
        pass

    def test_false_is_false(self):
        """Method: test_false_is_false."""
        # self.assertFalse(False)
        pass

    def test_false_is_true(self):
        """Method: test_false_is_true."""
        # self.assertTrue(False)
        pass

    def test_one_plus_one_equals_two(self):
        """Method: test_one_plus_one_equals_two."""
        # self.assertEqual(1 + 1, 2)
        pass
