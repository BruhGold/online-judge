from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.conf import settings
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User, update_last_login
from rest_framework_simplejwt.settings import api_settings

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    api_secret = serializers.CharField(required=False, write_only=True)
    provider = serializers.CharField(required=False, write_only=True)
    uid = serializers.CharField(required=False, write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['password'].required = False

    def validate(self, attrs):
        api_secret = attrs.get("api_secret")
        provider = attrs.get("provider")
        uid = attrs.get("uid")

        if api_secret and provider and uid:
            try:
                social = UserSocialAuth.objects.get(provider=provider, uid=uid)
                if api_secret == settings.API_TOKEN_OBTAIN_SECRET:
                    self.user = social.user
                else:
                    raise serializers.ValidationError("Invalid api_secret")
            except UserSocialAuth.DoesNotExist:
                raise serializers.ValidationError("No such social account")

            refresh = self.get_token(self.user)

            data = {}
            data["refresh"] = str(refresh)
            data["access"] = str(refresh.access_token)

            if api_settings.UPDATE_LAST_LOGIN:
                update_last_login(None, self.user)

            return data
        else:
            # fallback to username/password
            return super().validate(attrs)
