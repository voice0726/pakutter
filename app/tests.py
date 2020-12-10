from django.test import TestCase
from .views import *
from uuid import uuid4

# Create your tests here.
class TweetTest(TestCase):
    fixtures = ['fixture.json']

    def test_get(self):
        tweet_data = get_tweet("fca4b155dd8a45cda8f3c7fbed5d240a", 0, False)
        print(tweet_data)