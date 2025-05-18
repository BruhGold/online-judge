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

    def validate_types(self, value):
        if not value:
            raise serializers.ValidationError("At least one 'type' must be selected.")
        return value

    def validate_group(self, value):
        if value is None:
            raise serializers.ValidationError("A 'group' must be selected.")
        return value

    def validate_description(self, value):
        if not value:
            raise serializers.ValidationError("Description cannot be empty.")
        return value
    
    def validate_code(self, value):
        if not value:
            raise serializers.ValidationError("Code cannot be empty.")
        return value

    def validate_name(self,value):
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        return value

    def validate_points(self,value):
        if value is None:
            raise serializers.ValidationError("Points cannot be empty.")
        return value
    
    def validate_allowed_languages(self, value):
        if not value:
            raise serializers.ValidationError("At least one 'allowed_language' must be selected.")
        return value

    def validate_time_limit(self, value):
        if value is None:
            raise serializers.ValidationError("Time limit cannot be empty.")
        return value

    def validate_memory_limit(self, value):
        if value is None:
            raise serializers.ValidationError("Memory limit cannot be empty.")
        return value