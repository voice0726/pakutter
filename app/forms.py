from django import forms
from django.contrib.auth.forms import AuthenticationForm
from user.models import UserSetting, User

class TweetForm(forms.Form):
    tweet_content = forms.CharField(label='内容', max_length=255, required=True)

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
       super().__init__(*args, **kwargs)

class UserForm(forms.ModelForm):
    model = User
    fields = ('username',)
    widgets = {
        'username': forms.TextInput(attrs={'size': 40}),
    }

    class Meta:
        model = User
        fields = ('username',)
        widgets = {
            'username': forms.TextInput(attrs={'size': 40}),
        }


class SettingForm(forms.ModelForm):
    model = UserSetting
    fields = ('picture', 'bio')


    class Meta:
        model = UserSetting
        fields = ('picture', 'bio')
