import logging
import re
from operator import itemgetter
from urllib.parse import quote, urlencode, urlparse

from django.shortcuts import redirect
from django import forms
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from requests import HTTPError
import requests
from reversion import revisions
from django.conf import settings
from social_core.backends.github import GithubOAuth2
from social_core.backends.oauth import BaseOAuth2
from social_core.exceptions import InvalidEmail, SocialAuthBaseException
from social_core.pipeline.partial import partial
from social_django.middleware import SocialAuthExceptionMiddleware as OldSocialAuthExceptionMiddleware

from judge.forms import ProfileForm
from judge.models import Language, Profile

logger = logging.getLogger('judge.social_auth')


class GitHubSecureEmailOAuth2(GithubOAuth2):
    name = 'github-secure'

    def user_data(self, access_token, *args, **kwargs):
        data = self._user_data(access_token)
        try:
            emails = self._user_data(access_token, '/emails')
        except (HTTPError, ValueError, TypeError):
            emails = []

        emails = [(e.get('email'), e.get('primary'), 0) for e in emails if isinstance(e, dict) and e.get('verified')]
        emails.sort(key=itemgetter(1), reverse=True)
        emails = list(map(itemgetter(0), emails))

        if emails:
            data['email'] = emails[0]
        else:
            data['email'] = None

        return data

class MoodleOAuth2(BaseOAuth2):
    name = 'moodle'
    AUTHORIZATION_URL = f"http://{settings.MOODLE_DOMAIN}/local/oauth/login.php"
    ACCESS_TOKEN_URL = f'http://{settings.MOODLE_DOMAIN}/local/oauth/token.php'
    ACCESS_TOKEN_METHOD = 'POST'
    SCOPE_SEPARATOR = ' '
    REDIRECT_STATE = False
    RESPONSE_TYPE = 'code'
    EXTRA_DATA = [
        ('id', 'id'),
        ('expires', 'expires'),
        ('access_token', 'access_token'),
        ('refresh_token', 'refresh_token'),
    ]

    def user_data(self, access_token, *args, **kwargs):
        url = f"http://{settings.MOODLE_DOMAIN}/local/oauth/user_info.php?" + urlencode({
            'access_token': access_token
        })

        try:
            return self.get_json(url)
        except (HTTPError, ValueError, TypeError):
            return {}

    def get_user_details(self, response):
        return {
            'username': response.get('username', ''),
            'password': response.get('password', ''),
            'email': response.get('email', ''),
            'id': response.get('userid', None),
            'first_name': response.get('firstname', ''),
            'last_name': response.get('lastname', ''),
        }


def slugify_username(username, renotword=re.compile(r'[^\w]')):
    return renotword.sub('', username.replace('-', '_'))


def verify_email(backend, details, *args, **kwargs):
    if not details['email']:
        raise InvalidEmail(backend)


class UsernameForm(forms.Form):
    username = forms.RegexField(regex=r'^\w+$', max_length=30, label='Username',
                                error_messages={'invalid': 'A username must contain letters, numbers, or underscores.'})
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        min_length=6
    )

    def clean_username(self):
        if User.objects.filter(username=self.cleaned_data['username']).exists():
            raise forms.ValidationError('Sorry, the username is taken.')
        return self.cleaned_data['username']


@partial
def choose_username(backend, user, username=None, *args, **kwargs):
    if not user:
        request = backend.strategy.request
        if request.POST:
            form = UsernameForm(request.POST)
            if form.is_valid():
                return {
                    'username': form.cleaned_data['username'],
                    'password': form.cleaned_data['password'],
                }
        else:
            form = UsernameForm(initial={'username': username})
        return render(request, 'registration/username_select.html', {
            'title': 'Choose a username', 'form': form,
        })

# We are not using this right now, might comeback to it later
@partial
def post_login_sync(backend, user, response, *args, **kwargs):
    if backend.name == "moodle":
        social = user.social_auth.get(provider='moodle')
        access_token = social.response.get('access_token')
        
        if access_token:
            requests.post(
                f"http://{settings.MOODLE_DOMAIN}/api/sync",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=5
            )

@partial
def make_profile(backend, user, response, is_new=False, *args, **kwargs):
    if is_new:
        if not hasattr(user, 'profile'):
            profile = Profile(user=user)
            profile.language = Language.get_default_language()
            logger.info('Info from %s: %s', backend.name, response)
            profile.save()
            form = ProfileForm(instance=profile, user=user)
        else:
            data = backend.strategy.request_data()
            logger.info(data)
            form = ProfileForm(data, instance=user.profile, user=user)
            if form.is_valid():
                with revisions.create_revision(atomic=True):
                    form.save()
                    revisions.set_user(user)
                    revisions.set_comment('Updated on registration')
                    return
        return render(backend.strategy.request, 'registration/profile_creation.html', {
            'title': 'Create your profile', 'form': form,
        })


class SocialAuthExceptionMiddleware(OldSocialAuthExceptionMiddleware):
    def process_exception(self, request, exception):
        if isinstance(exception, SocialAuthBaseException):
            return HttpResponseRedirect('%s?message=%s' % (reverse('social_auth_error'),
                                                           quote(self.get_message(request, exception))))