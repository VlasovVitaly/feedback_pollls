#!/usr/bin/env python
from pathlib import Path
from aiohttp import web
import aiohttp_jinja2
import jinja2
from tortoise.contrib.aiohttp import register_tortoise
import yaml

from feedback.routes import setup_routes
from auth import setup_auth


def load_config():
    conf_path = Path(__file__).parent / "config" / "config.yaml"

    try:
        with conf_path.open("r") as conf:
            config = yaml.safe_load(conf)
    except FileNotFoundError:
        print('Config file does not exist. Create it from config/config.yaml.template')
        exit(1)

    return config


def setup_application():
    app = web.Application()

    app['config'] = load_config()

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(['templates', 'feedback/templates', 'auth/templates']))

    setup_routes(app)

    register_tortoise(
        app, db_url=app['config']['db_url'],
        modules={'models': ['feedback.models', 'auth.models']},
        generate_schemas=True
    )

    # Development static files
    if app['config']['devel']:
        app.router.add_static('/static/', Path('static'))

    setup_auth(app)

    return app


app = setup_application()


if __name__ == '__main__':
    web.run_app(app)
