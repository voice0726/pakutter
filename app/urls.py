from django.contrib import admin
from django.urls import path, re_path
from .views import *
from django.conf import settings
from django.contrib.staticfiles.urls import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

app_name = 'app'
urlpatterns = [
    path('', HomeView.as_view(), name='index'),
    path('login', auth, name='login'),
    path('load_more', get_more_tweets, name='load_more'),
    path('post', post_tweet, name='post_tweet'),
    path('search/', SearchView.as_view(), name='search'),
    path('hashtag/', HashtagView.as_view(), name='hashtag'),
    re_path(r'^settings/$', SettingView.as_view(), name='settings'),
    re_path(r'^json/(?P<tweet_id>[a-zA-Z0-9\-_]+)$', get_tweet_json, name='get_tweet_json'),
    re_path(r'^detail/(?P<tweet_id>[a-zA-Z0-9\-_]+)$', get_all_replies, name='get_detail'),
    re_path(r'^delete/(?P<tweet_id>[a-zA-Z0-9\-_]+)$', delete_tweet, name='delete_tweet'),
    re_path(r'^fav/(?P<tweet_id>[a-zA-Z0-9\-_]+)$', fav, name='fav_tweet'),
    re_path(r'^unfav/(?P<tweet_id>[a-zA-Z0-9\-_]+)$', unfav, name='unfav_tweet'),
    re_path(r'^retweet/(?P<tweet_id>[a-zA-Z0-9\-_]+)$', retweet, name='retweet'),
    re_path(r'^unretweet/(?P<tweet_id>[a-zA-Z0-9\-_]+)$', unretweet, name='unretweet'),
    re_path(r'^reply/(?P<reply_to>[a-zA-Z0-9\-_]+)$', reply, name='reply'),
    re_path(r'^follow/(?P<user_id>[a-zA-Z0-9\-_]+)$', follow, name='follow'),
    re_path(r'^unfollow/(?P<user_id>[a-zA-Z0-9\-_]+)$', unfollow, name='unfollow'),
    re_path(r'^(?P<username>[a-zA-Z0-9_]+)/$', UserPageView.as_view(), name='user_page'),
]
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
