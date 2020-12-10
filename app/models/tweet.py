from django.db import models
from django.conf import settings
import uuid as uuid_lib

class Tweet(models.Model):
    id = models.UUIDField(default=uuid_lib.uuid4,
                          primary_key=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.CharField('内容', max_length=255)
    is_retweet = models.BooleanField('RT', default=False)
    reply_to = models.UUIDField('リプライ先', blank=True, null=True, default=None)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)