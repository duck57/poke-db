from django.test import TestCase
from nestlist.models import (
    NstSpeciesListArchive,
    add_a_report,
    NstRawRpt,
    NstAdminEmail,
    NstMetropolisMajor,
    NstNeighborhood,
    NstLocation,
    NstRotationDate,
)
from typing import Optional, List, Dict, Union
from datetime import datetime
from nestlist.utils import append_utc
import time


# Create your tests here.
class ReportingTests(TestCase):
    """Don't normally have these print statements in real tests"""

    @classmethod
    def setUpTestData(cls):
        # setUpTestData: Run once to set up non-modified data for all class methods.
        # up bot IDs, and test nests here
        our_town: NstMetropolisMajor = NstMetropolisMajor.objects.create(
            name="Our Town", active=True
        )
        somewhere_else: NstMetropolisMajor = NstMetropolisMajor.objects.create(
            name="Somewhere Else"
        )
        ffa: NstNeighborhood = NstNeighborhood.objects.create(
            name="Far Far Away", major_city=somewhere_else
        )
        here: NstNeighborhood = NstNeighborhood.objects.create(
            name="Right Here", major_city=our_town
        )
        next_door: NstNeighborhood = NstNeighborhood.objects.create(
            name="Next Door", major_city=our_town
        )
        park1: NstLocation = NstLocation.objects.create(
            pk=1, permanent_species="Wailmer", neighborhood=here
        )
        system: NstAdminEmail = NstAdminEmail.objects.create(pk=1, is_bot=2)
        human: NstAdminEmail = NstAdminEmail.objects.create(pk=2, is_bot=0)
        input_bot: NstAdminEmail = NstAdminEmail.objects.create(pk=3, is_bot=1)
        cls.assertTrue(input_bot.restricted)
        pass

    def setUp(self):
        # print("setUp: Run once for every test method to setup clean data.")
        # TODO: new rotation here
        pass

    def reportingTestSuite(self):
        report_tests: List[Dict] = [
            {
                "name": "junk sample entry",
                "expected_status": 9,
                "nest": 0,
                "species": 1492,
                "user": 42,
                "server": "none of them",
            },
            {
                "name": "confirmed manual entry",
                "nest": 1,
                "species": "Bulbasaur|1",
                "expected_status": 2,
                "user": 7,
                "server": "localhost",
            },
            {
                "name": "unconfirmed manual entry",
                "nest": 1,
                "species": "4",
                "expected_status": 1,
                "user": 7,
                "server": "localhost",
            },
        ]
        for report in report_tests:
            time.sleep(0.007)  # for the timestamps to be chronological
            self.assertEqual(
                add_a_report(
                    name=report["name"],
                    nest=report["nest"],
                    timestamp=append_utc(datetime.utcnow()),
                    species=report["species"],
                    bot_id=report["user"],
                    server=report["server"],
                    rotation=report.get("rotation_id", None),
                ).status,
                report["expected_status"],
            )
        pass
