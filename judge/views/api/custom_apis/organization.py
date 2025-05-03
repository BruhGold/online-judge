from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from judge.models.profile import Organization
from judge.views.api.api_v2 import APIOrganizationList
from ..serializers.organization import OrganizationSerializer

class APIOrganizationListView(APIView, APIOrganizationList):
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def post(self, request, *args, **kwargs):
        serializer = OrganizationSerializer(data=request.data, context={'user': request.user})

        if serializer.is_valid():
            try:
                print("saving")
                organization = serializer.save()
                return Response(OrganizationSerializer(organization).data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response(
                    {"error": "Database constraint error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)