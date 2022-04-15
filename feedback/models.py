from datetime import date, timedelta
from functools import reduce
from operator import itemgetter

from tortoise import fields
from tortoise.exceptions import IntegrityError
from tortoise.functions import Count
from tortoise.models import Model, Q

from feedback.utils import generate_random_string


ALL_STAT_PERIODS = {
    'day': 'сегодня',
    'week': 'неделю',
    'month': 'месяц',
    'year': 'год'
}


DEFAULT_STAT_PERIOD = 'day'


class Poll(Model):
    url_code = fields.CharField(max_length=10, unique=True, null=True, index=True)
    vote = fields.SmallIntField(null=True, index=True)
    created_date = fields.DateField(default=date.today)
    voted_date = fields.DateField(null=True)

    async def update_urlcode(self):
        while True:
            self.url_code = generate_random_string(5)
            try:
                return await self.save(update_fields=['url_code'])
            except IntegrityError:
                pass

    def __str__(self):
        if self.vote is None:
            return f'[{self.id}]: not voted'

        return f'[{self.id}] {self.url_code} -> {self.vote}'


def calc_rating(ratings):
    rating = {
        'rating': 0, 'total': ratings.total,
        'rate1': ratings.rate1,
        'rate2': ratings.rate2,
        'rate3': ratings.rate3,
        'rate4': ratings.rate4,
        'rate5': ratings.rate5,
    }

    if ratings.total == 0:
        return rating

    all_ratings = zip(
        itemgetter('rate1', 'rate2', 'rate3', 'rate4', 'rate5')(rating), (1, 2, 3, 4, 5)
    )

    total_points = reduce(lambda prev, val: prev + (val[0] * val[1]), all_ratings, 0)
    rating['rating'] = total_points / rating['total']

    return rating


async def get_stats(period):
    rating_annotations = {
        'total': Count('id'),
        'rate1': Count('id', _filter=Q(vote=1)),
        'rate2': Count('id', _filter=Q(vote=2)),
        'rate3': Count('id', _filter=Q(vote=3)),
        'rate4': Count('id', _filter=Q(vote=4)),
        'rate5': Count('id', _filter=Q(vote=5)),
    }

    query_filters = {
        'day': {'voted_date': date.today()},
        'week': {'voted_date__gt': date.today() - timedelta(weeks=1)},
        'month': {'voted_date__gt': date.today() - timedelta(days=30)},
        'year': {'voted_date__gt': date.today() - timedelta(days=365)}
    }

    data = await Poll.filter(**query_filters[period]).only('id').annotate(**rating_annotations).first()
    data = calc_rating(data)

    return data
