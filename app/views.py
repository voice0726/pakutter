from django.shortcuts import redirect, render, get_object_or_404, Http404
from django.template.loader import render_to_string
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.http import JsonResponse
from django.db import transaction

from app.models.tweet import Tweet
from app.models.fav import Fav
from app.models.follow import Follow
from app.models.retweet import Retweet
from .forms import *

from .consts import *


# Create your views here.
class HomeView(LoginRequiredMixin, generic.ListView):
    """
    View page for logged-in user.
    Get all tweets, follower count, followee count, etc.
    """
    template_name = 'app/home.html'
    model = Tweet
    context_object_name = 'data'

    def get_queryset(self):
        data = {}
        data['user'] = self.request.user
        data['login_user'] = self.request.user
        data['tweets'] = get_tweet(self.request.user, 0, get_following=True)
        data['cnt_following'] = self.request.user.follower.count()
        data['cnt_followed'] = self.request.user.followee.count()
        return data


class UserPageView(generic.ListView):
    """
    User page for not logged-in user.
    Get all tweets posted by a user.
    """
    template_name = 'app/user.html'
    slug_field = "username"  # モデルのフィールドの名前
    slug_url_kwarg = "username"  # urls.pyでのキーワードの名前
    context_object_name = 'data'

    def get_queryset(self):
        data = {}
        user = User.objects.select_related('setting').prefetch_related('followee', 'follower').get(username=self.kwargs['username'])
        data['user'] = user
        data['login_user'] = self.request.user
        data['is_followed_by_login_user'] = bool([i for i in self.request.user.follower.all() if i.followee == user])
        data['tweets'] = get_tweet(user, 0, get_following=False)
        data['cnt_following'] = user.follower.count()
        data['cnt_followed'] = user.followee.count()
        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view_type'] = 'user_page'
        return context


class SettingView(generic.TemplateView):
    model = User
    template_name = 'app/settings.html'
    fields = ()

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['userform'] = UserForm
        context['settingform'] = SettingForm
        return context

    def get_queryset(self):
        return User.objects.get(pk=self.request.user.id)

    def post(self, request, *args, **kwargs):
        user = User.objects.get(pk=self.request.user.id)
        userform = UserForm(self.request.POST, instance=user)
        settingform = SettingForm(self.request.POST, self.request.FILES, instance=user.setting)

        if not userform.is_valid() or not settingform.is_valid():
            return render(self.request, template_name='app/settings.html',
                          context={'userform': userform, 'settingform': settingform})

        setting = UserSetting.objects.get(pk=self.request.user.id)
        setting.bio = settingform.cleaned_data['bio']
        setting.picture = settingform.cleaned_data['picture']

        user = User.objects.get(pk=self.request.user.id)
        user.viewname = userform.cleaned_data['username']

        try:
            setting.save()
            user.save()
        except:
            return redirect('/')

        return redirect('/')


class SearchView(generic.ListView):
    template_name = 'app/search.html'
    context_object_name = 'data'

    def get_queryset(self):
        data = {'tweets': search(self.request.GET.get('keyword'), self.request.user.id)}
        return data


class HashtagView(generic.ListView):
    template_name = 'app/search.html'
    context_object_name = 'data'

    def get_queryset(self):
        data = {}
        data['tweets'] = search('#' + self.request.GET.get('keyword'), self.request.user.id)
        return data


def get_tweet(user, last_index, get_following=False):
    """
    Get tweets by user_id after last_index
    :param user_id:
    :param last_index:
    :param get_following:
    :return:
    """
    following_list = [i.followee_id for i in user.follower.all()]
    target_list = []
    target_list.append(user.id)
    if get_following:
        target_list += following_list
    tweets = Tweet.objects.select_related('user__setting').prefetch_related('fav_set', 'retweet_set').filter(
        user_id__in=target_list).order_by('-created_at')[last_index:last_index + TWEETS_PER_PAGE]

    timeline = []
    for tweet in tweets:
        item = get_rt_fav(tweet, user.id)
        item['user'] = tweet.user
        if tweet.is_retweet:
            # First, search original tweets from data that was already fetched (i.e., you and your follower)
            rt = [i for i in tweets if str(i.id) == tweet.content]
            if len(rt) == 0:
                # If retweeted one is not tweeted by follower of the user
                rt = Tweet.objects.filter(pk=tweet.content).select_related('user__setting').prefetch_related('fav_set',
                                                                                                             'retweet_set')

            rt = rt[0]
            if rt.user_id in following_list and get_following is True:
                # If original tweet is made by follower, skip adding timeline to avoid being displayed twice
                continue
            if rt.user_id not in target_list:
                # If original tweet is not made by you and your follower
                item['tweet'] = rt
                item['user'] = rt.user
                item['fav_count'] = rt.fav_set.count()
                item['rt_count'] = rt.retweet_set.count()
                item['is_faved_by_user'] = is_faved_by_user(rt.fav_set, user.id)
                item['is_rt'] = True
                item['rt_by'] = tweet.user
                timeline.append(item)
                continue

        # Check if the item is retweeted by you or your follower
        rt_set = list(tweet.retweet_set.all())
        for rt in rt_set:
            item['is_rt'] = True
            if rt.user_id == user.id:
                item['rt_by'] = rt.user
                break
            else:
                item['rt_by'] = rt.user

        timeline.append(item)
    return timeline


def get_rt_fav(tweet, user_id):
    return {"tweet": tweet, "fav_count": tweet.fav_set.count(), "rt_count": tweet.retweet_set.count(),
            "is_faved_by_user": is_faved_by_user(tweet.fav_set, user_id)}


