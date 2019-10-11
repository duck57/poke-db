from django.test import TestCase
from nestlist.models import (
    NstSpeciesListArchive,
    add_a_report,
    NstRawRpt,
    NstAdminEmail,
)
from typing import Optional, List, Dict, Union
from datetime import datetime


# Create your tests here.
class ReportingTests(TestCase):
    """Don't normally have these print statements in real tests"""

    @classmethod
    def setUpTestData(cls):
        # setUpTestData: Run once to set up non-modified data for all class methods.
        # TODO: set up bot IDs, and test nests here
        pass

    def setUp(self):
        # print("setUp: Run once for every test method to setup clean data.")
        pass

    def reportingTestSuite(self):
        report_tests: List[Dict] = [
            {
                "name": "confirmed manual entry",
                "nest": 1,
                "species": "Bulbasaur|1",
                "expected_status": 2,
                "timestamp": "17 March 1592 17:03:23",
                "user": 7,
                "server": "localhost",
                "rotation_id": None,
            },
            {
                "name": "unconfirmed manual entry",
                "nest": 1,
                "species": "4",
                "expected_status": 1,
                "timestamp": "17 March 1592 17:03:23",
                "user": 7,
                "server": "localhost",
                "rotation_id": None,
            },
        ]
        for report in report_tests:
            self.assertEqual(
                add_a_report(
                    name=report["name"],
                    nest=report["nest"],
                    timestamp=report["timestamp"],
                    species=report["species"],
                    bot_id=report["user"],
                    server=report["server"],
                    rotation=report["rotation_id"],
                ).status,
                report["expected_status"],
            )
        pass
