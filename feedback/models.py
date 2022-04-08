from tortoise.models import Model
from tortoise.exceptions import IntegrityError
from tortoise import fields

from feedback.utils import generate_random_string


class Poll(Model):
    url_code = fields.CharField(max_length=10, unique=True, null=True, index=True)
    vote = fields.SmallIntField(null=True, index=True)
    created_timestamp = fields.DatetimeField(auto_now_add=True)
    voted_timestamp = fields.DatetimeField(null=True)

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
