from tortoise.models import Model
from tortoise import fields


class UserSession(Model):
    session_key = fields.CharField(max_length=32, pk=True)
    data = fields.TextField(null=False)
    expires = fields.DatetimeField(null=False)

    def __str__(self):
        return self.session_key
