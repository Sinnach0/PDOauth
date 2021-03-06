from pdoauth.AuthProvider import AuthProvider

class ServerSide(object):
    def doServerSideRequest(self, code):
        postData = {'code':code, 
            'grant_type':'authorization_code', 
            'client_id':self.appid, 
            'client_secret':self.appsecret, 
            'redirect_uri':'https://test.app/redirecturi'}
        self.controller._testdata.postdata = postData
        resp = AuthProvider().token_interface()
        data = self.fromJson(resp)
        self.assertTrue(data.has_key('access_token'))
        self.assertTrue(data.has_key('refresh_token'))
        self.assertEquals(data['token_type'], 'Bearer')
        self.assertEquals(data['expires_in'], 3600)
        return data

