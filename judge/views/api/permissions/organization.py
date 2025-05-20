from rest_framework.permissions import BasePermission, SAFE_METHODS
from judge.models.profile import Organization

class CanEditOrganization(BasePermission):
    def has_object_permission(self, request, view, obj:Organization):
        if request.method == "PUT" or request.method == "DELETE":
            return request.user.profile in obj.admins.all()
        return True