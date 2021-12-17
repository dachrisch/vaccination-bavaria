from unittest import TestCase

from bs4 import BeautifulSoup

from web import create_app


class TestVaccinationHome(TestCase):
    def setUp(self) -> None:
        self.test_app = create_app()
        self.test_client = self.test_app.test_client()

    def test_call_home(self):
        with self.test_client as client:
            response=client.get('/')
            self.assertEqual(200, response.status_code, response)
            soup=BeautifulSoup(response.data, features='html.parser')
            self.assertEqual('Bavarian Vaccination - Appointment Finder',soup.title.text)