def is_faved_by_user(fav_set, user_id):
    if fav_set.count() == 0:
        return False
    fav_set = fav_set.filter(user_id=user_id)
    if len(fav_set) != 0:
        return True
    return False


@transaction.atomic
def retweet(request, tweet_id):
    """
    Post retweet.
    :param request:
    :param tweet_id:
    :return:
    """
    tweet = Tweet()
    tweet.content = tweet_id
    tweet.user_id = request.user.id
    tweet.is_retweet = True

    rt = Retweet()
    rt.user_id = request.user.id
    rt.tweet_id = tweet_id

    try:
        tweet.save()
        rt.save()
        count = Retweet.objects.filter(tweet_id=tweet_id).count()
        return JsonResponse({'status': 200, 'count': count})
    except:
        return JsonResponse({'status': 500})



@transaction.atomic
def unretweet(request, tweet_id):
    retweet = Retweet.objects.get(user_id=request.user.id, tweet_id=tweet_id)
    tweet = Tweet.objects.get(is_retweet=True, content=str(tweet_id))
    try:
        retweet.delete()
        tweet.delete()
        count = retweet.objects.filter(tweet_id=tweet_id).count()
        return JsonResponse({'status': 200, 'count': count})
    except:
        return JsonResponse({'status': 500})


@login_required
def follow(request, user_id):
    follow = Follow()
    follow.follower_id = request.user.id
    follow.followee_id = user_id
    try:
        follow.save()
    except:
        return JsonResponse({'status': 500})
    return JsonResponse({'status': 200})


@login_required
def unfollow(request, user_id):
    try:
        Follow.objects.get(follower_id=request.user.id, followee_id=user_id).delete()
    except:
        return JsonResponse({'status': 500})
    return JsonResponse({'status': 200})


@login_required
def post_tweet(request):
    form = TweetForm(request.POST or None)

    if form.is_valid():
        tweet = Tweet()
        tweet.content = form.cleaned_data['tweet_content']
        tweet.user = request.user

        tweet.save()
        return redirect('app:index')
    return redirect('app:index')


def search(keyword, user_id):
    tweets = Tweet.objects.filter(content__icontains=keyword)[:TWEETS_PER_PAGE]

    timeline = []

    for tweet in tweets:
        item = get_rt_fav(tweet, user_id)
        timeline.append(item)

    return timeline


@login_required
def reply(request, reply_to):
    form = TweetForm(request.POST or None)

    if form.is_valid():
        tweet = Tweet()
        tweet.content = form.cleaned_data['tweet_content']
        tweet.reply_to = reply_to
        tweet.user = request.user

        Tweet.objects.create(content=tweet.content, user=tweet.user, reply_to=tweet.reply_to)
        return redirect('app:index')
    return redirect('app:index')


@login_required
def delete_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id)
    if tweet.user == request.user:
        tweet.delete()
        return redirect('app:index')
    return redirect('app:index')


@login_required
def fav(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id)
    fav = Fav()
    fav.tweet = tweet
    fav.user = request.user
    try:
        fav.save()
        count = Fav.objects.filter(tweet_id=tweet_id).count()
        return JsonResponse({'status': 200, 'count': count})
    except:
        return JsonResponse({'status': 500})


@login_required
def unfav(request, tweet_id):
    fav = get_object_or_404(Fav, tweet_id=tweet_id, user=request.user)
    try:
        fav.delete()
        count = Fav.objects.filter(tweet_id=tweet_id).count()
        return JsonResponse({'status': 200, 'count': count})
    except:
        return JsonResponse({'status': 500})


def auth(request):
    form = LoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        user = settings.AUTH_USER_MODEL.objects.get(username=username)
        try:
            login(request, user)
            json = {
                'auth': 'success',
            }
        except:
            json = {
                'auth': 'failure',
            }
        return JsonResponse(json)
    json = {
        'auth': 'failure',
    }
    return JsonResponse(json)


def get_more_tweets(request):
    with_following = False
    if request.POST['with_following'] == 'true':
        with_following = True

    user = User.objects.get(pk=request.POST['user_id'])
    tweets = get_tweet(user, int(request.POST['last_item_num']), with_following)
    if len(tweets) == 0:
        return JsonResponse({'fetched': 'False'})

    html = render_to_string('app/tweet_box.html',
                            {'data': {'tweets': tweets, 'user': request.user, 'login_user': request.user}})
    return JsonResponse({'fetched': 'True', 'html': html}, safe=False)


def get_tweet_json(request, tweet_id):
    """
    Get tweet json for reply modal.
    :param request:
    :param tweet_id:
    :return:
    """
    try:
        tweet = Tweet.objects.get(pk=tweet_id)
    except Tweet.DoesNotExist:
        return JsonResponse({'status': 500})

    return JsonResponse({'status': 200, 'username': tweet.user.username, 'content': tweet.content,
                         'time': "{0:%Y-%m-%d %H:%M:%S}".format(tweet.created_at)})


@login_required
def get_all_replies(request, tweet_id):
    data = []
    try:

        tweet = Tweet.objects.get(pk=tweet_id)
        data.append({'username': tweet.user.username, 'content': tweet.content,
                'time': "{0:%Y-%m-%d %H:%M:%S}".format(tweet.created_at)})
        # get previous ones
        while tweet.reply_to != "":
            try:
                tweet = Tweet.objects.get(pk=tweet.reply_to)
            except:
                break
            data.append({'username': tweet.user.username, 'content': tweet.content,
                     'time': "{0:%Y-%m-%d %H:%M:%S}".format(tweet.created_at)})
    except Exception as e:
        return JsonResponse({'status': 500})

    return JsonResponse({'status': 200, 'data': data})

