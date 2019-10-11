from django.test import TestCase
from .models import (
    Pokemon,
    match_species_by_name_or_number,
    match_species_by_type,
    nestable_species,
)


# Create your tests here.
class TestSpeciesFilter(TestCase):
    """Don't normally have these print statements in real tests"""

    @classmethod
    def setUpTestData(cls):
        """setUpTestData: Run once to set up non-modified data for all class methods."""
        kanto = match_species_by_name_or_number("Kanto")
        pass

    def setUp(self):
        """setUp: Run once for every test method to setup clean data."""
        pass

    def test_generational_filter(self):
        self.assertEqual(len(kanto), 151)

    def test_false_is_true(self):
        print("Method: test_false_is_true.")
        self.assertTrue(False)

    def test_one_plus_one_equals_two(self):
        print("Method: test_one_plus_one_equals_two.")
        self.assertEqual(1 + 1, 2)
