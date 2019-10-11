from django.test import TestCase
from nestlist.models import (
    NstSpeciesListArchive,
    add_a_report,
    NstRawRpt,
    NstAdminEmail,
)


# Create your tests here.
class YourTestClass(TestCase):
    """Don't normally have these print statements in real tests"""

    @classmethod
    def setUpTestData(cls):
        print(
            "setUpTestData: Run once to set up non-modified data for all class methods."
        )
        pass

    def setUp(self):
        print("setUp: Run once for every test method to setup clean data.")
        pass

    def test_false_is_false(self):
        print("Method: test_false_is_false.")
        self.assertFalse(False)

    def test_false_is_true(self):
        print("Method: test_false_is_true.")
        self.assertTrue(False)

    def test_one_plus_one_equals_two(self):
        print("Method: test_one_plus_one_equals_two.")
        self.assertEqual(1 + 1, 2)
