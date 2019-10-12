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
    new_rotation,
)
from typing import Optional, List, Dict, Union
from datetime import datetime
from nestlist.utils import append_utc
import time
from speciesinfo.models import nestable_species


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
            name="Somewhere Else", active=True
        )
        neighborhoods: List[NstNeighborhood] = [
            NstNeighborhood.objects.create(
                name="Far Far Away", major_city=somewhere_else
            ),
            NstNeighborhood.objects.create(name="Right Here", major_city=our_town),
            NstNeighborhood.objects.create(name="Next Door", major_city=our_town),
        ]
        nest_dex_index: int = 0
        nest_objs: List = []
        for _ in range(5):
            for place in neighborhoods:
                nest_objs.append(
                    NstLocation(
                        permanent_species=nestable_species()[nest_dex_index],
                        neighborhood=place,
                    )
                )
        for place in neighborhoods:
            for _ in range(10):
                nest_objs.append(NstLocation(neighborhood=place))
        NstLocation.objects.bulk_create(nest_objs)

        NstAdminEmail.objects.create(pk=1, is_bot=2)  # system
        NstAdminEmail.objects.create(pk=2, is_bot=0, city=our_town)  # human
        NstAdminEmail.objects.create(pk=3, is_bot=1, city=our_town)  # bot
        pass

    def setUp(self):
        # print("setUp: Run once for every test method to setup clean data.")
        self.assertTrue(
            new_rotation(append_utc(datetime.utcnow()), 1).success,
            "Can't create new rotation.",
        )
        pass

    def linkageTest(self):
        """Test that everything is linked up properly"""
        self.assertTrue(NstAdminEmail.objects.get(3).restricted, f"Bot is unrestricted")
        self.assertFalse(
            NstAdminEmail.objects.get(1).restricted, f"System is restricted"
        )
        self.assertFalse(
            NstAdminEmail.objects.get(2).restricted, f"Human is restricted"
        )
        nest_count: int = NstLocation.objects.all().count()
        self.assertEqual(
            nest_count, 45, f"{nest_count} nests were returned.  Expected 45."
        )
        print(
            NstLocation.objects.all()[:10]
        )  # remove me once I have a feel of how the IDs are assigned
        pass

    def reportingTestSuite(self):
        # TODO: flesh out this dict once I know which IDs to use
        # also, document said IDs
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
