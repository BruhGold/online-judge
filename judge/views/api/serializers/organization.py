from rest_framework import serializers
from judge.models.profile import Organization, Profile

class OrganizationSerializer(serializers.ModelSerializer):
    admins = serializers.PrimaryKeyRelatedField(many=True, queryset=Profile.objects.all(), required=False)
    class Meta:
        model = Organization
        fields = [
            'name',
            'slug',
            'short_name',
            'about',
            'admins',
            'creation_date',
            'is_open',
            'slots',
            'access_code',
            'logo_override_image',
        ]

    def validate(self, data):
        user = self.context['user']
        restricted_fields = ['is_open', 'slots', 'admins']
        if not user.has_perm('judge.organization_admin'):
            for field in restricted_fields:
                if field in data:
                    raise serializers.ValidationError(f"You don't have permission to set '{field}'.")
        return data

    # you can remove this if you don't want to force POST request sender as admin
    def create(self, validated_data):
        user = self.context['user']
        # Ensure admins includes the sender
        admins = validated_data.pop('admins', [])
        if user.profile not in admins:
            admins.append(user.profile)
        print(validated_data)
        org = Organization.objects.create(**validated_data)
        org.admins.set(admins)
        return org