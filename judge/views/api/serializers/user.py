from rest_framework import serializers

from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db import transaction

from social_django.models import UserSocialAuth
from judge.models import Submission, Profile

class DownloadDataSerializer(serializers.Serializer):
    comment_download = serializers.BooleanField(default=False, label=_('Download comments?'))
    submission_download = serializers.BooleanField(default=False, label=_('Download submissions?'))
    submission_problem_glob = serializers.CharField(
        default='*', max_length=100, label=_('Filter by problem code glob:')
    )
    submission_results = serializers.MultipleChoiceField(
        required=False,
        choices=sorted(Submission.RESULT),
        label=_('Filter by result:')
    )

    def validate(self, data):
        if not data.get('comment_download') and not data.get('submission_download'):
            raise serializers.ValidationError(
                _('Please select at least one thing to download.')
            )

        if not data.get('submission_download'):
            data['submission_problem_glob'] = '*'
            data['submission_results'] = []
        else:
            if 'submission_problem_glob' not in data or not data['submission_problem_glob']:
                data['submission_problem_glob'] = '*'
            if 'submission_results' not in data:
                data['submission_results'] = []
            else:
                data['submission_results'] = list(data.get('submission_results', []))
                
        return data


class SingleUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    email = serializers.CharField(required=False, allow_null=True)
    first_name = serializers.CharField(required=False, allow_null=True)
    last_name = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name']

    def validate(self, data):
        moodle_uid = self.context.get("moodle_uid")
        provider = self.context.get("provider", "moodle")  # default to 'moodle'

        if moodle_uid is None:
            raise serializers.ValidationError(_("Missing moodle_uid in context"))

        # check if usersocialauth exist for this moodle uid
        exists = UserSocialAuth.objects.filter(provider=provider, uid=moodle_uid).exists()
        if exists:
            raise serializers.ValidationError(
                _("This moodle UID already exists in the UserSocialAuth table"),
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        # create the Django user (with hashed password)
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data.get('password', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        # profile
        Profile.objects.create(user=user)
        # social-auth
        provider = self.context['provider']
        uid = self.context['moodle_uid']
        UserSocialAuth.objects.create(user=user, provider=provider, uid=uid)
        return user
