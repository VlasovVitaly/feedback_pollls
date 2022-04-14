from os import environ as env
import json
from datetime import datetime, timedelta

from aiohttp_security.abc import AbstractAuthorizationPolicy 
from aiohttp_security.session_identity import SessionIdentityPolicy
from aiohttp_security import setup as setup_security
from aiohttp_session import setup as setup_sessions
from aiohttp_session import AbstractStorage, Session

from feedback.utils import generate_random_string
from .models import UserSession


class SingleUseriEnvAuthPolicy(AbstractAuthorizationPolicy):
    async def authorized_userid(self, identity):
        if identity == env.get('stats_user'):
            return identity
        
    async def permits(self, identity, permission, context=None):
        return await self.authorized_userid(identity) and permission == 'stats'


class ModelSessionStorage(AbstractStorage):
    def __init__(self, model):
        super().__init__(cookie_name='aiohttp_session', httponly=True, encoder=json.dumps, decoder=json.loads)

        self._model = model
    
    async def load_session(self, request):
        cookie = self.load_cookie(request)

        if cookie is None:
            return await self.new_session()
        
        session = await self._model.filter(session_key=cookie, expires__gt=datetime.utcnow()).first()
        if not session:
            return await self.new_session()

        return Session(cookie, data={}, new=False, max_age=self.max_age)
    
    async def save_session(self, request, response, session):
        key = session.identity

        if key is None:
            key = generate_random_string(32)
            self.save_cookie(response, key, max_age=session.max_age)
        else:
            if session.empty:
                self.save_cookie(response, "", max_age=session.max_age)
            else:
                self.save_cookie(response, key, max_age=session.max_age)
        
        data = self._get_session_data(session)
        if not data:
            return
        
        session_fields = {'data': self._encoder(data["session"]), 'expires': datetime.utcnow() + timedelta(days=90)}

        if session.new:
            await self._model.create(session_key=key, **session_fields)
        else:
            await self._model.filter(session_key=key).update(**session_fields)
    
    async def remove_session(self, session, response):
        key = session.identity
        response.del_cookie(self._cookie_name, domain=self.cookie_params['domain'], path=self.cookie_params['path'])

        if key is None:
            return
        
        session = await self._model.filter(session_key=key).first()
        if session:
            await session.delete()


async def check_user(username, password):
    stat_user = env.get('stats_user')
    stat_pass = env.get('stats_pass')

    return (username == stat_user) and (password == stat_pass)


async def log_in(self):
    pass


async def log_out(self):
    pass


def setup_auth(app):
    # setup_sessions(app, SimpleCookieStorage())
    setup_sessions(app, ModelSessionStorage(UserSession))
    setup_security(app, SessionIdentityPolicy(), SingleUseriEnvAuthPolicy())