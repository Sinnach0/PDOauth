
from pyoauth2_shift.provider import AuthorizationProvider
from pdoauth.models.Application import Application
from pdoauth.models.KeyData import KeyData
from pdoauth.models.TokenInfoByAccessKey import TokenInfoByAccessKey
from pdoauth.Controller import Interfaced

class ScopeMustBeEmpty(Exception):
    pass

class DiscardingNonexistingToken(Exception):
    pass

class AuthProvider(AuthorizationProvider,Interfaced):

    def validate_client_id(self,client_id):
        if client_id is None:
            return False
        app = Application.get(client_id)
        return app
    def validate_client_secret(self,client_id,client_secret):
        if client_id is None:
            return False
        app = Application.get(client_id)
        return app.secret == client_secret
    
    def validate_redirect_uri(self,client_id,redirect_uri):
        if client_id is None or\
           redirect_uri is None:
            return False
        app = Application.get(client_id)
        if app is None:
            return False
        return app.redirect_uri == redirect_uri.split("?")[0]
    
    def validate_scope(self,client_id, scope):
        return scope == ""
    
    def validate_access(self):
        return self.getCurrentUser().is_authenticated()

    def persist_token_information(self, client_id, scope, access_token, token_type, expires_in, refresh_token, data):
        keydata = KeyData.new(client_id, data.user_id, access_token, refresh_token)
        TokenInfoByAccessKey.new(access_token, keydata, expires_in)

    
    def from_refresh_token(self,client_id, refresh_token, scope):
        if scope != '':
            raise ScopeMustBeEmpty()
        return KeyData.find_by_refresh_token(client_id, refresh_token)
    
    def discard_refresh_token(self, client_id, refresh_token):
        keyData = self.from_refresh_token(client_id, refresh_token, '')
        if keyData is None:
            raise DiscardingNonexistingToken()
        keyData.rm()
        
    def persist_authorization_code(self, client_id, code, scope):
        keyData = KeyData(client_id=client_id, authorization_code = code, user_id=self.getCurrentUser().userid)
        keyData.save()

    def from_authorization_code(self, client_id, code, scope):
        return KeyData.find_by_code(client_id=client_id,authorization_code = code)

    def discard_authorization_code(self, client_id, code):
        keydata = self.from_authorization_code(client_id, code, '')
        keydata.rm()
        
    def auth_interface(self):
        provider = AuthProvider()
        response = provider.get_authorization_code_from_uri(self.getRequestUrl())
        flask_res = self.make_response(response.text, response.status_code)
        for k, v in response.headers.iteritems():
            flask_res.headers[k] = v
        return flask_res

    def token_interface(self):
        provider = AuthProvider()
        requestForm = self.getRequestForm()
        data = {k:requestForm[k] for k in requestForm.iterkeys()}
        response = provider.get_token_from_post_data(data)
        flask_res = self.make_response(response.text, response.status_code)
        for k, v in response.headers.iteritems():
            flask_res.headers[k] = v
        
        return flask_res
