from os import environ as env
from aiohttp_security.abc import AbstractAuthorizationPolicy 
from aiohttp_security.session_identity import SessionIdentityPolicy
from aiohttp_security import setup
from aiohttp_session import setup as setup_sessions
from aiohttp_session import SimpleCookieStorage


class SingleUseriEnvAuthPolicy(AbstractAuthorizationPolicy):
    async def authorized_userid(self, identity):
        if identity == env.get('stats_user'):
            return identity
        
    async def permits(self, identity, permission, context=None):
        return await self.authorized_userid and permission == 'stats'


async def check_user(username, password):
    stat_user = env.get('stats_user')
    stat_pass = env.get('stats_pass')

    return (username == stat_user) and (password == stat_pass)


def setup_auth(app):
    setup_sessions(app, SimpleCookieStorage())
    setup(app, SessionIdentityPolicy(), SingleUseriEnvAuthPolicy())