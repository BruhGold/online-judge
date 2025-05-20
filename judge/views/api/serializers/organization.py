from rest_framework import serializers
from judge.models.profile import Organization, Profile

class OrganizationSerializer(serializers.ModelSerializer):
    admins = serializers.PrimaryKeyRelatedField(many=True, queryset=Profile.objects.all(), required=False)
    members = serializers.PrimaryKeyRelatedField(many=True,queryset=Profile.objects.all(),required=False)
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'slug',
            'short_name',
            'about',
            'admins',
            'members',
            'creation_date',
            'is_open',
            'slots',
            'access_code',
            'logo_override_image',
        ]

    def validate(self, data):
        user = self.context['user']
        restricted_fields = ['is_open', 'slots', 'admins', 'members']
        if not user.has_perm('judge.organization_admin'):
            for field in restricted_fields:
                if field in data:
                    raise serializers.ValidationError(f"You don't have permission to set '{field}'.")
        return data

    def create(self, validated_data):
        user = self.context['user']
        print(validated_data)

        # you can remove this if you don't want to force POST request sender as admin
        admins = validated_data.pop('admins', [])
        if user.profile not in admins:
            admins.append(user.profile)

        members = validated_data.pop('members', [])
            
        org = Organization.objects.create(**validated_data)

        # you can remove this if you don't want to force POST request sender as admin
        org.admins.set(admins)

        # this is for members
        org.members.set(members)
        return org