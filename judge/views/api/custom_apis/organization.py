from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from judge.models.profile import Organization
from judge.views.api.api_v2 import APIOrganizationList, APIOrganizationDetail
from ..serializers.organization import OrganizationSerializer
from ..permissions.organization import CanEditOrganization

class APIOrganizationListView(APIView, APIOrganizationList):
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly]

    def post(self, request, *args, **kwargs):
        serializer = OrganizationSerializer(data=request.data, context={'user': request.user})

        if serializer.is_valid():
            try:
                organization = serializer.save()
                return Response(OrganizationSerializer(organization).data, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                return Response(
                    {"error": "Database constraint error", "details": str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class APIOrganizationDetailView(APIView, APIOrganizationDetail):
    permission_classes = [DjangoModelPermissionsOrAnonReadOnly, CanEditOrganization]

    def put(self, request, *args, **kwargs):
        organization = self.get_object()

        self.check_object_permissions(request, organization) # this check if the user is an admin for this org or not

        serializer = OrganizationSerializer(organization, data=request.data, partial=True, context={'user': request.user})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        organization = self.get_object()
        self.check_object_permissions(request, organization)
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
