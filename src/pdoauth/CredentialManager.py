from Crypto.Hash.SHA256 import SHA256Hash
from pdoauth.models.User import User
from pdoauth.models.Credential import Credential

class CredentialManager(object):
    @classmethod
    def protect_secret(cls, credtype, identifier, secret):
        return SHA256Hash(secret).hexdigest()

    @classmethod
    def create_user_with_creds(cls, credtype, identifier, secret):
        user = User.new()
        protected = cls.protect_secret(credtype, identifier, secret)
        Credential.new(user, credtype, identifier, protected)
        return user

    
    @classmethod
    def validate_from_form(cls, form):
        cred = Credential.get('password', form.username.data)
        if cred is None:
            return None
        hashed = cls.protect_secret('password', form.username.data, form.password.data)
        if cred.secret == hashed:
            return cred.user
        return None
    
    
    
    
    
    