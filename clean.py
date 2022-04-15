#!/usr/bin/env python

async def cleanup():
    from datetime import datetime, date, timedelta

    from auth.models import UserSession
    from feedback.models import Poll
    from tortoise import Tortoise

    from main import load_config

    db_uri = load_config().get('db_url')
    year_ago = date.today() - timedelta(days=365)
    now = datetime.utcnow()

    await Tortoise.init(db_url=db_uri, modules={'models': ['feedback.models', 'auth.models']})

    await Poll.filter(vote__isnull=True, created_date__lt=year_ago).delete()
    await UserSession.filter(expires__lt=now).delete()

    await Tortoise.close_connections()


if __name__ == '__main__':
    from asyncio import run as asyncrun

    asyncrun(cleanup())
