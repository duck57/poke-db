from django.test import TestCase
from .models import (
    Pokemon,
    match_species_by_name_or_number,
    match_species_by_type,
    nestable_species,
    enabled_in_PoGO,
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
        self.assertEqual(kanto.count(), 151)
        pass

    def test_meltan_enabled(self):
        self.assertIn(Pokemon.objects.get(name="Meltan"), enabled_in_PoGO())
        pass

    def test_meltan_nestable(self):
        self.assertNotIn(
            Pokemon.objects.get(name="Meltan"), enabled_in_PoGO(nestable_species())
        )

    def test_alola_available(self):
        self.assertIn(Pokemon.objects.get(name="Alolan Vulpix"), enabled_in_PoGO())

    def test_alola_nestable(self):
        self.assertNotIn(
            Pokemon.objects.get(name="Alolan Vulpix"),
            enabled_in_PoGO(nestable_species()),
        )
