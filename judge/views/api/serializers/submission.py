from rest_framework import serializers
from judge.models import Submission, Language
from judge.widgets import AceWidget

class ProblemSubmitSerializer(serializers.Serializer):
    language = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all())
    source = serializers.CharField(max_length=65536)
    judge = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        problem = self.context.get('problem')
        user = self.context['request'].user.profile

        if not problem.allowed_languages.filter(id=data['language'].id).exists():
            raise serializers.ValidationError({'language': 'This language is not allowed for the selected problem.'})

        if problem.banned_users.filter(id=user.id).exists() and not user.user.is_superuser:
            raise serializers.ValidationError('You are banned from submitting to this problem.')

        return data
