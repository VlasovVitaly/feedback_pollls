import json
from datetime import datetime, timedelta
from os import environ as env

from aiohttp.web import HTTPFound
from aiohttp_security import (AbstractAuthorizationPolicy,
                              SessionIdentityPolicy, authorized_userid)
from aiohttp_security import setup as setup_security
from aiohttp_session import AbstractStorage, Session, get_session
from aiohttp_session import setup as setup_sessions

from feedback.utils import generate_random_string

from .models import UserSession

SESSION_AGE_DAYS = 90


class SingleUseriEnvAuthPolicy(AbstractAuthorizationPolicy):
    async def authorized_userid(self, identity):
        return identity == env.get('stats_user')

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

        session_data = {'session': self._decoder(session.data)}
        return Session(cookie, data=session_data, new=False, max_age=self.max_age)

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

        session_fields = {
            'data': self._encoder(data["session"]),
            'expires': datetime.utcnow() + timedelta(days=SESSION_AGE_DAYS)
        }

        if session.new:
            await self._model.create(session_key=key, **session_fields)
        else:
            await self._model.filter(session_key=key).update(**session_fields)


def login_required(handler, login_url='/login'):
    async def wrapped(request, *args, **kwargs):
        user = await authorized_userid(request)

        if not user:
            raise HTTPFound(login_url)

        session = await get_session(request)
        if not session.new:
            session.changed()

        return await handler(request, *args, **kwargs)

    return wrapped


async def check_user(username, password):
    return (username == env.get('stats_user')) and (password == env.get('stats_pass'))


def setup_auth(app):
    setup_sessions(app, ModelSessionStorage(UserSession))
    setup_security(app, SessionIdentityPolicy(), SingleUseriEnvAuthPolicy())
