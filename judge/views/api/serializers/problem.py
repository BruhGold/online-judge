from rest_framework import serializers
from judge.models.problem import Problem
from judge.models.problem import ProblemGroup, ProblemType, Profile, Language, Organization, License

class ProblemSerializer(serializers.ModelSerializer):
    authors = serializers.PrimaryKeyRelatedField(many=True, queryset=Profile.objects.all(), required=False)
    curators = serializers.PrimaryKeyRelatedField(many=True, queryset=Profile.objects.all(), required=False)
    testers = serializers.PrimaryKeyRelatedField(many=True, queryset=Profile.objects.all(), required=False)
    types = serializers.PrimaryKeyRelatedField(many=True, queryset=ProblemType.objects.all())
    group = serializers.PrimaryKeyRelatedField(queryset=ProblemGroup.objects.all())
    allowed_languages = serializers.PrimaryKeyRelatedField(many=True, queryset=Language.objects.all(), required=False)
    organizations = serializers.PrimaryKeyRelatedField(many=True, queryset=Organization.objects.all(), required=False)
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all(), allow_null=True, required=False)
    is_public = serializers.BooleanField(default=True)

    class Meta:
        model = Problem
        fields = '__all__'

    def validate(self, data):
        user = self.context['user']
        if not data.get('is_public', True) and not user.has_perm('judge.create_private_problem'):
            raise serializers.ValidationError("You don't have permission to create private problems.")
        return data