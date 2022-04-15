from datetime import date

import aiohttp_jinja2
from aiohttp import web
from aiohttp_security import forget, remember

from auth import check_user, login_required
from feedback.models import (ALL_STAT_PERIODS, DEFAULT_STAT_PERIOD, Poll,
                             get_stats)


def check_auth_token(view):
    async def wrapped(request):
        if request.headers.get("auth-token") == request.app['config']['token']:
            return await view(request)

        raise web.HTTPUnauthorized

    return wrapped


@aiohttp_jinja2.template('login.html')
async def login(request):
    context = {}

    if request.method == 'POST':
        form_data = await request.post()
        user = form_data.get('username')
        password = form_data.get('password')

        if await check_user(username=user, password=password):
            response = web.HTTPFound('/stats')
            await forget(request, response)
            await remember(request, response, user)
            return response

        context['fields'] = {}
        context['fields']['username'] = user
        context['fields']['password'] = password
        context['form_error'] = 'невозможно зайти под этими учетным данными'

    return context


@check_auth_token
async def create_poll(request):
    forwarded_proto = request.headers.get('X-Forwarded-Proto')
    poll = await Poll.create()
    await poll.update_urlcode()

    vote_url = request.app.router['vote'].url_for(url_code=poll.url_code)

    return web.Response(text=f'{forwarded_proto or request.scheme}://{request.host}{vote_url}')


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


@login_required
@aiohttp_jinja2.template('stats.html')
async def stats(request):
    period = request.query.get('period')
    
    if not period or period not in ALL_STAT_PERIODS:
        period  = DEFAULT_STAT_PERIOD

    context = await get_stats(period)
    context['current'] = period
    context['period_name'] = ALL_STAT_PERIODS[period]

    return context