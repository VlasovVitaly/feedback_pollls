from feedback.views import create_poll, vote_poll, vote_thanks, login


def setup_routes(application):
    application.router.add_post('/create', create_poll)
    application.router.add_post(r'/e/{url_code:[a-z0-9]{5}}', vote_poll, name='vote_post')
    application.router.add_get(r'/e/{url_code:[a-z0-9]{5}}', vote_poll, name='vote')
    application.router.add_get(r'/e/{url_code:[a-z0-9]{5}}/thanks', vote_thanks, name='vote_thanks')
