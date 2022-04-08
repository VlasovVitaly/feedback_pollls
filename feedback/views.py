from aiohttp import web
from aiohttp_security import remember
import aiohttp_jinja2
from datetime import date

from .models import Poll, get_stats


def check_auth_token(view):
    async def wrapped(request):
        if request.headers.get("auth-token") == request.app['config']['token']:
            return await view(request)

        raise web.HTTPUnauthorized

    return wrapped


@aiohttp_jinja2.template('login.html')
async def login(request):
    if request.method == 'POST':
        response = web.HTTPFound('/')
        data = await request.post()
        user = data.get('user')
        password = data.get('password')

        print(user, type(user))

        await remember(request, response, user)

        print(user, password)
    return {}


@check_auth_token
async def create_poll(request):
    poll = await Poll.create()
    await poll.update_urlcode()

    vote_url = request.app.router['vote'].url_for(url_code=poll.url_code)

    return web.Response(text=f'{request.scheme}://{request.host}{vote_url}')


@aiohttp_jinja2.template('vote.html')
async def vote_poll(request):
    poll = await Poll.get_or_none(url_code=request.match_info['url_code'])

    if request.method == 'POST':
        data = await request.post()

        try:
            rate = int(data['rating'])
            if rate < 1 or rate > 5:
                raise ValueError
        except (KeyError, ValueError, TypeError):
            raise web.HTTPBadRequest

        poll.vote = rate
        poll.voted_date = date.today()

        await poll.save(update_fields=['vote', 'voted_date'])

    return {}


@aiohttp_jinja2.template('vote-thanks.html')
async def vote_thanks(request):
    return {}


@aiohttp_jinja2.template('stats.html')
async def stats(request):
    return await get_stats()