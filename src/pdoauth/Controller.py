from pdoauth.app import mail, app
import flask
from pdoauth.models.User import User
from pdoauth.forms.LoginForm import LoginForm
from pdoauth.CredentialManager import CredentialManager
from flask_login import login_user, current_user, logout_user
from flask.globals import request, session
from pdoauth.forms.RegistrationForm import RegistrationForm
from pdoauth.models.Credential import Credential
from uuid import uuid4
import time
from pdoauth.models.TokenInfoByAccessKey import TokenInfoByAccessKey
from pdoauth.models.Assurance import Assurance, emailVerification
from pdoauth.forms.AssuranceForm import AssuranceForm
from flask import json
from pdoauth.forms.PasswordChangeForm import PasswordChangeForm
from pdoauth.forms.PasswordResetForm import PasswordResetForm
import urllib3
from pdoauth.forms import formValidated
from pdoauth.forms.CredentialForm import CredentialForm
from pdoauth.forms.DigestUpdateForm import DigestUpdateForm
from pdoauth.forms.CredentialIdentifierForm import CredentialIdentifierForm
from pdoauth.forms.DeregisterForm import DeregisterForm
from OpenSSL import crypto

anotherUserUsingYourHash = "another user is using your hash"

class FlaskInterface(object):
    def make_response(self, ret, status):
        return flask.make_response(ret, status)
    
    def validate_on_submit(self,form):
        return form.validate_on_submit()

    def _facebookMe(self, code):
        args = {"access_token":code, 
            "format":"json", 
            "method":"get"}
        http = urllib3.PoolManager()
        resp = http.request('GET', "https://graph.facebook.com/v2.2/me", args)
        return resp

class Responses(object):

    def errors_to_json(self, form):
        errs = []
        for field, errors in form.errors.items():
            for error in errors:
                fieldname = getattr(form, field).label.text
                errs.append("{0}: {1}".format(fieldname,error))
        return errs

    def _make_response(self, descriptor,status=200):
        ret = json.dumps(descriptor)
        return self.make_response(ret, status)
    
    def simple_response(self,text):
        return self._make_response(dict(message=text))
    
    def error_response(self,descriptor, status=400):
        return self._make_response(dict(errors=descriptor), status)
    
    def form_validation_error_response(self, form, status=400):
        errdict = self.errors_to_json(form)
        return self.error_response(errdict, status)
    
    def as_dict(self, user, **kwargs):
        kwargs.update({'email':user.email, 
            'userid':user.userid, 
            'assurances':Assurance.getByUser(user),
            'credentials': Credential.getByUser_as_dictlist(user)
        })
        ret = json.dumps(kwargs)
        return self.make_response(ret,200)

