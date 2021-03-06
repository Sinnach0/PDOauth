
from pdoauth.app import app
from pdoauth import main  # @UnusedImport
from test.helpers.ResponseInfo import ResponseInfo
from test.helpers.PDUnitTest import PDUnitTest, test

class UriServiceTest(PDUnitTest, ResponseInfo):

    def _checkUri(self, checkedUri):
        resp = self.controller.do_uris()
        self.assertEquals(resp.status_code, 200)
        uris = self.fromJson(resp)
        self.assertTrue(uris[checkedUri] is not None)
        self.assertEqual(uris[checkedUri], app.config.get(checkedUri))

    @test
    def the_uri_service_gives_back_the_BASE_URL(self):
        self._checkUri('BASE_URL')

    @test
    def the_uri_service_gives_back_the_SSL_LOGIN_BASE_URL(self):
        self._checkUri('SSL_LOGIN_BASE_URL')

    @test
    def the_uri_service_gives_back_the_PASSWORD_RESET_FORM_URL(self):
        self._checkUri('PASSWORD_RESET_FORM_URL')

    @test
    def the_uri_service_gives_back_the_START_URL(self):
        self._checkUri('START_URL')

    @test
    def the_uri_service_gives_back_the_SSL_LOGOUT_URL(self):
        self._checkUri('SSL_LOGOUT_URL')
