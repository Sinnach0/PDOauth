# -*- coding: UTF-8 -*-
from twatson.unittest_annotations import Fixture, test
from pdoauth.app import app
from pdoauth import main  # @UnusedImport
from test.TestUtil import UserTesting

class MainTest(Fixture, UserTesting):

    @test
    def NoRootUri(self):
        resp = app.test_client().get("/")
        self.assertEquals(resp.status_code, 404,)

    @test
    def static_files_are_served(self):
        with app.test_client() as c:
            resp = c.get("http://localhost.local/static/index.html")
            self.assertEqual(resp.status_code,200)
