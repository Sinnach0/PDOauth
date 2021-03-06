
from twatson.unittest_annotations import Fixture, test
import config
from pdoauth.app import app
from pdoauth.models.Credential import Credential
from Crypto.Hash.SHA256 import SHA256Hash
from pdoauth.models.User import User
from pdoauth.forms import credErr
from pdoauth.ReportedError import ReportedError
from test.helpers.todeprecate.UserTesting import UserTesting

class CredentialTest(Fixture, UserTesting):
    def setUp(self):
        self.setupRandom()
        self.user = self.createUserWithCredentials()
        self.cred=Credential.get('password', self.usercreation_userid)

    @test
    def Credential_representation_is_readable(self):
        secretdigest=SHA256Hash(self.usercreation_password).hexdigest()
        representation = "Credential(user={0},credentialType=password,secret={1})".format(
            self.usercreation_email,
            secretdigest)
        self.assertEquals("{0}".format(self.cred),representation)
        
    @test
    def Credential_can_be_retrieved_by_type_and_identifier(self):
        self.assertEquals(self.cred.user, self.user)

    @test
    def a_logged_in_user_can_add_credential(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            data = {
                "credentialType": "password",
                "identifier": "user_{0}".format(self.randString),
                "secret": "secret is {0}".format(self.mkRandomPassword())
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(200, resp.status_code)

    @test
    def when_a_credential_is_added_the_response_contains_user_data_which_contains_her_credentials(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            username = "user_{0}".format(self.randString)
            data = {
                "credentialType": "password",
                "identifier": username,
                "secret": "secret is {0}".format(self.mkRandomPassword())
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            text = self.getResponseText(resp)
            self.assertTrue(username in text)

    @test
    def a_not_logged_in_user_cannot_add_credential(self):
        with app.test_client() as c:
            self.setupRandom()
            data = {
                "credentialType": "password",
                "identifier": "user_{0}".format(self.randString),
                "secret": "secret is {0}".format(self.randString)
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(302, resp.status_code)

    @test
    def the_credential_is_actually_added(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            username = "user_{0}".format(self.randString)
            data = {
                "credentialType": "password",
                "identifier": username,
                "secret": "secret is {0}".format(self.mkRandomPassword())
            }
            uri = config.base_url + "/v1/add_credential"
            credBefore = Credential.get("password", username)
            self.assertTrue(credBefore is None)
            resp = c.post(uri, data=data)
            self.assertEqual(200, resp.status_code)
            credAfter = Credential.get("password", username)
            self.assertTrue(credAfter is not None)

    @test
    def the_added_credential_should_contain_credentialType(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            username = "user_{0}".format(self.randString)
            data = {
                "identifier": username,
                "secret": "secret is {0}".format(self.mkRandomPassword())
            }
            uri = config.base_url + "/v1/add_credential"
            credBefore = Credential.get("password", username)
            self.assertTrue(credBefore is None)
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            credAfter = Credential.get("password", username)
            self.assertTrue(credAfter is None)
            self.assertEqual('{{"errors": [{0}]}}'.format(credErr), self.getResponseText(resp))

    @test
    def the_added_credential_should_contain_valid_credentialType(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            username = "user_{0}".format(self.randString)
            data = {
                "credentialType": "invalid",
                "identifier": username,
                "secret": "secret is {0}".format(self.mkRandomPassword())
            }
            uri = config.base_url + "/v1/add_credential"
            credBefore = Credential.get("password", username)
            self.assertTrue(credBefore is None)
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            credAfter = Credential.get("password", username)
            self.assertTrue(credAfter is None)
            self.assertEqual('{{"errors": [{0}]}}'.format(credErr), self.getResponseText(resp))

    @test
    def the_added_credential_should_contain_identifier(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            data = {
                "credentialType": "password",
                "secret": "secret is {0}".format(self.mkRandomPassword())
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["identifier: Field must be between 4 and 250 characters long."]}', self.getResponseText(resp))

    @test
    def the_added_credential_should_contain_valid_identifier(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            data = {
                "credentialType": "password",
                "identifier": "aaa",
                "secret": "secret is {0}".format(self.mkRandomPassword())
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["identifier: Field must be between 4 and 250 characters long."]}', self.getResponseText(resp))

    @test
    def the_added_credential_should_contain_secret(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            username = "user_{0}".format(self.randString)
            data = {
                "credentialType": "password",
                "identifier": username,
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["secret: Field must be at least 8 characters long.", "secret: password should contain lowercase", "secret: password should contain uppercase", "secret: password should contain digit"]}',
                 self.getResponseText(resp))

    @test
    def the_password_should_be_at_least_8_characters_long(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            username = "user_{0}".format(self.randString)
            data = {
                "credentialType": "password",
                "identifier": username,
                "secret": "sH0rt"
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["secret: Field must be at least 8 characters long."]}', self.getResponseText(resp))

    @test
    def the_password_should_contain_lowercase_letters(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            username = "user_{0}".format(self.randString)
            data = {
                "credentialType": "password",
                "identifier": username,
                "secret": "THIS P4SSWORD IS UPPERCASE"
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["secret: password should contain lowercase"]}', self.getResponseText(resp))

    @test
    def the_password_should_contain_uppercase_letters(self):
        with app.test_client() as c:
            self.login(c)
            self.setupRandom()
            username = "user_{0}".format(self.randString)
            data = {
                "credentialType": "password",
                "identifier": username,
                "secret": "th1s p4ssw0rd 15 10w3rc453"
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["secret: password should contain uppercase"]}', self.getResponseText(resp))

    @test
    def cannot_add_an_already_existing_identifier(self):
        with app.test_client() as c:
            self.login(c)
            data = {
                "credentialType": "password",
                "identifier": self.usercreation_userid,
                "secret": self.mkRandomPassword()
            }
            uri = config.base_url + "/v1/add_credential"
            resp = c.post(uri, data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["identifier: There is already a user with that username"]}', self.getResponseText(resp))

    @test
    def a_credential_can_be_deleted(self):
        with app.test_client() as c:
            self.login(c)
            user = User.getByEmail(self.usercreation_email)
            credId = self.randString
            Credential.new(user, "facebook", credId, "testsecret")
            self.assertTrue(Credential.get("facebook", credId))
            data = {
                "credentialType": "facebook",
                "identifier": credId,
            }
            resp = c.post(config.base_url + "/v1/remove_credential", data=data)
            self.assertEqual(200, resp.status_code)
            self.assertEqual('{"message": "credential removed"}', self.getResponseText(resp))
            
    @test
    def the_credential_is_actually_deleted(self):
        with app.test_client() as c:
            self.login(c)
            user = User.getByEmail(self.usercreation_email)
            credId = self.randString
            Credential.new(user, "facebook", credId, "testsecret")
            self.assertTrue(Credential.get("facebook", credId))
            data = {
                "credentialType": "facebook",
                "identifier": credId,
            }
            c.post(config.base_url + "/v1/remove_credential", data=data)
            self.assertFalse(Credential.get("facebook", credId))

    @test
    def you_should_give_the_credentialType_for_credential_deletion(self):
        with app.test_client() as c:
            self.login(c)
            credId = self.randString
            data = {
                "identifier": credId,
            }
            resp = c.post(config.base_url + "/v1/remove_credential", data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{{"errors": [{0}]}}'.format(credErr), self.getResponseText(resp))

    @test
    def you_should_give_valid_credentialType_for_credential_deletion(self):
        with app.test_client() as c:
            self.login(c)
            credId = self.randString
            data = {
                "identifier": credId,
                "credentialType": "test",
            }
            resp = c.post(config.base_url + "/v1/remove_credential", data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{{"errors": [{0}]}}'.format(credErr), self.getResponseText(resp))

    @test
    def you_should_give_the_identifier_for_credential_deletion(self):
        with app.test_client() as c:
            self.login(c)
            data = {
                "credentialType": "facebook",
            }
            resp = c.post(config.base_url + "/v1/remove_credential", data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["identifier: Field must be between 4 and 250 characters long."]}', self.getResponseText(resp))

    @test
    def you_should_give_valid_identifier_for_credential_deletion(self):
        with app.test_client() as c:
            self.login(c)
            user = User.getByEmail(self.usercreation_email)
            credId = self.randString
            Credential.new(user, "facebook", credId, "testsecret")
            self.assertTrue(Credential.get("facebook", credId))
            data = {
                "identifier": credId+"no",
                "credentialType": "facebook",
            }
            resp = c.post(config.base_url + "/v1/remove_credential", data=data)
            self.assertEqual(404, resp.status_code)
            self.assertEqual('{"errors": ["No such credential"]}', self.getResponseText(resp))

    @test
    def the_credential_used_for_login_cannot_be_cleared(self):
        with app.test_client() as c:
            self.login(c)
            self.assertTrue(Credential.get("password", self.usercreation_userid))
            data = {
                "identifier": self.usercreation_userid,
                "credentialType": "password",
            }
            resp = c.post(config.base_url + "/v1/remove_credential", data=data)
            self.assertEqual(400, resp.status_code)
            self.assertEqual('{"errors": ["You cannot delete the login you are using"]}', self.getResponseText(resp))
            self.assertTrue(Credential.get("password", self.usercreation_userid))

    @test
    def an_already_existing_credential_cannot_be_addedd(self):
        self.createUserWithCredentials(userid="existinguser")
        with self.assertRaises(ReportedError):
            self.createUserWithCredentials(userid="existinguser")
        cred = Credential.get("password", "existinguser")
        cred.rm()