class Controller(Responses):
    
    def __init__(self, interface):
        class __patched(self.__class__):
            pass
        __patched.__bases__ += (interface,)
        self.__class__ = __patched
    
    def email_verification(self, user):
        secret=unicode(uuid4())
        expiry = time.time() + 60*60*24*4
        Credential.new(user, 'emailcheck', unicode(expiry), secret )
        timeText = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(expiry))
        uri = "{0}/v1/verify_email/{1}".format(app.config.get('BASE_URL'),secret)
        text = """Hi, click on <a href="{0}">{0}</a> until {1} to verify your email""".format(uri, timeText)
        mail.send_message(subject="verification", body=text, recipients=[user.email], sender=app.config.get('SERVER_EMAIL_ADDRESS'))
    
    def isAllowedToGetUser(self, userid):
        allowed = False
        authuser = None
        authHeader = request.headers.get('Authorization')
        if current_user.is_authenticated():
            if userid == 'me':
                return (True,current_user)
            if Assurance.getByUser(current_user).has_key('assurer'):
                authuser = User.get(userid)
                return (True, authuser)
        if authHeader:
            token = authHeader.split(" ")[1]
            data = TokenInfoByAccessKey.find(token)
            targetuserid = data.tokeninfo.user_id
            authuser = User.get(targetuserid)
            allowed = authuser.id == userid or userid == 'me'
        return allowed, authuser
    
    def login_create_response(self, user):
        user.set_authenticated()
        r = login_user(user)
        if r:
            resp = self.as_dict(user)
            token = unicode(uuid4())
            session['csrf_token'] = token
            resp.set_cookie("csrf", token)
            return resp
        return self.error_response(["Inactive or disabled user"], status=403)
    
    def passwordLogin(self, form):
        user = CredentialManager.validate_from_form(form)
        if user is None:
            return self.error_response(["Bad username or password"], status=403)
        return self.login_create_response(user)
    
    def facebookLogin(self, form):
        code = form.secret.data
        resp = self._facebookMe(code)
        if 200 != resp.status:
            return self.error_response(["Cannot login to facebook"], 403)
        data = json.loads(resp.data)
        if data["id"] != form.identifier.data:
            return self.error_response(["bad facebook id"], 403)
        cred = Credential.get("facebook", form.identifier.data)
        if cred is None:
            return self.error_response(["You have to register first"], 403)
        user = cred.user
        return self.login_create_response(user)

    @formValidated(LoginForm, 403)
    def do_login(self,form):
        session['logincred'] = dict(credentialType=form.credentialType.data, identifier = form.identifier.data)
        if form.credentialType.data == 'password':
            return self.passwordLogin(form)
        if form.credentialType.data == 'facebook':
            return self.facebookLogin(form)
        raise ValueError() #not reached

    def do_ssl_login(self):
        cert = request.environ.get('SSL_CLIENT_CERT',None)
        if cert is None:
            return self.error_response(["No certificate given"], 403)            
        x509 = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
        digest = x509.digest('sha1')
        cn = x509.get_subject().commonName
        identifier="{0}/{1}".format(
            digest,
            cn
        )
        cred = Credential.get("certificate", identifier)
        if cred is None:
            return self.error_response(["You have to register first"], 403)            
        return self.simple_response("You are logged in")

    @formValidated(DeregisterForm, 400)
    def do_deregister(self,form):
        if not self.isLoginCredentials(form):
            return self.error_response(["You should use your login credentials to deregister"], 400)
        return self.simple_response('deregistered')

    def do_logout(self):
        logout_user()
        return self.simple_response('logged out')

    def isAnyoneHandAssurredOf(self, anotherUsers):
        for anotherUser in anotherUsers:
            for assurance in Assurance.getByUser(anotherUser):
                if assurance not in [emailVerification]:
                    return True        
        return False

    @formValidated(RegistrationForm)
    def do_registration(self, form):
        additionalInfo = {}
        digest = form.digest.data
        if digest == '':
            digest = None
        if digest is not None:
            anotherUsers = User.getByDigest(form.digest.data)
            if anotherUsers:
                if self.isAnyoneHandAssurredOf(anotherUsers):
                    return self.error_response([anotherUserUsingYourHash], 400)
                additionalInfo["message"] = anotherUserUsingYourHash
        user = CredentialManager.create_user_with_creds(
            form.credentialType.data,
            form.identifier.data,
            form.secret.data,
            form.email.data,
            digest)
        self.email_verification(user)
        user.set_authenticated()
        user.activate()
        r = login_user(user)
        if r:
            return self.as_dict(user, **additionalInfo)
    
    def do_change_password(self):
        form = PasswordChangeForm()
        if form.validate_on_submit():
            user = current_user
            cred = Credential.getByUser(user, 'password')
            oldSecret = CredentialManager.protect_secret(form.oldPassword.data)
            if cred.secret != oldSecret:
                return self.error_response(["old password does not match"])
            secret = CredentialManager.protect_secret(form.newPassword.data)
            cred.secret = secret
            cred.save()
            return self.simple_response('password changed succesfully')
        return self.form_validation_error_response(form)
    
    def do_get_by_email(self, email):
        assurances = Assurance.getByUser(current_user)
        if assurances.has_key('assurer'):
            user = User.getByEmail(email)
            if user is None:
                return self.error_response(["no such user"], status=404)
            return self.as_dict(user)
        return self.error_response(["no authorization"], status=403)
    
    @formValidated(AssuranceForm)
    def do_add_assurance(self, form):
        assurances = Assurance.getByUser(current_user)
        neededAssurance = form.assurance.data
        assurerAssurance = "assurer.{0}".format(neededAssurance)
        if assurances.has_key('assurer') and assurances.has_key(assurerAssurance):
            if form.email.data:
                user = User.getByEmail(form.email.data)
                if form.digest.data:
                    users = User.getByDigest(form.digest.data)
                    for anotherUser in users:
                        if anotherUser.email != user.email:
                            anotherUser.hash = None
                            anotherUser.save()
            else:
                users = User.getByDigest(form.digest.data)
                if len(users) > 1:
                    return self.error_response(["Two users with the same hash; specify both hash and email"], 400)  
                user = users[0]                  
            Assurance.new(user, neededAssurance, current_user)
            return self.simple_response("added assurance {0} for {1}".format(neededAssurance, user.email))
        return self.error_response(["no authorization"], 403)
    
    def do_show_user(self, userid):
        allowed, targetuser = self.isAllowedToGetUser(userid)
        if allowed:
            return self.as_dict(targetuser)
        return self.error_response(["no authorization"], status=403)
    
    def do_verify_email(self, token):
        cred = Credential.getBySecret('emailcheck', token)
        if cred is None:
            return self.error_response(["unknown token"], 404)
        if float(cred.identifier) < time.time():
            return self.error_response(["expired token"], 400)
        user = cred.user
        Assurance.new(user,emailVerification,user)
        cred.rm()
        return self.simple_response("email verified OK")
    
    def _sendResetMail(self, user, secret, expiry):
        timeText = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime(expiry))
        serverName = app.config.get('SERVER_NAME')
        uri = "{0}?secret={1}".format(app.config.get("PASSWORD_RESET_FORM_URL"), secret, user.email)
        text = """Hi, click on <a href="{0}">{0}</a> until {1} to reset your password""".format(uri, timeText)
        subject = "Password Reset for {0}".format(serverName)
        mail.send_message(subject=subject, body=text, recipients=[user.email], sender=app.config.get('SERVER_EMAIL_ADDRESS'))
    
    def do_send_password_reset_email(self, email):
        user = User.getByEmail(email)
        if user is None:
            return self.error_response(['Invalid email address'])
        secret=unicode(uuid4())
        expiry = time.time()
        Credential.new(user, 'email_for_password_reset', secret, unicode(expiry+14400))
        self._sendResetMail(user, secret, expiry)
        return self.simple_response("Password reset email has successfully sent.")
    
    @formValidated(PasswordResetForm)
    def do_password_reset(self, form):
        credType = 'email_for_password_reset'
        cred = Credential.get(credType, form.secret.data)
        if cred is None or (float(cred.secret) < time.time()):
            Credential.deleteExpired(credType)
            return self.error_response(['What?'], 404)
        passcred = Credential.getByUser(cred.user, 'password')
        passcred.secret = CredentialManager.protect_secret(form.password.data)
        cred.rm()
        return self.simple_response('Password successfully changed')

    def isLoginCredentials(self, form):
        return session['logincred']['credentialType'] == form.credentialType.data and session['logincred']['identifier'] == form.identifier.data

    @formValidated(CredentialIdentifierForm)
    def do_remove_credential(self, form):
        if self.isLoginCredentials(form):
            return self.error_response(["You cannot delete the login you are using"], 400)            
        cred=Credential.get(form.credentialType.data, form.identifier.data)
        if cred is None:
            return self.error_response(['No such credential'], 404)
        cred.rm()
        return self.simple_response('credential removed')

    @formValidated(CredentialForm)
    def do_add_credential(self, form):
        Credential.new(current_user,
            form.credentialType.data,
            form.identifier.data,
            form.secret.data)
        return self.as_dict(current_user)
    
    @formValidated(DigestUpdateForm)
    def do_update_hash(self,form):
        digest = form.digest.data
        if digest == '':
            digest = None
        current_user.hash = digest
        assurances = Assurance.listByUser(current_user)
        for assurance in assurances:
            if assurance.name != emailVerification:
                assurance.rm()
        return self.simple_response('')